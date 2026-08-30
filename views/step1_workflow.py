import streamlit as st
from components.header import render_top_header
from components.stepper import render_stepper
from db.repository import get_all_products

def render_step1_view():
    """
    SCREEN 2 — STEP 1
    Configure Process Policy Workflow (Create & Edit Modes)
    - Product * dropdown (locked in Edit Mode to prevent cross-product corruption)
    - Process Name * text input
    - Previous, Next buttons
    """
    render_top_header()
    render_stepper(1)

    is_edit_mode = st.session_state.get("is_edit_mode", False)
    title_text = "Edit Process Policy Workflow" if is_edit_mode else "Configure Process Policy Workflow"
    st.markdown(f'<h1 class="page-title">{title_text}</h1>', unsafe_allow_html=True)

    if is_edit_mode:
        st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; padding: 10px 14px; border-radius: 8px; font-size: 13.5px; margin-top: -12px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
            <span>✏️</span>
            <span>You are editing an existing process: <b>{st.session_state.get('new_workflow_name', '')}</b></span>
        </div>
        """, unsafe_allow_html=True)

    # 1. Fetch available products from DB
    db_products = get_all_products()
    product_options = ["Select Product"] + [p["name"] for p in db_products]

    current_product = st.session_state.get("new_workflow_product", "")
    prod_idx = product_options.index(current_product) if current_product in product_options else 0

    # Product * (Locked in Edit Mode)
    st.markdown('<label class="form-label">Product <span class="required-star">*</span></label>', unsafe_allow_html=True)
    selected_product = st.selectbox(
        label="Product",
        options=product_options,
        index=prod_idx,
        disabled=is_edit_mode,
        label_visibility="collapsed",
        key="step1_product_input"
    )
    if is_edit_mode:
        st.markdown('<div style="font-size: 12px; color: #64748B; margin-top: 4px;">🔒 Product target is locked in Edit Mode to protect associated inspection logs.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Process Name * (Text input)
    st.markdown('<label class="form-label">Process Name <span class="required-star">*</span></label>', unsafe_allow_html=True)
    current_name = st.session_state.get("new_workflow_name", "")
    process_name = st.text_input(
        label="Process Name",
        value=current_name,
        placeholder="Enter process workflow name...",
        label_visibility="collapsed",
        key="step1_process_name_input"
    )

    # Bottom navigation
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_prev, col_spacer, col_next = st.columns([1.5, 7, 1.5])

    with col_prev:
        st.button("Previous", disabled=True, use_container_width=True, key="step1_prev")

    with col_next:
        if st.button("Next", type="primary", use_container_width=True, key="step1_next"):
            if not process_name.strip():
                st.warning("Please enter a process name.")
            elif selected_product == "Select Product" and not is_edit_mode:
                st.warning("Please select a target product.")
            else:
                st.session_state.new_workflow_product = selected_product if selected_product != "Select Product" else current_product
                st.session_state.new_workflow_name = process_name.strip()
                st.session_state.process_step = 2
                st.rerun()
