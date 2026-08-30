import streamlit as st
from components.header import render_top_header
from db.repository import (
    get_all_users,
    insert_user,
    update_user,
    delete_user,
    can_delete_user
)

@st.dialog("Invite Team Member", width="medium")
def show_create_user_modal():
    st.markdown('<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Add a new quality engineer or plant inspector to QualIQ.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="e.g. Jason Miller")
    with col2:
        email = st.text_input("Email Address *", placeholder="e.g. jason.miller@qualiq.io")
    
    col3, col4 = st.columns(2)
    with col3:
        role = st.selectbox("Role", ["Quality Director (Admin)", "Lead Process Engineer", "Shopfloor Inspector", "Quality Assurance Lead", "Senior Metrology Specialist"])
    with col4:
        status = st.selectbox("Status", ["Active", "Inactive", "Suspended"], index=0)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Member", type="primary", use_container_width=True):
            if name.strip() and email.strip():
                try:
                    insert_user(name, email, role, status)
                    st.toast(f"Invited user '{name}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {e}")
            else:
                st.warning("Please provide a name and email.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Edit Team Member", width="medium")
def show_edit_user_modal(user: dict):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Edit user profile for <b>{user["name"]}</b>.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", value=user["name"])
    with col2:
        email = st.text_input("Email Address *", value=user["email"])
    
    role_options = ["Quality Director (Admin)", "Lead Process Engineer", "Shopfloor Inspector", "Quality Assurance Lead", "Senior Metrology Specialist"]
    cur_role_idx = role_options.index(user["role"]) if user["role"] in role_options else 0
    role = st.selectbox("Role", options=role_options, index=cur_role_idx)

    status_options = ["Active", "Inactive", "Suspended"]
    cur_status_idx = status_options.index(user["status"]) if user["status"] in status_options else 0
    status = st.selectbox("Status", options=status_options, index=cur_status_idx)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Update Member", type="primary", use_container_width=True):
            if name.strip() and email.strip():
                update_user(user["id"], name, email, role, status)
                st.toast(f"Updated user '{name}'!")
                st.rerun()
            else:
                st.warning("Please provide a valid name and email.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Delete Team Member", width="small")
def show_delete_user_modal(user: dict):
    can_del, dataset_count, msg = can_delete_user(user["id"])
    
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
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Revoke Member Access?</div>
            <div style="font-size: 13.5px; color: #64748B; line-height: 1.5;">
                Are you sure you want to remove <b>{user['name']}</b> ({user['email']})?
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_del, col_cancel = st.columns([1, 1])
        with col_del:
            if st.button("Yes, Delete", type="primary", use_container_width=True):
                success, del_msg = delete_user(user["id"])
                if success:
                    st.toast(f"Removed user '{user['name']}'")
                else:
                    st.error(del_msg)
                st.rerun()
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.rerun()

def render_user_manager_view():
    """
    User Manager View — Full CRUD with Data Contribution Deletion Guard
    """
    render_top_header("User & Access Management")

    users = get_all_users()

    # Top Action Bar
    with st.container():
        col_title, col_add = st.columns([8, 2])
        with col_title:
            st.markdown(f'<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-top: 6px;">Platform Users & Roles ({len(users)})</div>', unsafe_allow_html=True)
        with col_add:
            if st.button("➕  Invite Member", type="primary", use_container_width=True, key="btn_open_new_user_modal"):
                show_create_user_modal()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        h1, h2, h3, h4, h5 = st.columns([3, 3, 2.5, 1.8, 1.4])
        h1.markdown("**User Name**")
        h2.markdown("**Email**")
        h3.markdown("**Role**")
        h4.markdown("**Status**")
        h5.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        for u in users:
            c1, c2, c3, c4, c5 = st.columns([3, 3, 2.5, 1.8, 1.4])
            c1.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{u['name']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color: #64748B;'>{u['email']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color: #334155;'>{u['role']}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span class='badge-status badge-success'><span style='font-size: 8px;'>●</span> {u['status']}</span>", unsafe_allow_html=True)
            
            with c5:
                col_e, col_d = st.columns(2)
                with col_e:
                    if st.button("✏️", key=f"edit_u_{u['id']}", help="Edit Member"):
                        show_edit_user_modal(u)
                with col_d:
                    if st.button("🗑️", key=f"del_u_{u['id']}", help="Delete Member"):
                        show_delete_user_modal(u)
            
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
