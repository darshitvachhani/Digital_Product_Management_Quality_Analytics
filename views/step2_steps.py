import streamlit as st
from components.header import render_top_header
from components.stepper import render_stepper

@st.dialog("Edit Process Step", width="medium")
def show_edit_step_modal(idx: int, current_name: str):
    st.markdown(f'<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Edit name for Step #{idx + 1}.</div>', unsafe_allow_html=True)
    new_name = st.text_input("Process Step Name *", value=current_name)
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Step", type="primary", use_container_width=True):
            if new_name.strip():
                # 1. Update step name
                st.session_state.new_workflow_steps[idx] = new_name.strip()
                
                # 2. Cascade update to mapped checkpoints
                if "new_workflow_checkpoints" in st.session_state and st.session_state.new_workflow_checkpoints:
                    for cp in st.session_state.new_workflow_checkpoints:
                        if cp.get("process") == current_name:
                            cp["process"] = new_name.strip()

                st.toast(f"Updated Step #{idx + 1}!")
                st.rerun()
            else:
                st.warning("Please enter a step name.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_step2_view():
    """
    SCREEN 3 — STEP 2
    Transaction Process Steps — Clean empty state on create, full CRUD on steps
    """
    render_top_header()
    render_stepper(2)

    is_edit_mode = st.session_state.get("is_edit_mode", False)
    st.markdown('<h1 class="page-title">Transaction Process Steps</h1>', unsafe_allow_html=True)

    if is_edit_mode:
        st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; padding: 10px 14px; border-radius: 8px; font-size: 13.5px; margin-top: -12px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
            <span>✏️</span>
            <span>Editing steps for process: <b>{st.session_state.get('new_workflow_name', '')}</b></span>
        </div>
        """, unsafe_allow_html=True)

    # Initialize workflow steps cleanly to empty list if not present
    if "new_workflow_steps" not in st.session_state or st.session_state.new_workflow_steps is None:
        st.session_state.new_workflow_steps = []

    # Form: Add Process Step * + Circular + Button
    st.markdown('<label class="form-label">Add Process Step <span class="required-star">*</span></label>', unsafe_allow_html=True)
    
    col_input, col_plus = st.columns([11, 1])
    with col_input:
        step_input = st.text_input(
            label="Add Process Step",
            value="",
            placeholder="e.g. Ingot Melting & Temperature Check...",
            label_visibility="collapsed",
            key="step2_new_step_input"
        )
    with col_plus:
        if st.button("➕", key="step2_add_btn", help="Add step to table"):
            if step_input.strip():
                st.session_state.new_workflow_steps.append(step_input.strip())
                st.toast(f"Added step: {step_input.strip()}")
                st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        h1, h2, h3, h4 = st.columns([1.5, 6, 2, 2])
        h1.markdown("**Sequence**")
        h2.markdown("**Process Step Name**")
        h3.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        h4.markdown("<div style='text-align: center;'><b>Reorder</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        steps = st.session_state.new_workflow_steps
        if not steps:
            st.markdown("<div style='text-align: center; color: #94A3B8; padding: 24px;'>No process steps added yet. Type a step name above and click <b>➕</b> to add one.</div>", unsafe_allow_html=True)
        else:
            for idx, step_name in enumerate(steps):
                c1, c2, c3, c4 = st.columns([1.5, 6, 2, 2])
                c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx + 1}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{step_name}</span>", unsafe_allow_html=True)
                
                with c3:
                    col_e, col_d = st.columns(2)
                    with col_e:
                        if st.button("✏️", key=f"edit_step_{idx}", help="Edit step"):
                            show_edit_step_modal(idx, step_name)
                    with col_d:
                        if st.button("🗑️", key=f"del_step_{idx}", help="Delete step"):
                            st.session_state.new_workflow_steps.pop(idx)
                            st.toast(f"Deleted step #{idx + 1}")
                            st.rerun()

                with c4:
                    col_up, col_down = st.columns(2)
                    with col_up:
                        if st.button("▲", key=f"up_step_{idx}", help="Move Up", disabled=(idx == 0)):
                            steps[idx], steps[idx - 1] = steps[idx - 1], steps[idx]
                            st.rerun()
                    with col_down:
                        if st.button("▼", key=f"down_step_{idx}", help="Move Down", disabled=(idx == len(steps) - 1)):
                            steps[idx], steps[idx + 1] = steps[idx + 1], steps[idx]
                            st.rerun()

                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

    # Bottom navigation
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_prev, col_spacer, col_next = st.columns([1.5, 7, 1.5])

    with col_prev:
        if st.button("Previous", use_container_width=True, key="step2_prev"):
            st.session_state.process_step = 1
            st.rerun()

    with col_next:
        if st.button("Next", type="primary", use_container_width=True, key="step2_next"):
            if not st.session_state.new_workflow_steps:
                st.warning("Please add at least one process step before continuing.")
            else:
                st.session_state.process_step = 3
                st.rerun()
