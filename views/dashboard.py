import streamlit as st
from datetime import datetime, date, timedelta
from components.header import render_top_header
from ai.dashboard_generator import (
    generate_quality_analytics_dashboard,
    generate_saved_version_dashboard,
    PROMPT_PRESETS
)
from ai.chart_insights import generate_chart_action_insight
from utils.pdf_generator import generate_quality_report_pdf
from db.repository import (
    get_all_products,
    get_processes_by_product,
    get_checkpoints_by_process,
    get_all_datasets,
    get_datasets_by_criteria,
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
    QUALITY ANALYTICS DASHBOARD
    - Dual-Mode Data Source Selection (Single Excel OR Cascading Filter + Date Range)
    - Prompt Preset Library with specialized chart definitions
    - AI-Powered Quality Intelligence & Executive PDF Export
    """
    render_top_header("Quality Analytics Dashboard")

    st.markdown("""<div style="font-size: 14.5px; color: #64748B; margin-top: -12px; margin-bottom: 18px;">
AI-enhanced manufacturing quality analytics, root cause investigation, dynamic dashboard generation, and executive PDF reporting.
</div>""", unsafe_allow_html=True)

    default_prompt = "Generate a quality analytics dashboard suitable to the uploaded data"

    # =========================================================================
    # SECTION 1: DUAL-MODE DATA SOURCE SELECTION (OR LOGIC)
    # =========================================================================
    with st.container(border=True):
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-size: 15px; font-weight: 700; color: #0F172A;">📊 Step 1: Select Inspection Data Source</div>
            <span style="font-size: 12px; background: #F1F5F9; color: #475569; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Choose Option A OR Option B</span>
        </div>
        """, unsafe_allow_html=True)

        data_mode = st.radio(
            label="Data Source Mode",
            options=["📄 Option A: Choose Specific Excel Dataset", "🔍 Option B: Multi-Criteria Filter & Date Range Aggregation"],
            index=0,
            horizontal=True,
            key="dash_data_mode_select"
        )

        st.markdown("<hr style='margin: 10px 0 14px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        # All available datasets for Single Mode
        all_datasets = get_all_datasets()
        selected_matched_datasets = []
        filter_context = {}

        if "Option A" in data_mode:
            # OPTION A: Single Excel Sheet Selection
            if not all_datasets:
                st.warning("No datasets found in Data Warehouse. Please upload an inspection file in Data Entry.")
                ds_options = ["No datasets available"]
            else:
                ds_options = [
                    f"{d['file_name']} ({d['product_name']} • {d['checkpoint_name']} • {format_date_str(d['created_at'])})"
                    for d in all_datasets
                ]

            col_single_ds, col_single_info = st.columns([7, 3])
            with col_single_ds:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Select Excel Dataset to Analyze</label>', unsafe_allow_html=True)
                chosen_ds_str = st.selectbox(
                    label="Select Excel Dataset",
                    options=ds_options,
                    index=0,
                    label_visibility="collapsed",
                    key="dash_single_excel_select"
                )

            # Match dataset object
            if all_datasets and chosen_ds_str != "No datasets available":
                chosen_idx = ds_options.index(chosen_ds_str)
                target_ds = all_datasets[chosen_idx]
                selected_matched_datasets = [target_ds]
                filter_context = {
                    "mode": "single_excel",
                    "file_name": target_ds["file_name"],
                    "product": target_ds["product_name"],
                    "process": target_ds["process_name"],
                    "checkpoint": target_ds["checkpoint_name"],
                    "date_range_str": format_date_str(target_ds["created_at"])
                }
                with col_single_info:
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 12px; border-radius: 6px; font-size: 12px; color: #334155; margin-top: 20px;">
                        <b>Uploader:</b> {target_ds['uploaded_by_name']}<br>
                        <b>Status:</b> <span style="color: #16A34A; font-weight: 600;">● {target_ds['status']}</span>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            # OPTION B: Cascading Multi-Criteria + Date Range Aggregation
            col_p, col_pr, col_cp = st.columns(3)

            # 1. Product Filter
            products = get_all_products()
            prod_options = ["All Products"] + [p["name"] for p in products]
            with col_p:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Product</label>', unsafe_allow_html=True)
                sel_product = st.selectbox("Product", options=prod_options, index=0, label_visibility="collapsed", key="dash_filter_product")

            # 2. Cascading Process Filter
            if sel_product == "All Products":
                proc_records = get_processes_by_product("All Products")
            else:
                proc_records = get_processes_by_product(sel_product)
            proc_options = ["All Processes"] + [pr["process_name"] for pr in proc_records]
            with col_pr:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Process (Cascaded)</label>', unsafe_allow_html=True)
                sel_process = st.selectbox("Process", options=proc_options, index=0, label_visibility="collapsed", key="dash_filter_process")

            # 3. Cascading Checkpoint Filter
            if sel_process == "All Processes":
                cp_records = get_checkpoints_by_process("All Processes")
            else:
                cp_records = get_checkpoints_by_process(sel_process)
            cp_options = ["All Checkpoints"] + [c["checkpoint_name"] for c in cp_records]
            with col_cp:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Checkpoint (Cascaded)</label>', unsafe_allow_html=True)
                sel_checkpoint = st.selectbox("Checkpoint", options=cp_options, index=0, label_visibility="collapsed", key="dash_filter_checkpoint")

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

            # 4. Date Range Filter
            col_start, col_end, col_badge = st.columns([3, 3, 4])
            default_start = date(2026, 8, 1)
            default_end = date(2026, 8, 31)

            with col_start:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Start Date (Upload / Record)</label>', unsafe_allow_html=True)
                start_d = st.date_input("Start Date", value=default_start, label_visibility="collapsed", key="dash_start_date")

            with col_end:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">End Date</label>', unsafe_allow_html=True)
                end_d = st.date_input("End Date", value=default_end, label_visibility="collapsed", key="dash_end_date")

            # Fetch matching datasets
            selected_matched_datasets = get_datasets_by_criteria(
                product=sel_product,
                process=sel_process,
                checkpoint=sel_checkpoint,
                start_date=start_d,
                end_date=end_d
            )

            filter_context = {
                "mode": "multi_filter",
                "product": sel_product,
                "process": sel_process,
                "checkpoint": sel_checkpoint,
                "start_date": str(start_d),
                "end_date": str(end_d),
                "date_range_str": f"{start_d} to {end_d}",
                "dataset_count": len(selected_matched_datasets)
            }

            with col_badge:
                match_count = len(selected_matched_datasets)
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                if match_count > 0:
                    st.markdown(f"""
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; padding: 8px 12px; border-radius: 6px; font-size: 12.5px; font-weight: 600; text-align: center;">
                        🎯 Matched <b>{match_count}</b> dataset(s) for aggregate synthesis
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #FEF2F2; border: 1px solid #FECACA; color: #B91C1C; padding: 8px 12px; border-radius: 6px; font-size: 12.5px; font-weight: 600; text-align: center;">
                        ⚠️ 0 datasets matched current filter criteria
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: 3-WAY ANALYSIS QUERY SELECTION (OR LOGIC)
    # =========================================================================
    with st.container(border=True):
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-size: 15px; font-weight: 700; color: #0F172A;">✨ Step 2: Choose Analysis Definition (OR Selection)</div>
            <span style="font-size: 12px; background: #F1F5F9; color: #475569; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Choose 1 of 3 Modes</span>
        </div>
        """, unsafe_allow_html=True)

        query_mode = st.radio(
            label="Analysis Query Mode",
            options=[
                "⭐ Standard Analysis Preset",
                "✍️ Custom Analytics Prompt",
                "📂 Saved Dashboard Version"
            ],
            index=0,
            horizontal=True,
            key="dash_query_mode_select"
        )

        st.markdown("<hr style='margin: 10px 0 14px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if "Standard Analysis Preset" in query_mode:
            # MODE 1: Standard Analysis Preset
            col_preset_sel, col_preset_btn = st.columns([7.8, 2.2])
            preset_labels = [p["title"] for p in PROMPT_PRESETS]
            with col_preset_sel:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Choose Standard Analysis Preset</label>', unsafe_allow_html=True)
                sel_preset_title = st.selectbox(
                    label="Standard Analysis Preset",
                    options=preset_labels,
                    index=0,
                    label_visibility="collapsed",
                    key="dash_preset_select_radio"
                )
            
            # Find chosen preset
            chosen_preset = next((p for p in PROMPT_PRESETS if p["title"] == sel_preset_title), PROMPT_PRESETS[0])
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 14px; border-radius: 6px; font-size: 12.5px; color: #475569; margin: 6px 0 10px 0;">
                <b>Description:</b> {chosen_preset['description']}<br>
                <b>Embedded Prompt:</b> <span style="font-style: italic; color: #1E293B;">"{chosen_preset['prompt']}"</span>
            </div>
            """, unsafe_allow_html=True)

            with col_preset_btn:
                st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
                if st.button("✨ Generate Dashboard", type="primary", use_container_width=True, key="btn_gen_preset"):
                    with st.spinner(f"Synthesizing {chosen_preset['title']} with Gemini AI..."):
                        dashboard_data = generate_quality_analytics_dashboard(
                            user_prompt=chosen_preset["prompt"],
                            selected_datasets=selected_matched_datasets,
                            filter_context=filter_context
                        )
                        st.session_state.cached_dashboard_data = dashboard_data
                        st.session_state.active_prompt = chosen_preset["prompt"]
                        st.session_state.last_loaded_version_id = None
                    st.rerun()

        elif "Custom Analytics Prompt" in query_mode:
            # MODE 2: Custom Analytics Prompt
            col_custom_input, col_custom_btn = st.columns([7.8, 2.2])
            with col_custom_input:
                st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Type Natural Language Analytics Query</label>', unsafe_allow_html=True)
                custom_prompt = st.text_input(
                    label="Custom Analytics Prompt",
                    value=st.session_state.get("active_prompt", default_prompt),
                    placeholder="e.g. Compare night shift defect variance and machine spindle drift...",
                    label_visibility="collapsed",
                    key="dash_custom_prompt_input"
                )

            with col_custom_btn:
                st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
                if st.button("✨ Generate Dashboard", type="primary", use_container_width=True, key="btn_gen_custom"):
                    if custom_prompt.strip():
                        with st.spinner("Analyzing quality datasets and generating intelligence dashboard with Gemini AI..."):
                            dashboard_data = generate_quality_analytics_dashboard(
                                user_prompt=custom_prompt.strip(),
                                selected_datasets=selected_matched_datasets,
                                filter_context=filter_context
                            )
                            st.session_state.cached_dashboard_data = dashboard_data
                            st.session_state.active_prompt = custom_prompt.strip()
                            st.session_state.last_loaded_version_id = None
                        st.rerun()
                    else:
                        st.warning("Please type a custom prompt.")

        else:
            # MODE 3: Saved Dashboard Version
            saved_versions = get_all_dashboard_versions()
            if not saved_versions:
                st.info("No saved dashboard versions found. Save your current analysis as a version using the '💾 Save as Version' button below.")
            else:
                ver_options = [
                    f"v{v['id']}: {v['name']} ({format_date_str(v.get('created_at'))}) — By {v.get('created_by', 'Admin')}"
                    for v in saved_versions
                ]
                col_ver_sel, col_ver_btn = st.columns([7.8, 2.2])
                with col_ver_sel:
                    st.markdown('<label class="form-label" style="font-size: 13px; font-weight: 600;">Select Saved Dashboard Version</label>', unsafe_allow_html=True)
                    sel_ver_str = st.selectbox(
                        label="Saved Version",
                        options=ver_options,
                        index=0,
                        label_visibility="collapsed",
                        key="dash_saved_version_radio"
                    )

                with col_ver_btn:
                    st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
                    if st.button("📂 Load Version", type="primary", use_container_width=True, key="btn_load_saved_ver"):
                        ver_id = int(sel_ver_str.split(":")[0].replace("v", ""))
                        ver_record = get_dashboard_version_by_id(ver_id)
                        if ver_record:
                            st.session_state.cached_dashboard_data = generate_saved_version_dashboard(ver_record)
                            st.session_state.active_prompt = ver_record["prompt"]
                            st.session_state.last_loaded_version_id = ver_id
                            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # If no dashboard has been generated yet, show readiness placeholder
    if "cached_dashboard_data" not in st.session_state or st.session_state.cached_dashboard_data is None:
        st.markdown("""
        <div class="qualiq-card" style="padding: 36px 24px; text-align: center; background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 12px; margin-top: 10px;">
            <div style="font-size: 38px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Ready to Generate Quality Analytics Dashboard</div>
            <div style="font-size: 14px; color: #64748B; max-width: 620px; margin: 0 auto 18px auto; line-height: 1.5;">
                Select your <b>Data Source</b> (Single Excel or Multi-Criteria Filter), pick an <b>Analysis Preset</b>, and click <b>✨ Generate Dashboard</b> to synthesize custom quality intelligence across your inspection datasets.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Use Cached Dashboard Data
    dashboard_data = st.session_state.cached_dashboard_data
    kpis = dashboard_data["kpis"]
    charts = dashboard_data["charts"]
    ai_narrative = dashboard_data["ai_narrative"]
    scope_desc = dashboard_data.get("scope_desc", "Active Dataset Selection")

    # =========================================================================
    # SECTION 3: ACTIONS TOOLBAR (SAVE VERSION + EXPORT PDF)
    # =========================================================================
    with st.container(border=True):
        col_hdr_title, col_btn_save, col_btn_pdf = st.columns([5.8, 2.2, 2.8])
        with col_hdr_title:
            st.markdown(f"""
            <div>
                <div style="font-size: 15px; font-weight: 700; color: #0F172A;">📊 Active Dashboard: {scope_desc}</div>
                <div style="font-size: 12px; color: #64748B;">Generated via Gemini 2.5 Flash • Multi-variable statistical correlation</div>
            </div>
            """, unsafe_allow_html=True)
        
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
                report_title=f"Quality Intelligence Report ({scope_desc})"
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

    # =========================================================================
    # SECTION 4: 4-KPI METRIC CARDS
    # =========================================================================
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        st.markdown(f"""<div class="qualiq-card" style="padding: 18px 20px; margin-bottom: 20px;">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Total Inspected</div>
<div style="font-size: 26px; font-weight: 800; color: #0F172A; margin-top: 4px;">{kpis['total_inspected']}</div>
<div style="font-size: 12px; color: #10B981; font-weight: 600; margin-top: 4px;">● {scope_desc}</div>
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

    # =========================================================================
    # SECTION 5: 2x2 PLOTLY GRAPHS GRID
    # =========================================================================
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        with st.container(border=True):
            ch1_title, ch1_btn = st.columns([8, 2])
            ch1_title.markdown("**Defect Pareto (80/20 Distribution)**")
            with ch1_btn:
                with st.popover("💡 Insight", use_container_width=True):
                    st.markdown(generate_chart_action_insight("pareto", kpis))
            st.plotly_chart(charts["pareto"], use_container_width=True, key="plotly_pareto")

    with col_c2:
        with st.container(border=True):
            ch2_title, ch2_btn = st.columns([8, 2])
            ch2_title.markdown("**Machine Defect Rate vs Upper Control Limit**")
            with ch2_btn:
                with st.popover("💡 Insight", use_container_width=True):
                    st.markdown(generate_chart_action_insight("machine", kpis))
            st.plotly_chart(charts["machine"], use_container_width=True, key="plotly_machine")

    col_c3, col_c4 = st.columns(2)

    with col_c3:
        with st.container(border=True):
            ch3_title, ch3_btn = st.columns([8, 2])
            ch3_title.markdown("**14-Day Shift Quality Trend Comparison**")
            with ch3_btn:
                with st.popover("💡 Insight", use_container_width=True):
                    st.markdown(generate_chart_action_insight("trend", kpis))
            st.plotly_chart(charts["trend"], use_container_width=True, key="plotly_trend")

    with col_c4:
        with st.container(border=True):
            ch4_title, ch4_btn = st.columns([8, 2])
            ch4_title.markdown("**Dimensional Tolerance Distribution (Cpk)**")
            with ch4_btn:
                with st.popover("💡 Insight", use_container_width=True):
                    st.markdown(generate_chart_action_insight("distribution", kpis))
            st.plotly_chart(charts["distribution"], use_container_width=True, key="plotly_distribution")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 6: AI QUALITY INTELLIGENCE NARRATIVE
    # =========================================================================
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 20px;">🤖</span>
            <span style="font-size: 16px; font-weight: 700; color: #0F172A;">Gemini Executive Quality Intelligence Narrative</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(ai_narrative)
