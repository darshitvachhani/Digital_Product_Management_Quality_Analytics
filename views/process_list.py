import streamlit as st
from components.header import render_top_header
from db.repository import get_all_products, get_all_processes, get_process_full_details

def render_process_list_view():
    """
    PROCESS LIST SCREEN
    - Filter by Product dropdown
    - "+ Add New Process" button (launches 4-step workflow in Create Mode)
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
        h1, h2, h3, h4, h5 = st.columns([1, 4.5, 3, 2, 1.2])
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

                c1, c2, c3, c4, c5 = st.columns([1, 4.5, 3, 2, 1.2])
                c1.markdown(f"<span style='font-weight: 600; color: #475569;'>{idx}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-weight: 600; color: #0F172A;'>{proc['process_name']}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='color: #334155;'>{proc['product_name']}</span>", unsafe_allow_html=True)
                c4.markdown(badge_html, unsafe_allow_html=True)
                
                with c5:
                    if st.button("✏️", key=f"edit_proc_btn_{proc['id']}", help="Edit this process in 4-step wizard"):
                        # Hydrate full details and enter 4-step Edit Mode
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
