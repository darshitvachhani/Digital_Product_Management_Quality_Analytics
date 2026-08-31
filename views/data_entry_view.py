import streamlit as st
from datetime import datetime
from components.header import render_top_header, get_current_user
from db.repository import (
    get_all_checkpoints_list,
    get_all_datasets,
    insert_quality_dataset,
    update_quality_dataset,
    delete_quality_dataset,
    upload_file_to_supabase_storage
)
from utils.excel_generator import (
    validate_excel_columns,
    get_required_columns_for_checkpoint,
    generate_checkpoint_template_excel
)

# Role-to-checkpoint scoping mapping
ROLE_CHECKPOINT_PERMISSIONS = {
    "Quality Director (Admin)": None, # Unrestricted (All checkpoints)
    "Shopfloor Inspector": ["Casting Temperature", "Visual Casting Inspection", "Fettling / Flash Removal"],
    "Lead Process Engineer": ["Machining Dimensions", "Surface Finish", "Tool / Machine Condition"],
    "Senior Metrology Specialist": ["Dimensional Accuracy", "Geometric Tolerances (G&T)", "Final Dimensional Inspection"],
    "Quality Assurance Lead": ["Cleanliness", "Assembly Fitment", "Leak Test"]
}

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
    DATA ENTRY SCREEN — Role Scoping & Dynamic Checkpoint Template Download
    """
    render_top_header("Data Entry")

    current_user = get_current_user()
    user_role = current_user.get("role", "Quality Director (Admin)")
    is_admin = "Admin" in user_role or "Director" in user_role

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 16px;">
Ingest and register production quality spreadsheets, inspection sheets, and sensor logs mapped to manufacturing checkpoints.
</div>""", unsafe_allow_html=True)

    # Active User Permission Scope Banner
    if is_admin:
        st.markdown(f"""<div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 16px; border-radius: 8px; font-size: 13px; color: #166534; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;">
            <div><b>Active User:</b> {current_user['name']} • <b>Role:</b> {user_role} 👑 <i>(Unrestricted: All checkpoints & custom schemas allowed)</i></div>
            <span style="font-size: 11px; background: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 4px; font-weight: 700;">ADMIN BYPASS</span>
        </div>""", unsafe_allow_html=True)
    else:
        allowed_cps = ROLE_CHECKPOINT_PERMISSIONS.get(user_role, [])
        st.markdown(f"""<div style="background: #FEF3C7; border: 1px solid #FDE68A; padding: 10px 16px; border-radius: 8px; font-size: 13px; color: #92400E; margin-bottom: 18px;">
            <b>Active User:</b> {current_user['name']} • <b>Role:</b> {user_role} 🛡️<br/>
            <b>Allowed Checkpoint Scope:</b> {', '.join(allowed_cps) if allowed_cps else 'Assigned stations only'} <i>(Strict column validation active)</i>
        </div>""", unsafe_allow_html=True)

    # Inline upload error banner
    if st.session_state.get("last_upload_error"):
        st.markdown(f"""<div style="background-color: #FEF2F2; border: 1px solid #F87171; color: #991B1B; padding: 14px 18px; border-radius: 8px; font-size: 13.5px; margin-bottom: 18px;">
<div style="font-weight: 700; font-size: 14.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
    <span>❌</span> <span>Upload Validation Error</span>
</div>
<div>{st.session_state.last_upload_error}</div>
</div>""", unsafe_allow_html=True)

    # Inline success banner
    if st.session_state.get("last_uploaded_file_name"):
        st.markdown(f"""<div style="background-color: #DCFCE7; border: 1px solid #86EFAC; color: #15803D; padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
<span style="font-size: 18px; font-weight: 700;">✓</span>
<span>File <b>{st.session_state.last_uploaded_file_name}</b> successfully validated and ingested into Supabase Cloud!</span>
</div>""", unsafe_allow_html=True)

    # 1. Fetch available checkpoints for dropdown (Filtered by Role)
    all_checkpoints = get_all_checkpoints_list()
    
    if is_admin:
        allowed_checkpoints = all_checkpoints
    else:
        perm_names = ROLE_CHECKPOINT_PERMISSIONS.get(user_role, [])
        allowed_checkpoints = [c for c in all_checkpoints if any(p.lower() in c["checkpoint_name"].lower() for p in perm_names)]
        if not allowed_checkpoints:
            allowed_checkpoints = all_checkpoints[:3]

    checkpoint_options = ["Select Checkpoint"] + [
        f"{c['checkpoint_name']} — ({c['process_name']})" for c in allowed_checkpoints
    ]

    # Upload Form Card
    with st.container(border=True):
        col_sel, col_btn_tpl = st.columns([7.2, 2.8])
        
        with col_sel:
            st.markdown('<label class="form-label" style="font-size: 14.5px; font-weight: 600; margin-bottom: 6px;">Choose Checkpoint <span class="required-star">*</span></label>', unsafe_allow_html=True)
            selected_cp_str = st.selectbox(
                label="Choose Checkpoint",
                options=checkpoint_options,
                index=0,
                label_visibility="collapsed",
                key="data_entry_checkpoint_select"
            )

        has_checkpoint_selected = selected_cp_str != "Select Checkpoint"
        selected_cp_name = selected_cp_str.split(" — ")[0] if has_checkpoint_selected else ""

        with col_btn_tpl:
            st.markdown('<div style="height: 27px;"></div>', unsafe_allow_html=True)
            if has_checkpoint_selected:
                tpl_bytes = generate_checkpoint_template_excel(selected_cp_name)
                st.download_button(
                    label="📥 Download Template (.xlsx)",
                    data=tpl_bytes,
                    file_name=f"Template_{selected_cp_name.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_de_tpl_{selected_cp_name[:15]}",
                    use_container_width=True,
                    help=f"Download valid reference Excel template for {selected_cp_name}"
                )
            else:
                st.button(
                    label="📥 Download Template (.xlsx)",
                    disabled=True,
                    use_container_width=True,
                    key="dl_de_tpl_disabled",
                    help="Please select a checkpoint first to download its specific Excel template"
                )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        st.markdown('<label class="form-label" style="font-size: 14.5px; font-weight: 600; margin-bottom: 6px;">Upload File (.xlsx, .xls, .csv) <span class="required-star">*</span></label>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            label="Upload File",
            type=["xlsx", "xls", "csv"],
            label_visibility="collapsed",
            key="data_entry_uploader"
        )

        if uploaded_file is not None:
            if not has_checkpoint_selected:
                st.warning("⚠️ Please select a Checkpoint first before uploading.")
            else:
                file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}_{selected_cp_name}_{current_user['name']}"
                if not st.session_state.get(file_key, False):
                    
                    # STRICT COLUMN VALIDATION (Enforced for non-admins)
                    if not is_admin:
                        is_valid, missing_cols, found_cols = validate_excel_columns(uploaded_file, selected_cp_name)
                        if not is_valid:
                            req_cols = get_required_columns_for_checkpoint(selected_cp_name)
                            st.session_state.last_upload_error = f"The uploaded file <b>{uploaded_file.name}</b> is missing mandatory columns for <i>{selected_cp_name}</i>: <br/><br/><b>Missing Columns:</b> <code style='color: #DC2626;'>{', '.join(missing_cols)}</code><br/><b>Found Columns:</b> <code>{', '.join(found_cols)}</code><br/><br/>Please download and use the official <b>{selected_cp_name} Template</b> above."
                            st.session_state.last_uploaded_file_name = None
                            st.session_state[file_key] = True
                            st.rerun()

                    # Validation Passed: Ingest to Supabase
                    st.session_state.last_upload_error = None
                    file_size_kb = max(1, uploaded_file.size // 1024)
                    
                    # Upload file to Supabase Storage
                    try:
                        file_bytes = uploaded_file.getvalue()
                        upload_file_to_supabase_storage(uploaded_file.name, file_bytes)
                    except Exception as e:
                        print(f"File storage upload notice: {e}")

                    insert_quality_dataset(
                        checkpoint_name=selected_cp_name,
                        file_name=uploaded_file.name,
                        file_size_kb=file_size_kb,
                        uploaded_by_name=f"{current_user['name']} ({user_role.split()[0]})"
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
            uploaded_on = d.get("created_at") or datetime.now().strftime("%Y-%m-%d")
            uploaded_on_str = uploaded_on.strftime("%Y-%m-%d %H:%M") if hasattr(uploaded_on, "strftime") else str(uploaded_on)[:16]

            c1, c2, c3, c4, c5, c6 = st.columns([1, 4.5, 3.5, 2.5, 2, 1.5])
            c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>📊 {d['file_name']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color: #2563EB; font-weight: 500;'>{d['checkpoint_name']}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span style='color: #334155;'>{d['uploaded_by_name']}</span>", unsafe_allow_html=True)
            c5.markdown(f"<span style='color: #64748B; font-size: 13.5px;'>{uploaded_on_str}</span>", unsafe_allow_html=True)
            
            with c6:
                col_e, col_d = st.columns(2)
                with col_e:
                    if st.button("✏️", key=f"edit_de_{d['id']}", help="Edit Dataset"):
                        show_edit_dataset_modal(d)
                with col_d:
                    if st.button("🗑️", key=f"del_de_{d['id']}", help="Delete Dataset"):
                        show_delete_dataset_modal(d)
            
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
