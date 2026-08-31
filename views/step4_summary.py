import streamlit as st
from components.header import render_top_header
from components.stepper import render_stepper
from db.repository import create_full_process_workflow, update_full_process_workflow
from utils.excel_generator import generate_checkpoint_template_excel, get_required_columns_for_checkpoint

@st.dialog(" ", width="small")
def show_success_modal(message: str = "Process configured successfully"):
    """
    PROPER CENTRED MODAL DIALOG:
    - Green success/check icon
    - Dynamic success message (configured or updated)
    - Blue "OK" button below message
    - Clicking OK redirects user to main Process List page
    """
    st.markdown(f"""<div style="text-align: center; padding: 8px 12px 18px 12px;">
<div style="width: 58px; height: 58px; border-radius: 50%; background-color: #DCFCE7; color: #16A34A; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; margin-bottom: 16px; border: 2px solid #86EFAC; box-shadow: 0 4px 10px rgba(22, 163, 74, 0.15);">✓</div>
<div style="font-size: 19px; font-weight: 700; color: #0F172A; margin-bottom: 22px; font-family: 'Inter', sans-serif;">{message}</div>
</div>""", unsafe_allow_html=True)
    
    if st.button("OK", type="primary", use_container_width=True, key="btn_modal_ok_redirect"):
        st.session_state.is_edit_mode = False
        st.session_state.editing_process_id = None
        st.session_state.process_view_mode = "list"
        st.session_state.process_step = 1
        st.rerun()

def render_step4_view():
    """
    SCREEN 5 — STEP 4
    Summary & Reference Excel Template Generator
    """
    render_top_header()
    render_stepper(4)

    is_edit_mode = st.session_state.get("is_edit_mode", False)
    editing_process_id = st.session_state.get("editing_process_id")
    
    title_text = "Edit Summary & Review" if is_edit_mode else "Summary"
    st.markdown(f'<h1 class="page-title">{title_text}</h1>', unsafe_allow_html=True)

    product_name = st.session_state.get("new_workflow_product", "") or "Tractor Engine Cover"
    process_name = st.session_state.get("new_workflow_name", "") or "New Process Workflow"
    steps = st.session_state.get("new_workflow_steps", [])
    checkpoints = st.session_state.get("new_workflow_checkpoints", [])

    st.markdown(f"""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; display: flex; gap: 32px;">
<div>
<span style="font-size: 12px; text-transform: uppercase; color: #64748B; font-weight: 600; letter-spacing: 0.5px;">Product Target</span>
<div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-top: 2px;">{product_name}</div>
</div>
<div>
<span style="font-size: 12px; text-transform: uppercase; color: #64748B; font-weight: 600; letter-spacing: 0.5px;">Process Workflow</span>
<div style="font-size: 15px; font-weight: 700; color: #2563EB; margin-top: 2px;">{process_name}</div>
</div>
<div>
<span style="font-size: 12px; text-transform: uppercase; color: #64748B; font-weight: 600; letter-spacing: 0.5px;">Total Steps</span>
<div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-top: 2px;">{len(steps)} Steps</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;">
        <div style="font-size: 13.5px; font-weight: 700; color: #1E40AF; margin-bottom: 4px;">📊 Checkpoint Quality Data Contracts & Sample Excel Reference Templates</div>
        <div style="font-size: 12.5px; color: #3B82F6;">Download official pre-formatted Excel reference templates for each checkpoint below. These templates define the exact required column names to pass shopfloor upload validation.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 12px;">Configured Checkpoints & Downloadable Templates</div>', unsafe_allow_html=True)

    effective_checkpoints = checkpoints if checkpoints else [
        {"name": f"{process_name} Quality Gate 1", "process": steps[0] if steps else "Step 1", "summary": f"Standard quality gate for {process_name}."}
    ]

    for idx, cp in enumerate(effective_checkpoints, start=1):
        cp_name = cp.get("name", "Checkpoint")
        req_cols = get_required_columns_for_checkpoint(cp_name)
        excel_bytes = generate_checkpoint_template_excel(cp_name)
        clean_filename = f"Template_{cp_name.replace(' ', '_').replace('/', '_')}.xlsx"

        with st.container(border=True):
            col_info, col_dl = st.columns([7.5, 2.5])
            
            with col_info:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="background: #E2E8F0; color: #334155; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 4px;">Gate #{idx}</span>
                    <span style="font-size: 15px; font-weight: 700; color: #0F172A;">{cp_name}</span>
                    <span style="font-size: 13px; color: #64748B;">• Step: {cp.get('process', steps[0] if steps else 'General')}</span>
                </div>
                <div style="font-size: 13px; color: #475569; margin-bottom: 8px; line-height: 1.4;">
                    {cp.get('summary', 'Standard tolerance verification inspection.')}
                </div>
                <div style="font-size: 12px; color: #64748B;">
                    <b>Required Column Schema:</b> <code>{' | '.join(req_cols)}</code>
                </div>
                """, unsafe_allow_html=True)

            with col_dl:
                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 Sample Excel (.xlsx)",
                    data=excel_bytes,
                    file_name=clean_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_template_step4_{idx}_{cp_name[:15]}",
                    use_container_width=True,
                    help=f"Download official reference template for {cp_name}"
                )

    # Bottom navigation
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_prev, col_spacer, col_finish = st.columns([1.5, 7, 1.5])

    with col_prev:
        if st.button("Previous", use_container_width=True, key="step4_prev"):
            st.session_state.process_step = 3
            st.rerun()

    with col_finish:
        if st.button("Finish", type="primary", use_container_width=True, key="step4_finish"):
            save_checkpoints = checkpoints if checkpoints else [
                {"name": f"{process_name} Quality Gate 1", "process": steps[0] if steps else "Step 1", "status": "Configuration Complete", "summary": f"Initial verification check for {process_name}."}
            ]
            save_steps = steps if steps else [f"{process_name} Step 1"]

            if is_edit_mode and editing_process_id:
                try:
                    update_full_process_workflow(
                        process_id=editing_process_id,
                        process_name=process_name.strip(),
                        steps=save_steps,
                        checkpoints=save_checkpoints
                    )
                    show_success_modal("Process updated successfully")
                except Exception as e:
                    st.error(f"Error updating database: {e}")
            else:
                try:
                    create_full_process_workflow(
                        product_name=product_name,
                        process_name=process_name.strip(),
                        steps=save_steps,
                        checkpoints=save_checkpoints
                    )
                    show_success_modal("Process configured successfully")
                except Exception as e:
                    st.error(f"Error saving to database: {e}")
