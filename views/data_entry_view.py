import streamlit as st
from datetime import datetime
from components.header import render_top_header
from db.repository import (
    get_all_checkpoints_list,
    get_all_datasets,
    insert_quality_dataset,
    update_quality_dataset,
    delete_quality_dataset
)

@st.dialog("Edit Quality Dataset", width="medium")
def show_edit_dataset_modal(dataset: dict):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Update metadata for <b>{dataset["file_name"]}</b>.</div>', unsafe_allow_html=True)
    
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

@st.dialog("Delete Quality Dataset", width="small")
def show_delete_dataset_modal(dataset: dict):
    st.markdown(f"""
    <div style="text-align: center; padding: 6px 0 16px 0;">
        <div style="font-size: 34px; margin-bottom: 10px;">⚠️</div>
        <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Delete Dataset Record?</div>
        <div style="font-size: 13.5px; color: #64748B; line-height: 1.5;">
            Are you sure you want to remove <b>{dataset['file_name']}</b> from the database?
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

def render_data_entry_view():
    """
    DATA ENTRY SCREEN — Full CRUD
    """
    render_top_header("Data Entry")

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 20px;">
Ingest and register production quality spreadsheets, inspection sheets, and sensor logs mapped to manufacturing checkpoints.
</div>""", unsafe_allow_html=True)

    # Inline success banner if file was uploaded
    if st.session_state.get("last_uploaded_file_name"):
        st.markdown(f"""<div style="background-color: #DCFCE7; border: 1px solid #86EFAC; color: #15803D; padding: 12px 18px; border-radius: 8px; font-size: 14.5px; font-weight: 600; display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
<span style="font-size: 18px; font-weight: 700;">✓</span>
<span>File <b>{st.session_state.last_uploaded_file_name}</b> uploaded successfully</span>
</div>""", unsafe_allow_html=True)

    # 1. Fetch available checkpoints for dropdown
    checkpoints = get_all_checkpoints_list()
    checkpoint_options = ["Select Checkpoint"] + [
        f"{c['checkpoint_name']} — ({c['process_name']})" for c in checkpoints
    ]

    # Upload Form Card
    with st.container(border=True):
        st.markdown('<label class="form-label" style="font-size: 14.5px; font-weight: 600; margin-bottom: 6px;">Choose Checkpoint <span class="required-star">*</span></label>', unsafe_allow_html=True)
        selected_cp_str = st.selectbox(
            label="Choose Checkpoint",
            options=checkpoint_options,
            index=0,
            label_visibility="collapsed",
            key="data_entry_checkpoint_select"
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        st.markdown('<label class="form-label" style="font-size: 14.5px; font-weight: 600; margin-bottom: 6px;">Upload File (.xlsx, .xls) <span class="required-star">*</span></label>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            label="Upload File",
            type=["xlsx", "xls", "csv"],
            label_visibility="collapsed",
            key="data_entry_uploader"
        )

        if uploaded_file is not None:
            file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
            if not st.session_state.get(file_key, False):
                cp_name = selected_cp_str.split(" — ")[0] if selected_cp_str != "Select Checkpoint" else "Casting Temperature"
                file_size_kb = max(1, uploaded_file.size // 1024)
                
                insert_quality_dataset(
                    checkpoint_name=cp_name,
                    file_name=uploaded_file.name,
                    file_size_kb=file_size_kb,
                    uploaded_by_name="Alexander Wright (Admin)"
                )
                
                st.session_state[file_key] = True
                st.session_state.last_uploaded_file_name = uploaded_file.name
                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. Fetch all uploaded datasets from DB
    datasets = get_all_datasets()

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        st.markdown(f'<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 12px;">Recent Data Ingestion Records ({len(datasets)})</div>', unsafe_allow_html=True)
        
        h1, h2, h3, h4, h5, h6 = st.columns([1, 4.5, 3.5, 2.5, 2, 1.5])
        h1.markdown("**S.No.**")
        h2.markdown("**File Name**")
        h3.markdown("**Checkpoint**")
        h4.markdown("**Uploaded By**")
        h5.markdown("**Uploaded On**")
        h6.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        for idx, d in enumerate(datasets, start=1):
            uploaded_on = d.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
            if len(str(uploaded_on)) > 16:
                uploaded_on = str(uploaded_on)[:16]

            c1, c2, c3, c4, c5, c6 = st.columns([1, 4.5, 3.5, 2.5, 2, 1.5])
            c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>📊 {d['file_name']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color: #2563EB; font-weight: 500;'>{d['checkpoint_name']}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span style='color: #334155;'>{d['uploaded_by_name']}</span>", unsafe_allow_html=True)
            c5.markdown(f"<span style='color: #64748B; font-size: 13.5px;'>{uploaded_on}</span>", unsafe_allow_html=True)
            
            with c6:
                col_e, col_d = st.columns(2)
                with col_e:
                    if st.button("✏️", key=f"edit_de_{d['id']}", help="Edit Dataset"):
                        show_edit_dataset_modal(d)
                with col_d:
                    if st.button("🗑️", key=f"del_de_{d['id']}", help="Delete Dataset"):
                        show_delete_dataset_modal(d)
            
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
