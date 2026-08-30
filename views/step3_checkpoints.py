import streamlit as st
from components.header import render_top_header
from components.stepper import render_stepper
from ai.doc_summary import summarize_checkpoint_document

@st.dialog("Edit Checkpoint", width="medium")
def show_edit_checkpoint_modal(idx: int, cp: dict):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Edit checkpoint parameters for <b>{cp["name"]}</b>.</div>', unsafe_allow_html=True)
    
    available_steps = st.session_state.get("new_workflow_steps", ["Default Process Step"])
    cur_proc = cp.get("process", available_steps[0])
    cur_proc_idx = available_steps.index(cur_proc) if cur_proc in available_steps else 0
    
    new_name = st.text_input("Checkpoint Name *", value=cp["name"])
    new_proc = st.selectbox("Associated Process Step *", options=available_steps, index=cur_proc_idx)
    new_summary = st.text_area("Quality Summary / Tolerance Spec", value=cp.get("summary", ""), height=90)
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Checkpoint", type="primary", use_container_width=True):
            if new_name.strip():
                st.session_state.new_workflow_checkpoints[idx]["name"] = new_name.strip()
                st.session_state.new_workflow_checkpoints[idx]["process"] = new_proc
                st.session_state.new_workflow_checkpoints[idx]["summary"] = new_summary.strip()
                st.toast(f"Updated checkpoint: {new_name.strip()}")
                st.rerun()
            else:
                st.warning("Please enter a valid checkpoint name.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_step3_view():
    """
    SCREEN 4 — STEP 3
    Configure Checkpoints — Full CRUD, AI Document Understanding & Reordering
    """
    render_top_header()
    render_stepper(3)

    is_edit_mode = st.session_state.get("is_edit_mode", False)
    st.markdown('<h1 class="page-title">Configure Checkpoints</h1>', unsafe_allow_html=True)

    if is_edit_mode:
        st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; padding: 10px 14px; border-radius: 8px; font-size: 13.5px; margin-top: -12px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
            <span>✏️</span>
            <span>Editing checkpoints for: <b>{st.session_state.get('new_workflow_name', '')}</b></span>
        </div>
        """, unsafe_allow_html=True)

    # 1. Fetch process steps options from Step 2
    available_steps = st.session_state.get("new_workflow_steps", [
        "Foundry / Casting & Fettling",
        "CNC Rough & Finish Milling",
        "Drilling, Tapping & Boring",
        "Metrology & GNT Inspection",
        "Cleaning, Assembly & Final QC Leak Test"
    ])
    process_options = ["Select Process Step"] + available_steps

    # Initialize checkpoints in session state if not present
    if "new_workflow_checkpoints" not in st.session_state or st.session_state.new_workflow_checkpoints is None:
        st.session_state.new_workflow_checkpoints = [
            {
                "id": "cp_init_1",
                "sequence": 1,
                "name": "Casting Temperature & Pour Rate",
                "process": available_steps[0] if available_steps else "Process Step 1",
                "doc": "casting_sop_v2.pdf",
                "status": "Configuration Complete",
                "summary": "Melt temperature 1420±15°C with optical pyrometer verification."
            },
            {
                "id": "cp_init_2",
                "sequence": 2,
                "name": "Milling Surface Flatness & Bore",
                "process": available_steps[min(1, len(available_steps)-1)],
                "doc": "milling_spec_guide.pdf",
                "status": "Configuration Complete",
                "summary": "Face flatness within 0.025 mm, surface roughness Ra ≤ 1.6 µm."
            }
        ]

    # Form: Inputs at the top
    col_name, col_proc, col_add = st.columns([5, 5, 2])

    with col_name:
        st.markdown('<label class="form-label">Name <span class="required-star">*</span></label>', unsafe_allow_html=True)
        cp_name = st.text_input(
            label="Name",
            value="",
            placeholder="Enter checkpoint name...",
            label_visibility="collapsed",
            key="step3_name_input"
        )

    with col_proc:
        st.markdown('<label class="form-label">Process Step <span class="required-star">*</span></label>', unsafe_allow_html=True)
        cp_proc = st.selectbox(
            label="Process Step",
            options=process_options,
            index=0,
            label_visibility="collapsed",
            key="step3_process_select"
        )

    with col_add:
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True, key="step3_add_cp_btn"):
            if cp_name.strip() and cp_proc != "Select Process Step":
                # Generate AI Document & Quality Specification Summary
                with st.spinner("Analyzing checkpoint quality requirements with Gemini AI..."):
                    ai_summary = summarize_checkpoint_document(
                        checkpoint_name=cp_name.strip(),
                        process_name=cp_proc,
                        document_name=f"spec_{cp_name.strip().lower().replace(' ', '_')}.pdf"
                    )

                st.session_state.new_workflow_checkpoints.append({
                    "id": f"new_cp_{len(st.session_state.new_workflow_checkpoints) + 1}",
                    "name": cp_name.strip(),
                    "process": cp_proc,
                    "status": "Configuration Complete",
                    "summary": ai_summary,
                    "doc": f"spec_{cp_name.strip().lower().replace(' ', '_')}.pdf"
                })
                st.toast(f"Added checkpoint: {cp_name.strip()}")
                st.rerun()
            else:
                st.warning("Please specify checkpoint name and select a process step.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    checkpoints = st.session_state.new_workflow_checkpoints

    # Render Table with Interactive Action & Reorder Buttons
    with st.container(border=True):
        h1, h2, h3, h4, h5, h6, h7 = st.columns([0.8, 3.5, 3, 2, 1.8, 1.3, 1.3])
        h1.markdown("**Seq**")
        h2.markdown("**Checkpoint**")
        h3.markdown("**Process Step**")
        h4.markdown("**Document**")
        h5.markdown("**Status**")
        h6.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        h7.markdown("<div style='text-align: center;'><b>Reorder</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if not checkpoints:
            st.markdown("<div style='text-align: center; color: #94A3B8; padding: 24px;'>No checkpoints configured for this process yet. Add one above.</div>", unsafe_allow_html=True)
        else:
            for idx, item in enumerate(checkpoints):
                status_class = "badge-success" if item.get("status") == "Configuration Complete" else "badge-error"
                badge_html = f"<span class='badge-status {status_class}'><span style='font-size: 8px;'>●</span> {item.get('status', 'Complete')}</span>"
                doc_name = item.get("doc", "spec_sheet.pdf")

                c1, c2, c3, c4, c5, c6, c7 = st.columns([0.8, 3.5, 3, 2, 1.8, 1.3, 1.3])
                c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx + 1}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{item['name']}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='color: #475569;'>{item['process']}</span>", unsafe_allow_html=True)
                c4.markdown(f"<div class='upload-control-pill'><span>📎</span><span>{doc_name}</span></div>", unsafe_allow_html=True)
                c5.markdown(badge_html, unsafe_allow_html=True)
                
                with c6:
                    col_e, col_d = st.columns(2)
                    with col_e:
                        if st.button("✏️", key=f"edit_cp_{idx}", help="Edit Checkpoint"):
                            show_edit_checkpoint_modal(idx, item)
                    with col_d:
                        if st.button("🗑️", key=f"del_cp_{idx}", help="Delete Checkpoint"):
                            st.session_state.new_workflow_checkpoints.pop(idx)
                            st.toast(f"Removed checkpoint '{item['name']}'")
                            st.rerun()

                with c7:
                    col_up, col_down = st.columns(2)
                    with col_up:
                        if st.button("▲", key=f"up_cp_{idx}", help="Move Up", disabled=(idx == 0)):
                            checkpoints[idx], checkpoints[idx - 1] = checkpoints[idx - 1], checkpoints[idx]
                            st.rerun()
                    with col_down:
                        if st.button("▼", key=f"down_cp_{idx}", help="Move Down", disabled=(idx == len(checkpoints) - 1)):
                            checkpoints[idx], checkpoints[idx + 1] = checkpoints[idx + 1], checkpoints[idx]
                            st.rerun()

                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

    # Bottom navigation
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_prev, col_spacer, col_next = st.columns([1.5, 7, 1.5])

    with col_prev:
        if st.button("Previous", use_container_width=True, key="step3_prev"):
            st.session_state.process_step = 2
            st.rerun()

    with col_next:
        if st.button("Next", type="primary", use_container_width=True, key="step3_next"):
            st.session_state.process_step = 4
            st.rerun()
