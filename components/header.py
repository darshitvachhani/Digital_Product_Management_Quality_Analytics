import streamlit as st

USERS_LIST = [
    {
        "name": "Alexander Wright",
        "email": "alex.wright@qualiq.io",
        "role": "Quality Director (Admin)",
        "badge": "👑 Admin (Full Access)",
        "description": "Superuser: Unrestricted access to all checkpoints & any file format."
    },
    {
        "name": "David Chang",
        "email": "david.chang@qualiq.io",
        "role": "Shopfloor Inspector",
        "badge": "👷 Shopfloor Inspector",
        "description": "Restricted to Foundry & Casting checkpoints with strict column validation."
    },
    {
        "name": "Elena Rostova",
        "email": "elena.rostova@qualiq.io",
        "role": "Lead Process Engineer",
        "badge": "⚙️ Process Engineer",
        "description": "Restricted to CNC Machining & Dimensions checkpoints with column validation."
    },
    {
        "name": "Sarah Jenkins",
        "email": "sarah.jenkins@qualiq.io",
        "role": "Senior Metrology Specialist",
        "badge": "🔬 Metrology Specialist",
        "description": "Restricted to CMM & G&T Inspection checkpoints with column validation."
    }
]

def get_current_user():
    """Retrieves the active user session or defaults to Alexander Wright."""
    if "current_user" not in st.session_state:
        st.session_state.current_user = USERS_LIST[0]
    return st.session_state.current_user

def render_top_header(title: str = ""):
    """
    Renders top header with interactive User / Role Switcher in the top right.
    """
    current_user = get_current_user()
    
    col_title, col_profile = st.columns([5.2, 1.8])

    with col_title:
        if title:
            st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)

    with col_profile:
        # Display active role badge in popover trigger
        btn_label = f"👤 {current_user['name'].split()[0]} ({current_user['role'].split()[0]})"
        
        with st.popover(btn_label, use_container_width=True):
            st.markdown(f"""
            <div style="padding: 4px 0 8px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 10px;">
                <div style="font-weight: 700; font-size: 14px; color: #0F172A;">{current_user['name']}</div>
                <div style="font-size: 12px; color: #2563EB; font-weight: 600;">{current_user['role']}</div>
                <div style="font-size: 11.5px; color: #64748B; margin-top: 2px;">{current_user['email']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 4px;">SWITCH ACTIVE USER / ROLE:</div>', unsafe_allow_html=True)
            
            user_options = [u["name"] for u in USERS_LIST]
            cur_idx = user_options.index(current_user["name"]) if current_user["name"] in user_options else 0
            
            selected_user_name = st.selectbox(
                label="Switch User",
                options=user_options,
                index=cur_idx,
                label_visibility="collapsed",
                key="header_switch_user_select"
            )

            if selected_user_name != current_user["name"]:
                new_u = next(u for u in USERS_LIST if u["name"] == selected_user_name)
                st.session_state.current_user = new_u
                st.toast(f"Switched active user to {new_u['name']} ({new_u['role']})")
                st.rerun()

            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 10px; border-radius: 6px; font-size: 11.5px; color: #64748B; margin: 10px 0;">
                <b>Role Scope:</b> {current_user['description']}
            </div>
            """, unsafe_allow_html=True)
