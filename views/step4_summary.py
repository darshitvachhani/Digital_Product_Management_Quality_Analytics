import streamlit as st
from components.header import render_top_header
from components.stepper import render_stepper
from db.repository import create_full_process_workflow, update_full_process_workflow

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
    Summary — Persists workflow to SQLite Database on Finish (Create & Edit Modes)
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

    st.markdown('<div style="font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 12px;">Workflow Configuration Summary</div>', unsafe_allow_html=True)

    # Build summary rows without leading indentation
    if checkpoints:
        rows = []
        for idx, cp in enumerate(checkpoints, start=1):
            rows.append(
                f"<tr>"
                f"<td style='font-weight: 600; color: #475569;'>{idx}</td>"
                f"<td style='font-weight: 600; color: #0F172A;'>{cp['name']}</td>"
                f"<td style='color: #475569;'>{cp.get('process', '')}</td>"
                f"<td style='color: #334155; font-size: 13.5px; line-height: 1.45;'>{cp.get('summary', 'Standard tolerance verification.')}</td>"
                f"</tr>"
            )
        rows_html = "\n".join(rows)
    else:
        rows_html = f"""<tr>
<td style='font-weight: 600; color: #475569;'>1</td>
<td style='font-weight: 600; color: #0F172A;'>{process_name} Gate Check</td>
<td style='color: #475569;'>{steps[0] if steps else 'Standard Step'}</td>
<td style='color: #334155; font-size: 13.5px; line-height: 1.45;'>Standard tolerance and dimension verification check for {process_name}.</td>
</tr>"""

    table_html = f"""<table class="qualiq-table" style="margin-top: 0;">
<thead>
<tr>
<th style="width: 8%;">Sequence</th>
<th style="width: 26%;">Checkpoint</th>
<th style="width: 26%;">Process Step</th>
<th style="width: 40%;">Summary</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>"""

    st.markdown(table_html, unsafe_allow_html=True)

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
