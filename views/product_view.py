import streamlit as st
from components.header import render_top_header
from db.repository import (
    get_all_products,
    insert_product,
    update_product,
    delete_product,
    can_delete_product
)

@st.dialog("Create New Product", width="medium")
def show_create_product_modal():
    st.markdown('<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Register a new manufacturing component line into QualIQ.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        code = st.text_input("Product Code *", placeholder="e.g. PRD-104")
    with col2:
        name = st.text_input("Product Name *", placeholder="e.g. Crankshaft Housing")
    
    line = st.text_input("Manufacturing Line *", placeholder="e.g. Line 03 - Precision Machining")
    status = st.selectbox("Status", ["Active", "Inactive", "Archived"], index=0)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Product", type="primary", use_container_width=True):
            if code.strip() and name.strip() and line.strip():
                try:
                    insert_product(code, name, line, status)
                    st.toast(f"Created product '{name}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating product: {e}")
            else:
                st.warning("Please fill in all required fields.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Edit Product", width="medium")
def show_edit_product_modal(product: dict):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Update product details for <b>{product["name"]}</b>.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        code = st.text_input("Product Code *", value=product["product_code"])
    with col2:
        name = st.text_input("Product Name *", value=product["name"])
    
    line = st.text_input("Manufacturing Line *", value=product["manufacturing_line"])
    
    status_options = ["Active", "Inactive", "Archived"]
    cur_status_idx = status_options.index(product["status"]) if product["status"] in status_options else 0
    status = st.selectbox("Status", options=status_options, index=cur_status_idx)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Changes", type="primary", use_container_width=True):
            if code.strip() and name.strip() and line.strip():
                try:
                    update_product(product["id"], code, name, line, status)
                    st.toast(f"Updated product '{name}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating product: {e}")
            else:
                st.warning("Please fill in all required fields.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Delete Product", width="small")
def show_delete_product_modal(product: dict):
    can_del, count, msg = can_delete_product(product["id"])
    
    if not can_del:
        st.markdown(f"""
        <div style="text-align: center; padding: 6px 0 16px 0;">
            <div style="font-size: 34px; margin-bottom: 10px;">🚫</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Deletion Blocked</div>
            <div style="font-size: 13.5px; color: #DC2626; line-height: 1.5; background: #FEF2F2; padding: 12px; border-radius: 8px; border: 1px solid #FCA5A5;">
                {msg}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Close", type="primary", use_container_width=True):
            st.rerun()
    else:
        st.markdown(f"""
        <div style="text-align: center; padding: 6px 0 16px 0;">
            <div style="font-size: 34px; margin-bottom: 10px;">⚠️</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Delete Product?</div>
            <div style="font-size: 13.5px; color: #64748B; line-height: 1.5;">
                Are you sure you want to delete <b>{product['name']}</b> ({product['product_code']})?
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_del, col_cancel = st.columns([1, 1])
        with col_del:
            if st.button("Yes, Delete", type="primary", use_container_width=True):
                success, del_msg = delete_product(product["id"])
                if success:
                    st.toast(f"Deleted product '{product['name']}'")
                else:
                    st.error(del_msg)
                st.rerun()
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.rerun()

def render_product_view():
    """
    Products View — Full CRUD with Strict Deletion Guard
    """
    render_top_header("Products")

    products = get_all_products()

    # Top Action Bar
    with st.container():
        col_title, col_add = st.columns([8, 2])
        with col_title:
            st.markdown(f'<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-top: 6px;">Configured Manufacturing Products ({len(products)})</div>', unsafe_allow_html=True)
        with col_add:
            if st.button("➕  New Product", type="primary", use_container_width=True, key="btn_open_new_prod_modal"):
                show_create_product_modal()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        h1, h2, h3, h4, h5 = st.columns([1.5, 4, 3, 2, 1.5])
        h1.markdown("**Code**")
        h2.markdown("**Product Name**")
        h3.markdown("**Manufacturing Line**")
        h4.markdown("**Status**")
        h5.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        for prod in products:
            status = prod["status"]
            if status == "Active":
                badge_html = f"<span class='badge-status badge-success'><span style='font-size: 8px;'>●</span> {status}</span>"
            elif status == "Inactive":
                badge_html = f"<span class='badge-status badge-warning'><span style='font-size: 8px;'>●</span> {status}</span>"
            else:
                badge_html = f"<span class='badge-status badge-inactive'><span style='font-size: 8px;'>●</span> {status}</span>"

            c1, c2, c3, c4, c5 = st.columns([1.5, 4, 3, 2, 1.5])
            c1.markdown(f"<span style='font-weight: 700; color: #2563EB;'>{prod['product_code']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{prod['name']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color: #475569;'>{prod['manufacturing_line']}</span>", unsafe_allow_html=True)
            c4.markdown(badge_html, unsafe_allow_html=True)
            
            with c5:
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️", key=f"edit_prod_{prod['id']}", help="Edit Product"):
                        show_edit_product_modal(prod)
                with col_del:
                    if st.button("🗑️", key=f"del_prod_{prod['id']}", help="Delete Product"):
                        show_delete_product_modal(prod)
            
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
