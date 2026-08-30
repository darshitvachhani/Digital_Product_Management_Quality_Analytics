import streamlit as st

def render_top_header(title: str = ""):
    """
    Renders top header with Profile Menu at the extreme top-right.
    """
    col_title, col_profile = st.columns([5, 1])

    with col_title:
        if title:
            st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)

    with col_profile:
        col_space, col_pop = st.columns([1, 2])
        with col_pop:
            with st.popover("👤 Admin", use_container_width=True):
                st.markdown("""
                <div style="padding: 4px 0 8px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 14px; color: #0F172A;">Alexander Wright</div>
                    <div style="font-size: 12px; color: #64748B;">alex.wright@qualiq.io</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("👤 Profile", use_container_width=True, key="hdr_profile"):
                    st.toast("Viewing Profile")
                if st.button("💳 Account", use_container_width=True, key="hdr_account"):
                    st.toast("Opening Account details")
                if st.button("⚙️ Settings", use_container_width=True, key="hdr_settings"):
                    st.toast("Opening Settings")
                if st.button("💎 Subscription", use_container_width=True, key="hdr_subscription"):
                    st.toast("Viewing Subscription tier")
                st.markdown("<hr style='margin: 6px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
                if st.button("🚪 Logout", use_container_width=True, key="hdr_logout"):
                    st.toast("Logged out (Visual Prototype)")
