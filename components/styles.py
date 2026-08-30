import streamlit as st

def inject_custom_styles():
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-navy: #0B192C;
        --secondary-navy: #1E293B;
        --accent-blue: #2563EB;
        --accent-blue-hover: #1D4ED8;
        --accent-light-blue: #EFF6FF;
        --text-dark: #0F172A;
        --text-muted: #64748B;
        --border-light: #E2E8F0;
        --bg-main: #F8FAFC;
        --bg-card: #FFFFFF;
        --success-green: #16A34A;
        --success-bg: #DCFCE7;
        --error-red: #DC2626;
        --error-bg: #FEE2E2;
    }

    /* Global Typography & Background */
    html, body {
        font-family: 'Inter', 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: var(--text-dark);
        background-color: var(--bg-main);
    }

    .stApp {
        background-color: var(--bg-main);
    }

    /* Hide Streamlit Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--primary-navy) !important;
        border-right: 1px solid #1E293B !important;
    }

    section[data-testid="stSidebar"] * {
        color: #E2E8F0;
    }

    .sidebar-brand-container {
        padding: 20px 14px 28px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid #1E2E48;
        margin-bottom: 24px;
    }

    .sidebar-brand-icon {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #2563EB, #38BDF8);
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 20px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
    }

    .sidebar-brand-text {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .sidebar-brand-sub {
        font-size: 11px;
        color: #94A3B8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Target all Streamlit sidebar buttons specifically */
    section[data-testid="stSidebar"] div[data-testid="stButton"] {
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    section[data-testid="stSidebar"] button {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-start !important;
        text-align: left !important;
        align-items: center !important;
        padding: 12px 18px !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] button div[data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] div[data-testid="stButton"] button [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] button div[data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 16.5px !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }

    section[data-testid="stSidebar"] button:hover {
        background-color: #16253D !important;
    }

    section[data-testid="stSidebar"] button:hover [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] button:active,
    section[data-testid="stSidebar"] button:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Active Nav Item */
    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
        background-color: #1A3154 !important;
        border-left: 4px solid #38BDF8 !important;
        border-radius: 0 8px 8px 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }

    section[data-testid="stSidebar"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1280px;
    }

    /* Page Titles */
    .page-title {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-dark);
        margin-top: 4px;
        margin-bottom: 18px;
        letter-spacing: -0.4px;
    }

    .page-subtitle {
        font-size: 15px;
        font-weight: 500;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }

    /* Form Inputs */
    .form-label {
        font-size: 14px;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 6px;
        display: block;
    }

    .required-star {
        color: #EF4444;
        font-weight: bold;
    }

    /* Card Containers */
    .qualiq-card {
        background: #FFFFFF;
        border: 1px solid var(--border-light);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }

    /* Large Empty Dashboard Workspace */
    .dashboard-workspace {
        width: 100%;
        min-height: 480px;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        background-color: #FFFFFF;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 24px;
        padding: 40px;
        box-sizing: border-box;
    }

    .workspace-empty-icon {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background-color: #F1F5F9;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #94A3B8;
        font-size: 24px;
        margin-bottom: 14px;
    }

    .workspace-empty-text {
        font-size: 15px;
        font-weight: 500;
        color: #94A3B8;
        letter-spacing: 0.2px;
    }

    /* Custom Tables */
    .qualiq-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid var(--border-light);
        border-radius: 10px;
        overflow: hidden;
        margin-top: 16px;
        background: #FFFFFF;
    }

    .qualiq-table th {
        background-color: #F8FAFC;
        color: #475569;
        font-weight: 600;
        font-size: 13.5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 14px 18px;
        border-bottom: 1px solid var(--border-light);
        text-align: left;
    }

    .qualiq-table td {
        padding: 14px 18px;
        font-size: 14.5px;
        color: #1E293B;
        border-bottom: 1px solid var(--border-light);
        vertical-align: middle;
    }

    .qualiq-table tr:last-child td {
        border-bottom: none;
    }

    .qualiq-table tr:hover td {
        background-color: #F8FAFC;
    }

    /* Badges */
    .badge-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12.5px;
        font-weight: 600;
        line-height: 1;
    }

    .badge-success {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #86EFAC;
    }

    .badge-error {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
    }

    .badge-inactive {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #CBD5E1;
    }

    .badge-warning {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FCD34D;
    }

    /* Action Buttons in Tables */
    .action-group {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .table-icon-btn {
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 6px 9px;
        color: #475569;
        cursor: pointer;
        font-size: 13px;
        transition: all 0.15s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    .table-icon-btn:hover {
        background: #E2E8F0;
        color: #0F172A;
    }

    /* Upload visual pill/button */
    .upload-control-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 14px;
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        color: #334155;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
    }

    .upload-control-pill:hover {
        background-color: #F1F5F9;
        border-color: #94A3B8;
    }

    /* Bottom Navigation Container */
    .bottom-nav-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 32px;
        padding-top: 20px;
        border-top: 1px solid var(--border-light);
    }

    /* Modal / Dialog Customization */
    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 16px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 20px 35px -5px rgba(15, 23, 42, 0.25) !important;
        background-color: #FFFFFF !important;
        padding: 24px !important;
    }

    div[data-testid="stDialog"] div[data-testid="stModalHeader"] {
        display: none !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
