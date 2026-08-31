import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="QualIQ | Manufacturing Quality Analytics",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema & Master Seed Data
from db.schema import init_db
init_db()

from components.styles import inject_custom_styles
from components.sidebar import render_sidebar
from views.dashboard import render_dashboard_view
from views.process_list import render_process_list_view
from views.step1_workflow import render_step1_view
from views.step2_steps import render_step2_view
from views.step3_checkpoints import render_step3_view
from views.step4_summary import render_step4_view
from views.product_view import render_product_view
from views.data_entry_view import render_data_entry_view
from views.data_warehouse_view import render_data_warehouse_view
from views.user_manager_view import render_user_manager_view

# Initialize Session State
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if "process_view_mode" not in st.session_state:
    st.session_state.process_view_mode = "list"

if "process_step" not in st.session_state:
    st.session_state.process_step = 1

# Inject Design System Styles
inject_custom_styles()

# Render Global Sidebar
render_sidebar()

# Main Content Routing
page = st.session_state.current_page

if page == "Dashboard":
    render_dashboard_view()
elif page in ("Products", "Product"):
    render_product_view()
elif page in ("Processes", "Process"):
    if st.session_state.get("process_view_mode", "list") == "list":
        render_process_list_view()
    else:
        step = st.session_state.get("process_step", 1)
        if step == 1:
            render_step1_view()
        elif step == 2:
            render_step2_view()
        elif step == 3:
            render_step3_view()
        elif step == 4:
            render_step4_view()
elif page == "Data Entry":
    render_data_entry_view()
elif page == "Data Warehouse":
    render_data_warehouse_view()
elif page in ("User Management", "User Manager"):
    render_user_manager_view()
