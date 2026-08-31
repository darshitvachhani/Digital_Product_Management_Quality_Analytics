import streamlit as st

def render_sidebar():
    """
    Renders the consistent deep-blue sidebar with the 6 navigation items:
    - Dashboard
    - Products
    - Processes
    - Data Entry
    - Data Warehouse
    - User Management
    """
    with st.sidebar:
        # Direct sidebar CSS injection for tight vertical spacing & left alignment
        st.markdown("""
        <style>
        /* Collapse vertical spacing between elements in sidebar */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"],
        [data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
        [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div,
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
            gap: 2px !important;
        }

        [data-testid="stSidebar"] div.element-container,
        [data-testid="stSidebar"] div[data-testid="element-container"],
        section[data-testid="stSidebar"] div[data-testid="element-container"] {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
            margin-top: 0px !important;
            padding-top: 0px !important;
        }

        [data-testid="stSidebar"] div.stButton,
        section[data-testid="stSidebar"] div.stButton {
            margin: 0px 0px 4px 0px !important;
            padding: 0px !important;
        }

        /* Force left alignment on sidebar buttons with compact height */
        [data-testid="stSidebar"] div.stButton > button,
        [data-testid="stSidebar"] button {
            width: 100% !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-start !important;
            text-align: left !important;
            align-items: center !important;
            padding: 9px 14px !important;
            min-height: 38px !important;
            height: 40px !important;
            background-color: transparent !important;
            border: none !important;
            border-radius: 8px !important;
            margin: 0 !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] div.stButton button div,
        [data-testid="stSidebar"] div.stButton button p,
        [data-testid="stSidebar"] div.stButton button span,
        [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
            width: 100% !important;
            text-align: left !important;
            justify-content: flex-start !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            color: #94A3B8 !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }

        [data-testid="stSidebar"] div.stButton button:hover {
            background-color: #16253D !important;
        }

        [data-testid="stSidebar"] div.stButton button:hover p,
        [data-testid="stSidebar"] div.stButton button:hover div {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"] div.stButton button[kind="primary"] {
            background-color: #1A3154 !important;
            border-left: 4px solid #38BDF8 !important;
            border-radius: 0 8px 8px 0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        }

        [data-testid="stSidebar"] div.stButton button[kind="primary"] p,
        [data-testid="stSidebar"] div.stButton button[kind="primary"] div {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Brand Header
        st.markdown("""
        <div class="sidebar-brand-container" style="padding: 16px 14px 20px 14px; margin-bottom: 16px;">
            <div class="sidebar-brand-icon">Q</div>
            <div>
                <div class="sidebar-brand-text">QualIQ</div>
                <div class="sidebar-brand-sub">Quality Analytics</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        current_page = st.session_state.get("current_page", "Dashboard")
        # Normalize legacy names if present in state
        if current_page == "Product":
            current_page = "Products"
        elif current_page == "Process":
            current_page = "Processes"
        elif current_page == "User Manager":
            current_page = "User Management"

        # Navigation Items (Renamed per user request)
        nav_items = [
            ("Dashboard", "📊", "Dashboard"),
            ("Products", "📦", "Products"),
            ("Processes", "⚙️", "Processes"),
            ("Data Entry", "📥", "Data Entry"),
            ("Data Warehouse", "🗄️", "Data Warehouse"),
            ("User Management", "👥", "User Management")
        ]

        for page_name, icon, label in nav_items:
            is_active = (current_page == page_name)
            btn_label = f"{icon}  {label}"
            
            if st.button(
                btn_label,
                key=f"nav_btn_{page_name.replace(' ', '_').lower()}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                st.session_state.current_page = page_name
                if page_name == "Processes":
                    st.session_state.process_view_mode = "list"
                    st.session_state.process_step = 1
                st.rerun()

        # Bottom sidebar subtle system status badge
        st.markdown("""
        <div style="position: fixed; bottom: 16px; left: 16px; width: 220px; padding: 10px 12px; background: #132238; border-radius: 8px; border: 1px solid #1E2E48;">
            <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 2px;">System Environment</div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: #E2E8F0; font-weight: 500;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background-color: #10B981; display: inline-block;"></span>
                Manufacturing Line 04 (Live)
            </div>
        </div>
        """, unsafe_allow_html=True)
