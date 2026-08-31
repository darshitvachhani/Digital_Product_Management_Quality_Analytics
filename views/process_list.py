import streamlit as st
from components.header import render_top_header
from db.repository import get_all_products, get_all_processes, get_process_full_details

@st.dialog("Process Checkpoint Flow", width="large")
def show_process_flow_dialog(proc_id: int):
    """
    VISUAL STEP-BY-STEP WORKFLOW FLOW DIALOG
    - Modal dialog dismissable via top-right ✕ cross
    - Flow-like step-by-step sequential cards connected with arrows (➔)
    - Multi-line wrap support
    - Includes checkpoint name, sequence, SOP document, and summary
    """
    proc_data = get_process_full_details(proc_id)
    if not proc_data:
        st.error("Process details not found.")
        return

    st.markdown(f"""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center;">
<div>
<div style="font-size: 11px; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.5px;">PROCESS WORKFLOW</div>
<div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{proc_data['process_name']}</div>
<div style="font-size: 13px; color: #475569; margin-top: 2px;">Product: <b>{proc_data['product_name']}</b> ({proc_data.get('product_code', '')})</div>
</div>
<div>
<span style="background: #DCFCE7; color: #166534; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">● {proc_data['status']}</span>
</div>
</div>""", unsafe_allow_html=True)

    checkpoints = proc_data.get("checkpoints", [])
    steps = proc_data.get("steps", [])

    st.markdown('<div style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 12px;">Sequential Quality Checkpoints Flow</div>', unsafe_allow_html=True)

    if not checkpoints:
        st.info("No checkpoints configured for this process yet.")
        return

    # Render flow cards using a flexbox container with zero-indent lines
    flow_items = []
    for idx, cp in enumerate(checkpoints, start=1):
        step_name = cp.get("process") or (steps[idx-1] if idx <= len(steps) else "Process Step")
        doc_name = cp.get("upload_document_name") or cp.get("doc") or "Standard SOP"
        summary_text = cp.get("summary") or "Quality tolerance and parameter verification check."

        card = (
            f'<div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 14px 16px; min-width: 230px; max-width: 270px; flex: 1 1 230px; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04); margin-bottom: 12px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
            f'<span style="background: #2563EB; color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;">Gate {idx}</span>'
            f'<span style="font-size: 11px; color: #16A34A; font-weight: 600;">✓ Active</span>'
            f'</div>'
            f'<div style="font-size: 14px; font-weight: 700; color: #0F172A; margin-bottom: 4px; line-height: 1.3;">{cp["name"]}</div>'
            f'<div style="font-size: 11.5px; color: #64748B; margin-bottom: 6px;"><b>Step:</b> {step_name}</div>'
            f'<div style="font-size: 12px; color: #334155; line-height: 1.4; margin-bottom: 8px; background: #F8FAFC; padding: 6px 8px; border-radius: 4px; border: 1px solid #F1F5F9;">{summary_text}</div>'
            f'<div style="font-size: 11px; color: #2563EB; display: flex; align-items: center; gap: 4px;"><span>📄</span> <span style="font-family: monospace; font-weight: 600;">{doc_name}</span></div>'
            f'</div>'
        )
        flow_items.append(card)

        # Add arrow if not the last item
        if idx < len(checkpoints):
            arrow = (
                f'<div style="display: flex; align-items: center; justify-content: center; font-size: 24px; color: #64748B; padding: 0 6px; margin-bottom: 12px; font-weight: bold;">'
                f'➔'
                f'</div>'
            )
            flow_items.append(arrow)

    flow_container_html = (
        f'<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 10px 4px;">'
        f'{"".join(flow_items)}'
        f'</div>'
    )

    st.markdown(flow_container_html, unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

def render_process_list_view():
    """
    PROCESS LIST SCREEN
    - Filter by Product dropdown
    - "+ Add New Process" button (launches 4-step workflow in Create Mode)
    - "👁️" View button on each row (opens interactive flow diagram modal)
    - "✏️" Edit button on each row (launches 4-step workflow in Edit Mode)
    """
    render_top_header("Process List")

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 20px;">
Manage, inspect, and configure manufacturing process quality policies across product lines.
</div>""", unsafe_allow_html=True)

    # 1. Fetch available products for filter dropdown
    products = get_all_products()
    filter_options = ["All Products"] + [p["name"] for p in products]

    # Controls Row: Filter by Product & + Add New Process button
    col_filter, col_spacer, col_btn = st.columns([3.5, 4.5, 2])

    with col_filter:
        st.markdown('<label class="form-label" style="font-size: 13.5px; margin-bottom: 4px;">Filter by Product</label>', unsafe_allow_html=True)
        selected_filter = st.selectbox(
            label="Filter by Product",
            options=filter_options,
            index=0,
            label_visibility="collapsed",
            key="process_list_filter_product"
        )

    with col_btn:
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        if st.button("➕  Add New Process", type="primary", use_container_width=True, key="btn_add_new_process"):
            st.session_state.is_edit_mode = False
            st.session_state.editing_process_id = None
            st.session_state.new_workflow_product = ""
            st.session_state.new_workflow_name = ""
            st.session_state.new_workflow_steps = []
            st.session_state.new_workflow_checkpoints = []
            st.session_state.process_view_mode = "workflow"
            st.session_state.process_step = 1
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Fetch processes based on filter
    processes = get_all_processes(selected_filter)

    # Render Table with Interactive Action Buttons
    with st.container(border=True):
        # Table Header
        h1, h2, h3, h4, h5 = st.columns([1, 4.2, 3, 2, 1.8])
        h1.markdown("**S.No.**")
        h2.markdown("**Process**")
        h3.markdown("**Product**")
        h4.markdown("**Status**")
        h5.markdown("<div style='text-align: center;'><b>Actions</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if not processes:
            st.markdown("<div style='text-align: center; color: #94A3B8; padding: 24px;'>No processes configured for the selected product. Click <b>+ Add New Process</b> to configure one.</div>", unsafe_allow_html=True)
        else:
            for idx, proc in enumerate(processes, start=1):
                status = proc["status"]
                if status in ("Active", "Complete"):
                    badge_html = f"<span class='badge-status badge-success'><span style='font-size: 8px;'>●</span> {status}</span>"
                elif status == "Incomplete":
                    badge_html = f"<span class='badge-status badge-warning'><span style='font-size: 8px;'>●</span> {status}</span>"
                else:
                    badge_html = f"<span class='badge-status badge-inactive'><span style='font-size: 8px;'>●</span> {status}</span>"

                c1, c2, c3, c4, c5 = st.columns([1, 4.2, 3, 2, 1.8])
                c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{proc['process_name']}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='color: #334155;'>{proc['product_name']}</span>", unsafe_allow_html=True)
                c4.markdown(badge_html, unsafe_allow_html=True)
                
                with c5:
                    col_v, col_e = st.columns(2)
                    with col_v:
                        if st.button("👁️", key=f"view_proc_btn_{proc['id']}", help="View step-by-step checkpoint flow"):
                            show_process_flow_dialog(proc["id"])
                    with col_e:
                        if st.button("✏️", key=f"edit_proc_btn_{proc['id']}", help="Edit this process in 4-step wizard"):
                            proc_data = get_process_full_details(proc["id"])
                            if proc_data:
                                st.session_state.is_edit_mode = True
                                st.session_state.editing_process_id = proc["id"]
                                st.session_state.new_workflow_product = proc_data["product_name"]
                                st.session_state.new_workflow_name = proc_data["process_name"]
                                st.session_state.new_workflow_steps = proc_data["steps"]
                                st.session_state.new_workflow_checkpoints = proc_data["checkpoints"]
                                st.session_state.process_view_mode = "workflow"
                                st.session_state.process_step = 1
                                st.rerun()
                
                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
