import streamlit as st
from datetime import datetime
from components.header import render_top_header
from ai.dashboard_generator import generate_quality_analytics_dashboard, generate_saved_version_dashboard
from ai.chart_insights import generate_chart_action_insight
from utils.pdf_generator import generate_quality_report_pdf
from db.repository import (
    get_all_dashboard_versions,
    get_dashboard_version_by_id,
    save_dashboard_version,
    delete_dashboard_version
)

def format_date_str(val) -> str:
    """Safely formats datetime object or ISO string to YYYY-MM-DD."""
    if not val:
        return datetime.now().strftime("%Y-%m-%d")
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return str(val)[:10]

@st.dialog("Save Dashboard Version", width="medium")
def show_save_version_modal(current_prompt: str, current_data: dict):
    st.markdown('<div style="font-size: 13.5px; color: #64748B; margin-bottom: 16px;">Save the current quality analytics snapshot as a persistent version preset.</div>', unsafe_allow_html=True)
    
    ver_name = st.text_input("Version Preset Name *", placeholder="e.g. Q3 Line 01 Deep Dive")
    author = st.text_input("Created By", value="Alexander Wright (Quality Director)")
    
    st.markdown(f"""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 6px; font-size: 12.5px; color: #475569; margin: 10px 0;">
        <b>Associated Prompt:</b> {current_prompt}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Save Version", type="primary", use_container_width=True):
            if ver_name.strip():
                save_dashboard_version(ver_name.strip(), current_prompt, current_data, author.strip())
                st.toast(f"Saved dashboard version: '{ver_name.strip()}'!")
                st.rerun()
            else:
                st.warning("Please provide a version name.")
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Manage Saved Versions", width="medium")
def show_manage_versions_modal():
    st.markdown('<div style="font-size: 13.5px; color: #64748B; margin-bottom: 14px;">Review and manage saved quality dashboard presets.</div>', unsafe_allow_html=True)
    
    versions = get_all_dashboard_versions()
    if not versions:
        st.info("No saved dashboard versions found.")
        return

    for v in versions:
        col_info, col_del = st.columns([8.5, 1.5])
        with col_info:
            date_display = format_date_str(v.get("created_at"))
            st.markdown(f"<b>{v['name']}</b><br><span style='font-size: 12px; color: #64748B;'>By {v['created_by']} • {date_display}</span>", unsafe_allow_html=True)
        with col_del:
            if st.button("🗑️", key=f"del_ver_modal_{v['id']}", help="Delete version"):
                delete_dashboard_version(v["id"])
                st.toast(f"Deleted version '{v['name']}'")
                st.rerun()
        st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

def render_dashboard_view():
    """
    QUALITY ANALYTICS DASHBOARD WITH PERSISTENT VERSIONING & PDF EXPORT
    """
    render_top_header("Quality Analytics Dashboard")

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 20px;">
AI-enhanced manufacturing quality analytics, root cause investigation, dynamic dashboard generation, and executive PDF reporting.
</div>""", unsafe_allow_html=True)

    default_prompt = "Generate a quality analytics dashboard suitable to the uploaded data"

    # --- 1. Version Preset Selector Bar ---
    saved_versions = get_all_dashboard_versions()
    version_options = ["-- Custom Prompt / Select a Saved Version --"] + [
        f"v{v['id']}: {v['name']} ({format_date_str(v.get('created_at'))})" for v in saved_versions
    ]

    has_dashboard = "cached_dashboard_data" in st.session_state and st.session_state.cached_dashboard_data is not None

    with st.container(border=True):
        col_ver_sel, col_ver_btn = st.columns([8.2, 2.8])
        
        with col_ver_sel:
            st.markdown('<label class="form-label" style="font-size: 13px; margin-bottom: 4px; font-weight: 600;">📂 Load Saved Dashboard Version</label>', unsafe_allow_html=True)
            selected_ver_str = st.selectbox(
                label="Saved Dashboard Versions",
                options=version_options,
                index=0,
                label_visibility="collapsed",
                key="dashboard_version_select"
            )

        with col_ver_btn:
            st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
            if st.button("⚙️  Manage Versions", use_container_width=True, key="btn_manage_versions"):
                show_manage_versions_modal()

        # Handle version selection
        if selected_ver_str != "-- Custom Prompt / Select a Saved Version --":
            ver_id = int(selected_ver_str.split(":")[0].replace("v", ""))
            ver_record = get_dashboard_version_by_id(ver_id)
            if ver_record:
                if st.session_state.get("last_loaded_version_id") != ver_id:
                    st.session_state.cached_dashboard_data = generate_saved_version_dashboard(ver_record)
                    st.session_state.active_prompt = ver_record["prompt"]
                    st.session_state.last_loaded_version_id = ver_id
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # --- 2. Prompt Input & Action Buttons ---
        col_prompt, col_gen = st.columns([8.2, 2.8])

        with col_prompt:
            st.markdown('<label class="form-label" style="font-size: 13px; margin-bottom: 4px; font-weight: 600;">✨ Natural Language Query / Analytics Prompt</label>', unsafe_allow_html=True)
            user_prompt = st.text_input(
                label="Dashboard Prompt",
                value=st.session_state.get("active_prompt", default_prompt),
                placeholder="Describe the quality analytics, defect metrics, or machine comparisons you want...",
                label_visibility="collapsed",
                key="dashboard_prompt_input"
            )

        with col_gen:
            st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
            if st.button("✨  Generate Dashboard", type="primary", use_container_width=True, key="btn_generate_dashboard"):
                with st.spinner("Analyzing quality datasets and generating intelligence dashboard with Gemini AI..."):
                    dashboard_data = generate_quality_analytics_dashboard(user_prompt)
                    st.session_state.cached_dashboard_data = dashboard_data
                    st.session_state.active_prompt = user_prompt
                    st.session_state.last_loaded_version_id = None
                st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # If no dashboard has been generated yet, show readiness placeholder
    if "cached_dashboard_data" not in st.session_state or st.session_state.cached_dashboard_data is None:
        st.markdown("""
        <div class="qualiq-card" style="padding: 36px 24px; text-align: center; background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 12px; margin-top: 10px;">
            <div style="font-size: 38px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Ready to Generate or Load Quality Analytics Dashboard</div>
            <div style="font-size: 14px; color: #64748B; max-width: 580px; margin: 0 auto 18px auto; line-height: 1.5;">
                Select a <b>Saved Version</b> from the dropdown above to load an instant snapshot, or click <b>✨ Generate Dashboard</b> to synthesize custom analytics across 18 production datasets using Gemini AI. Once generated, you can export the official <b>Executive PDF Report</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Use Cached Dashboard Data (Zero redundant API calls!)
    dashboard_data = st.session_state.cached_dashboard_data
    kpis = dashboard_data["kpis"]
    charts = dashboard_data["charts"]
    ai_narrative = dashboard_data["ai_narrative"]

    # --- 3. Prominent Executive Actions Toolbar (Save + Export PDF) ---
    with st.container(border=True):
        col_hdr_title, col_btn_save, col_btn_pdf = st.columns([6.2, 2.3, 2.5])
        with col_hdr_title:
            st.markdown('<div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-top: 6px;">📊 Active Quality Dashboard Snapshot</div>', unsafe_allow_html=True)
        
        with col_btn_save:
            if st.button("💾  Save as Version", use_container_width=True, key="btn_open_save_version_modal"):
                show_save_version_modal(st.session_state.get("active_prompt", default_prompt), dashboard_data)

        with col_btn_pdf:
            report_date_str = datetime.now().strftime("%Y-%m-%d")
            pdf_filename = f"QualIQ_Executive_Quality_Report_{report_date_str}.pdf"
            
            pdf_data = generate_quality_report_pdf(
                prompt=st.session_state.get("active_prompt", default_prompt),
                kpis=kpis,
                ai_narrative=ai_narrative,
                author="Alexander Wright (Quality Director)",
                report_title="Plant-Wide Quality & Cpk Overview"
            )
            
            st.download_button(
                label="📥  Download PDF Report",
                data=pdf_data,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                key="btn_download_dashboard_pdf"
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- 4. Executive KPI Cards ---
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        st.markdown(f"""<div class="qualiq-card" style="padding: 18px 20px; margin-bottom: 20px;">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Total Inspected</div>
<div style="font-size: 26px; font-weight: 800; color: #0F172A; margin-top: 4px;">{kpis['total_inspected']}</div>
<div style="font-size: 12px; color: #10B981; font-weight: 600; margin-top: 4px;">● Across 18 Datasets</div>
</div>""", unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""<div class="qualiq-card" style="padding: 18px 20px; margin-bottom: 20px;">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">First-Pass Yield</div>
<div style="font-size: 26px; font-weight: 800; color: #15803D; margin-top: 4px;">{kpis['first_pass_yield']}</div>
<div style="font-size: 12px; color: #10B981; font-weight: 600; margin-top: 4px;">▲ +0.4% vs benchmark</div>
</div>""", unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""<div class="qualiq-card" style="padding: 18px 20px; margin-bottom: 20px;">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Defect Rate</div>
<div style="font-size: 26px; font-weight: 800; color: #B91C1C; margin-top: 4px;">{kpis['defect_rate']}</div>
<div style="font-size: 12px; color: #DC2626; font-weight: 600; margin-top: 4px;">● Non-conformance index</div>
</div>""", unsafe_allow_html=True)

    with col_kpi4:
        st.markdown(f"""<div class="qualiq-card" style="padding: 18px 20px; margin-bottom: 20px;">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Capability (Cpk)</div>
<div style="font-size: 26px; font-weight: 800; color: #2563EB; margin-top: 4px;">{kpis['cpk_index']}</div>
<div style="font-size: 12px; color: #2563EB; font-weight: 600; margin-top: 4px;">● Stable Process Window</div>
</div>""", unsafe_allow_html=True)

    # --- 5. Charts Grid (2x2) with Chart-Level AI Insight Popovers ---
    col_c1, col_c2 = st.columns(2)

    # Chart 1: Defect Breakdown
    with col_c1:
        with st.container(border=True):
            head_col1, head_col2 = st.columns([7.2, 2.8])
            with head_col1:
                st.markdown('<div style="font-size: 15px; font-weight: 700; color: #1E293B;">Defect Breakdown (Pareto Analysis)</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Non-conformance frequency by failure mode</div>', unsafe_allow_html=True)
            with head_col2:
                with st.popover("💡 AI Insight", use_container_width=True):
                    render_chart_insight_content("defect_breakdown", "Defect Breakdown Pareto Analysis", {"top_defect": "Dimensional Drift (38.9%)", "second_defect": "Surface Porosity (26.3%)"})
            
            st.plotly_chart(charts["defect_breakdown"], use_container_width=True, key="plotly_pareto")

    # Chart 2: Machine Comparison
    with col_c2:
        with st.container(border=True):
            head_col1, head_col2 = st.columns([7.2, 2.8])
            with head_col1:
                st.markdown('<div style="font-size: 15px; font-weight: 700; color: #1E293B;">Machine Defect Rate Comparison</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Station-wise variance vs 3.5% threshold</div>', unsafe_allow_html=True)
            with head_col2:
                with st.popover("💡 AI Insight", use_container_width=True):
                    render_chart_insight_content("machine_comparison", "Machine Defect Rate Comparison", {"outlier": "Milling Station CNC-04 (7.8%)", "benchmark_avg": "2.4%"})
            
            st.plotly_chart(charts["machine_comparison"], use_container_width=True, key="plotly_machine")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    col_c3, col_c4 = st.columns(2)

    # Chart 3: Temporal Trend
    with col_c3:
        with st.container(border=True):
            head_col1, head_col2 = st.columns([7.2, 2.8])
            with head_col1:
                st.markdown('<div style="font-size: 15px; font-weight: 700; color: #1E293B;">Shift Defect Rate Trend (14 Days)</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Shift A (Morning), Shift B (Evening), Shift C (Night)</div>', unsafe_allow_html=True)
            with head_col2:
                with st.popover("💡 AI Insight", use_container_width=True):
                    render_chart_insight_content("defect_trend", "Shift Defect Rate Trend (14 Days)", {"peak_shift": "Shift C (Night Shift)", "peak_rate": "6.4%"})
            
            st.plotly_chart(charts["defect_trend"], use_container_width=True, key="plotly_trend")

    # Chart 4: Tolerance Distribution
    with col_c4:
        with st.container(border=True):
            head_col1, head_col2 = st.columns([7.2, 2.8])
            with head_col1:
                st.markdown('<div style="font-size: 15px; font-weight: 700; color: #1E293B;">Tolerance Deviation Distribution & Cpk</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Measurement histogram vs USL/LSL limits (±0.025 mm)</div>', unsafe_allow_html=True)
            with head_col2:
                with st.popover("💡 AI Insight", use_container_width=True):
                    render_chart_insight_content("tolerance_distribution", "Tolerance Deviation Distribution & Cpk", {"mean_skew": "+0.008 mm", "usl": "+0.025 mm", "cpk": "1.28"})
            
            st.plotly_chart(charts["tolerance_distribution"], use_container_width=True, key="plotly_tolerance")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --- 6. Executive AI Intelligence Narrative ---
    with st.container(border=True):
        st.markdown('<div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;">🤖 Executive Quality Intelligence Narrative</div>', unsafe_allow_html=True)
        st.markdown(ai_narrative, unsafe_allow_html=False)

def render_chart_insight_content(chart_id: str, chart_title: str, metrics: dict):
    """Renders structured AI insight popover content for a specific chart."""
    insight = generate_chart_action_insight(chart_id, chart_title, metrics)

    if insight.get("formatted"):
        st.markdown(insight["raw_text"])
    else:
        st.markdown(f"""
        <div style="min-width: 290px; padding: 2px 0;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">🔍 Key Observation</div>
            <div style="font-size: 12.5px; color: #334155; line-height: 1.45; margin-bottom: 12px;">{insight['observation']}</div>

            <div style="font-size: 13px; font-weight: 700; color: #D97706; margin-bottom: 6px;">⚠️ Root Cause Hypothesis</div>
            <div style="font-size: 12.5px; color: #334155; line-height: 1.45; margin-bottom: 12px;">{insight['hypothesis']}</div>

            <div style="font-size: 13px; font-weight: 700; color: #2563EB; margin-bottom: 6px;">🎯 Recommended Action Plan</div>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #334155; line-height: 1.45;">
                {''.join([f'<li style="margin-bottom: 4px;">{act}</li>' for act in insight['actions']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
