import streamlit as st
from datetime import datetime, date
from components.header import render_top_header
from db.repository import (
    get_all_products,
    get_all_processes,
    get_all_checkpoints_list,
    get_all_datasets,
    update_quality_dataset,
    delete_quality_dataset
)

@st.dialog("Edit Warehouse Dataset", width="medium")
def show_edit_warehouse_dataset_modal(dataset: dict):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Update catalog record for <b>{dataset["file_name"]}</b>.</div>', unsafe_allow_html=True)
    
    checkpoints = get_all_checkpoints_list()
    cp_names = [c["checkpoint_name"] for c in checkpoints]
    
    file_name = st.text_input("File Name *", value=dataset["file_name"])
    
    cur_cp_idx = cp_names.index(dataset["checkpoint_name"]) if dataset["checkpoint_name"] in cp_names else 0
    cp_selected = st.selectbox("Mapped Checkpoint *", options=cp_names, index=cur_cp_idx)
    
    uploaded_by = st.text_input("Uploaded By", value=dataset["uploaded_by_name"])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Changes", type="primary", use_container_width=True):
            if file_name.strip():
                update_quality_dataset(dataset["id"], file_name, cp_selected, uploaded_by)
                st.toast(f"Updated dataset '{file_name}'!")
                st.rerun()
            else:
                st.warning("Please provide a valid file name.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Delete Warehouse Dataset", width="small")
def show_delete_warehouse_dataset_modal(dataset: dict):
    st.markdown(f"""
    <div style="text-align: center; padding: 6px 0 16px 0;">
        <div style="font-size: 34px; margin-bottom: 10px;">⚠️</div>
        <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Delete Dataset Record?</div>
        <div style="font-size: 13.5px; color: #64748B; line-height: 1.5;">
            Are you sure you want to delete <b>{dataset['file_name']}</b> from the Data Warehouse?
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_del, col_cancel = st.columns([1, 1])
    with col_del:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            delete_quality_dataset(dataset["id"])
            st.toast(f"Deleted dataset '{dataset['file_name']}'")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_data_warehouse_view():
    """
    DATA WAREHOUSE SCREEN — Full CRUD
    """
    render_top_header("Data Warehouse")

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 20px;">
Centralized quality data repository. Filter, inspect, and query raw manufacturing inspection logs and telemetry datasets across product lines.
</div>""", unsafe_allow_html=True)

    # 1. Fetch filter choices from database
    products = get_all_products()
    product_options = ["All Products"] + [p["name"] for p in products]

    processes = get_all_processes()
    process_options = ["All Processes"] + list(dict.fromkeys([p["process_name"] for p in processes]))

    checkpoints = get_all_checkpoints_list()
    checkpoint_options = ["All Checkpoints"] + list(dict.fromkeys([c["checkpoint_name"] for c in checkpoints]))

    user_options = ["All Users", "Alexander Wright", "Elena Rostova", "David Chang", "Sarah Jenkins", "Marcus Vance"]

    # 2. Filter Controls Card
    with st.container(border=True):
        col_prod, col_proc, col_cp = st.columns([1, 1, 1])
        
        with col_prod:
            st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Product</label>', unsafe_allow_html=True)
            filter_prod = st.selectbox(
                label="Product",
                options=product_options,
                index=0,
                label_visibility="collapsed",
                key="dw_filter_prod"
            )

        with col_proc:
            st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Process</label>', unsafe_allow_html=True)
            filter_proc = st.selectbox(
                label="Process",
                options=process_options,
                index=0,
                label_visibility="collapsed",
                key="dw_filter_proc"
            )

        with col_cp:
            st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Checkpoint</label>', unsafe_allow_html=True)
            filter_cp = st.selectbox(
                label="Checkpoint",
                options=checkpoint_options,
                index=0,
                label_visibility="collapsed",
                key="dw_filter_cp"
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        col_user, col_date, col_search = st.columns([1, 1, 1])

        with col_user:
            st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Uploaded By</label>', unsafe_allow_html=True)
            filter_user = st.selectbox(
                label="Uploaded By",
                options=user_options,
                index=0,
                label_visibility="collapsed",
                key="dw_filter_user"
            )

        with col_date:
            st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Date Range</label>', unsafe_allow_html=True)
            date_filter = st.date_input(
                label="Date Range",
                value=(date(2026, 1, 1), date.today()),
                label_visibility="collapsed",
                key="dw_filter_date"
            )

        with col_search:
            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
            search_clicked = st.button("🔍  Search Warehouse", type="primary", use_container_width=True, key="dw_btn_search")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 3. Query Datasets from Database based on Filters
    datasets = get_all_datasets(
        product_filter=filter_prod,
        process_filter=filter_proc,
        checkpoint_filter=filter_cp,
        user_filter=filter_user
    )

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        st.markdown(f'<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 12px;">Quality Datasets Catalog ({len(datasets)} files)</div>', unsafe_allow_html=True)
        
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([0.8, 3.8, 2.2, 2.4, 2.2, 1.8, 1.4, 1.4])
        h1.markdown("**S.No.**")
        h2.markdown("**File Name**")
        h3.markdown("**Product**")
        h4.markdown("**Process**")
        h5.markdown("**Checkpoint**")
        h6.markdown("**Uploaded By**")
        h7.markdown("**Uploaded On**")
        h8.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if not datasets:
            st.markdown("<div style='text-align: center; color: #94A3B8; padding: 24px;'>No datasets match the selected filter criteria.</div>", unsafe_allow_html=True)
        else:
            for idx, d in enumerate(datasets, start=1):
                uploaded_on = d.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
                if len(str(uploaded_on)) > 10:
                    uploaded_on = str(uploaded_on)[:10]

                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.8, 3.8, 2.2, 2.4, 2.2, 1.8, 1.4, 1.4])
                c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>📊 {d['file_name']}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='color: #334155;'>{d['product_name']}</span>", unsafe_allow_html=True)
                c4.markdown(f"<span style='color: #475569;'>{d['process_name']}</span>", unsafe_allow_html=True)
                c5.markdown(f"<span style='color: #2563EB; font-weight: 500;'>{d['checkpoint_name']}</span>", unsafe_allow_html=True)
                c6.markdown(f"<span style='color: #334155;'>{d['uploaded_by_name']}</span>", unsafe_allow_html=True)
                c7.markdown(f"<span style='color: #64748B; font-size: 13px;'>{uploaded_on}</span>", unsafe_allow_html=True)
                
                with c8:
                    col_e, col_d = st.columns(2)
                    with col_e:
                        if st.button("✏️", key=f"edit_dw_{d['id']}", help="Edit Dataset"):
                            show_edit_warehouse_dataset_modal(d)
                    with col_d:
                        if st.button("🗑️", key=f"del_dw_{d['id']}", help="Delete Dataset"):
                            show_delete_warehouse_dataset_modal(d)
                
                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
