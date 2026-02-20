"""
🩸 Hematology & Clinical Laboratory Analysis Tool
Comprehensive blood investigation analysis with AI-powered review.
Supports CBC, LFT, and multi-panel analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import io
import os
from typing import Dict, List, Optional

# Import utility modules
from utils.ocr_parser import process_uploaded_file, PARAMETER_PATTERNS
from utils.analysis_engine import (
    analyze_all_parameters, classify_value, get_reference_range,
    check_sample_quality, generate_summary_text, REFERENCE_RANGES,
    get_differential_diagnosis, calculate_additional_indices
)
from utils.lft_engine import (
    LFT_REFERENCE_RANGES, analyze_lft, calculate_r_value,
    determine_lft_pattern, determine_severity, generate_lft_recommendations,
    generate_lft_educational_content, get_lft_differential_diagnosis
)
from utils.ai_review import get_ai_review, get_parameter_specific_ai_review
from utils.pdf_generator import generate_pdf_report

# ── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="🩸 Blood Investigation Analysis Tool",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        margin-bottom: 20px;
        text-align: center;
    }
    .main-header h1 { font-size: 2.2em; margin-bottom: 5px; }
    .main-header p { opacity: 0.9; font-size: 1.1em; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        margin-bottom: 10px;
    }
    .critical-alert {
        background: #fee;
        border: 2px solid #e74c3c;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .normal-badge {
        background: #d4edda; color: #155724;
        padding: 4px 12px; border-radius: 20px;
        font-weight: bold; font-size: 0.85em;
    }
    .abnormal-badge {
        background: #fff3cd; color: #856404;
        padding: 4px 12px; border-radius: 20px;
        font-weight: bold; font-size: 0.85em;
    }
    .critical-badge {
        background: #f8d7da; color: #721c24;
        padding: 4px 12px; border-radius: 20px;
        font-weight: bold; font-size: 0.85em;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .diagnosis-card {
        background: #f8f9fa;
        border-left: 4px solid #4ecdc4;
        padding: 15px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .quality-pass { border-left-color: #27ae60; }
    .quality-warning { border-left-color: #f39c12; }
    .quality-error { border-left-color: #e74c3c; }
    .quality-info { border-left-color: #3498db; }
    .lft-pattern-hepatocellular { background: #ffe0e0; border-color: #e74c3c; }
    .lft-pattern-cholestatic { background: #e0f7fa; border-color: #00bcd4; }
    .lft-pattern-mixed { background: #fff8e1; border-color: #ffc107; }
    .lft-pattern-isolated { background: #f3e5f5; border-color: #9c27b0; }
    .step-box {
        background: white;
        padding: 18px;
        margin: 10px 0;
        border-radius: 10px;
        border-left: 4px solid #4ecdc4;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ────────────────────────────────────
if 'parameters' not in st.session_state:
    st.session_state.parameters = {}
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'ai_review_text' not in st.session_state:
    st.session_state.ai_review_text = None
if 'lft_parameters' not in st.session_state:
    st.session_state.lft_parameters = {}
if 'lft_clinical' not in st.session_state:
    st.session_state.lft_clinical = {}
if 'lft_analysis_results' not in st.session_state:
    st.session_state.lft_analysis_results = None
if 'active_panel' not in st.session_state:
    st.session_state.active_panel = 'CBC'

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/blood-sample.png", width=80)
    st.title("⚕️ Settings")

    api_key = st.text_input(
        "Claude API Key",
        type="password",
        help="Enter your Anthropic API key for AI-powered analysis",
        value=os.environ.get("ANTHROPIC_API_KEY", "")
    )

    st.divider()

    st.subheader("🔬 Analysis Panel")
    panel_choice = st.radio(
        "Select Analysis Panel",
        ["CBC (Complete Blood Count)", "LFT (Liver Function Tests)", "Combined Panel"],
        index=0
    )
    if "CBC" in panel_choice:
        st.session_state.active_panel = 'CBC'
    elif "LFT" in panel_choice:
        st.session_state.active_panel = 'LFT'
    else:
        st.session_state.active_panel = 'Combined'

    st.divider()

    sex = st.selectbox("Patient Sex (for reference ranges)", ["Default", "Male", "Female"])
    st.session_state.patient_info['sex'] = sex

    st.divider()
    st.markdown("### 📖 About")
    st.info(
        "This tool analyzes blood investigation reports using OCR extraction and "
        "AI-powered clinical interpretation. Upload reports or enter values manually."
    )
    st.warning(
        "⚠️ **Disclaimer:** For educational purposes only. "
        "Not for clinical decision-making. Always consult qualified professionals."
    )

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🩸 Blood Investigation Analysis Tool</h1>
    <p>AI-Powered Hematology & Clinical Pathology Analysis Platform</p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════

def render_status_badge(status: str) -> str:
    """Return HTML badge for a parameter status."""
    if 'critical' in status:
        return '<span class="critical-badge">⚠️ CRITICAL</span>'
    elif status in ('low', 'high'):
        return '<span class="abnormal-badge">⬆ ABNORMAL</span>' if status == 'high' else '<span class="abnormal-badge">⬇ ABNORMAL</span>'
    elif status == 'normal':
        return '<span class="normal-badge">✅ NORMAL</span>'
    return ''


def create_gauge_chart(value: float, low: float, high: float, title: str, unit: str) -> go.Figure:
    """Create a gauge chart for a parameter."""
    range_span = high - low
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': f"{title} ({unit})", 'font': {'size': 14}},
        number={'font': {'size': 20}},
        gauge={
            'axis': {'range': [low - range_span, high + range_span], 'tickwidth': 1},
            'bar': {'color': "#667eea"},
            'bgcolor': "white",
            'steps': [
                {'range': [low - range_span, low], 'color': '#fee'},
                {'range': [low, high], 'color': '#d4edda'},
                {'range': [high, high + range_span], 'color': '#fff3cd'},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_parameter_bar_chart(analysis: Dict) -> go.Figure:
    """Create a horizontal bar chart showing all parameters relative to normal range."""
    params_data = analysis.get('parameters', {})
    names, deviations, colors = [], [], []

    for name, data in params_data.items():
        classification = data.get('classification', {})
        ref_low = classification.get('low')
        ref_high = classification.get('high')
        val = data.get('value')
        if ref_low is None or ref_high is None or val is None:
            continue
        mid = (ref_low + ref_high) / 2
        ref_range = ref_high - ref_low
        if ref_range == 0:
            continue
        deviation = ((val - mid) / (ref_range / 2)) * 100
        status = classification.get('status', 'normal')
        color = '#e74c3c' if 'critical' in status else '#f39c12' if status in ('low', 'high') else '#27ae60'
        names.append(name)
        deviations.append(deviation)
        colors.append(color)

    fig = go.Figure(go.Bar(
        x=deviations, y=names, orientation='h',
        marker_color=colors,
        text=[f"{d:+.0f}%" for d in deviations],
        textposition='outside'
    ))
    fig.add_vrect(x0=-100, x1=100, fillcolor="green", opacity=0.05, line_width=0)
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Parameter Deviation from Normal Range",
        xaxis_title="% Deviation from midpoint of normal range",
        yaxis_title="", height=max(300, len(names) * 35),
        margin=dict(l=120, r=40, t=40, b=40)
    )
    return fig


# ════════════════════════════════════════════════════════════════════
#  CBC PANEL
# ════════════════════════════════════════════════════════════════════

def render_cbc_panel():
    """Render the CBC analysis panel."""

    tab_upload, tab_manual, tab_analysis, tab_lft_sub, tab_ai, tab_report = st.tabs([
        "📤 Upload Report", "✏️ Manual Entry", "📊 CBC Analysis",
        "🧬 LFT (if combined)", "🤖 AI Review", "📄 Report"
    ])

    # ── Tab 1: Upload ───────────────────────────────────────────────
    with tab_upload:
        st.subheader("📤 Upload Blood Investigation Report")
        st.write("Upload PDF or image files (JPG, JPEG, PNG) of blood reports.")

        uploaded_files = st.file_uploader(
            "Choose file(s)",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Upload one or more blood investigation reports"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        if uploaded_file.type in ['image/jpeg', 'image/jpg', 'image/png']:
                            from PIL import Image
                            image = Image.open(uploaded_file)
                            st.image(image, caption=uploaded_file.name, use_container_width=True)
                            uploaded_file.seek(0)

                    with col2:
                        with st.spinner("Extracting data..."):
                            text, params, info = process_uploaded_file(uploaded_file)

                        st.text_area("Extracted Text", text, height=200, key=f"text_{uploaded_file.name}")

                        if params:
                            st.success(f"✅ Extracted {len(params)} parameters")
                            for k, v in params.items():
                                st.session_state.parameters[k] = v
                        else:
                            st.warning("No parameters extracted. Try manual entry.")

                        if info:
                            for k, v in info.items():
                                st.session_state.patient_info[k] = v

                        st.session_state.extracted_text += text + "\n"

            if st.session_state.parameters:
                st.success(f"Total parameters loaded: {len(st.session_state.parameters)}")

    # ── Tab 2: Manual Entry ─────────────────────────────────────────
    with tab_manual:
        st.subheader("✏️ Manual Parameter Entry")
        st.write("Enter or edit blood investigation values manually.")

        # Patient info
        with st.expander("👤 Patient Information", expanded=False):
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                st.session_state.patient_info['name'] = st.text_input(
                    "Patient Name",
                    value=st.session_state.patient_info.get('name', '')
                )
            with pc2:
                st.session_state.patient_info['age'] = st.text_input(
                    "Age",
                    value=st.session_state.patient_info.get('age', '')
                )
            with pc3:
                st.session_state.patient_info['date'] = st.text_input(
                    "Report Date",
                    value=st.session_state.patient_info.get('date', '')
                )

        # RBC Parameters
        st.markdown("#### 🔴 Red Blood Cell Parameters")
        rbc_cols = st.columns(4)
        rbc_params = [
            ('RBC', 'x10¹²/L', 0.0, 10.0, 0.1),
            ('Hemoglobin', 'g/dL', 0.0, 25.0, 0.1),
            ('Hematocrit', '%', 0.0, 70.0, 0.1),
            ('MCV', 'fL', 0.0, 150.0, 0.1),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(rbc_params):
            with rbc_cols[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        rbc_cols2 = st.columns(4)
        rbc_params2 = [
            ('MCH', 'pg', 0.0, 50.0, 0.1),
            ('MCHC', 'g/dL', 0.0, 45.0, 0.1),
            ('RDW', '%', 0.0, 35.0, 0.1),
            ('Reticulocytes', '%', 0.0, 20.0, 0.1),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(rbc_params2):
            with rbc_cols2[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        # WBC Parameters
        st.markdown("#### ⚪ White Blood Cell Parameters")
        wbc_cols = st.columns(3)
        wbc_params = [
            ('WBC', 'x10⁹/L', 0.0, 100.0, 0.1),
            ('Neutrophils', '%', 0.0, 100.0, 0.1),
            ('Lymphocytes', '%', 0.0, 100.0, 0.1),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(wbc_params):
            with wbc_cols[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        wbc_cols2 = st.columns(3)
        wbc_params2 = [
            ('Monocytes', '%', 0.0, 30.0, 0.1),
            ('Eosinophils', '%', 0.0, 30.0, 0.1),
            ('Basophils', '%', 0.0, 10.0, 0.1),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(wbc_params2):
            with wbc_cols2[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        # Platelet Parameters
        st.markdown("#### 🟣 Platelet Parameters")
        plt_cols = st.columns(3)
        plt_params = [
            ('Platelets', 'x10⁹/L', 0.0, 1500.0, 1.0),
            ('MPV', 'fL', 0.0, 20.0, 0.1),
            ('PDW', 'fL', 0.0, 30.0, 0.1),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(plt_params):
            with plt_cols[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        # Additional
        st.markdown("#### 🔬 Additional Parameters")
        add_cols = st.columns(3)
        add_params = [
            ('ESR', 'mm/hr', 0.0, 150.0, 1.0),
            ('ANC', 'x10⁹/L', 0.0, 30.0, 0.01),
            ('ALC', 'x10⁹/L', 0.0, 20.0, 0.01),
        ]
        for i, (name, unit, mn, mx, step) in enumerate(add_params):
            with add_cols[i]:
                current = st.session_state.parameters.get(name, {}).get('value', 0.0)
                val = st.number_input(f"{name} ({unit})", min_value=mn, max_value=mx, value=float(current), step=step, key=f"man_{name}")
                if val > 0:
                    st.session_state.parameters[name] = {'value': val, 'unit': unit}

        # Delete parameters
        st.markdown("---")
        st.markdown("#### 🗑️ Remove Parameters")
        if st.session_state.parameters:
            params_to_delete = st.multiselect(
                "Select parameters to remove",
                options=list(st.session_state.parameters.keys())
            )
            if st.button("🗑️ Remove Selected") and params_to_delete:
                for p in params_to_delete:
                    del st.session_state.parameters[p]
                st.rerun()

        # Current parameters summary
        if st.session_state.parameters:
            st.markdown("---")
            st.markdown("#### 📋 Current Parameter Summary")
            df_data = []
            for name, data in st.session_state.parameters.items():
                ref = get_reference_range(name, sex)
                df_data.append({
                    'Parameter': name,
                    'Value': data.get('value', ''),
                    'Unit': data.get('unit', ''),
                    'Ref Low': ref.get('low', ''),
                    'Ref High': ref.get('high', ''),
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    # ── Tab 3: CBC Analysis ─────────────────────────────────────────
    with tab_analysis:
        st.subheader("📊 CBC Analysis Results")

        if not st.session_state.parameters:
            st.info("Please upload a report or enter values manually first.")
        else:
            if st.button("🔬 Run CBC Analysis", type="primary", key="run_cbc"):
                with st.spinner("Analyzing..."):
                    st.session_state.analysis_results = analyze_all_parameters(
                        st.session_state.parameters, sex
                    )

            if st.session_state.analysis_results:
                analysis = st.session_state.analysis_results

                # Summary cards
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    st.metric("Total Parameters", analysis['total_parameters'])
                with sc2:
                    st.metric("Abnormal", analysis['abnormal_count'],
                              delta=None if analysis['abnormal_count'] == 0 else f"{analysis['abnormal_count']} abnormal",
                              delta_color="inverse")
                with sc3:
                    st.metric("Critical Values", analysis['critical_count'],
                              delta=None if analysis['critical_count'] == 0 else "⚠️ ALERT",
                              delta_color="inverse")
                with sc4:
                    normal = analysis['total_parameters'] - analysis['abnormal_count']
                    st.metric("Normal", normal)

                # Critical values alert
                if analysis['critical_values']:
                    st.markdown('<div class="critical-alert">', unsafe_allow_html=True)
                    st.error("🚨 CRITICAL VALUES DETECTED - Immediate clinical attention required!")
                    for cv in analysis['critical_values']:
                        st.markdown(f"**{cv['parameter']}**: {cv['message']}")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Quality assessment
                with st.expander("🔍 Sample Quality Assessment", expanded=True):
                    for check in analysis['quality_checks']:
                        sev = check['severity']
                        css = f"quality-{sev}"
                        icon = {'pass': '✅', 'info': 'ℹ️', 'warning': '⚠️', 'error': '❌'}.get(sev, '❓')
                        st.markdown(
                            f'<div class="diagnosis-card {css}">'
                            f'<strong>{icon} {check["rule"]}</strong><br>'
                            f'Expected: {check["expected"]} | Actual: {check["actual"]}<br>'
                            f'<em>{check["interpretation"]}</em></div>',
                            unsafe_allow_html=True
                        )

                # Parameter deviation chart
                st.plotly_chart(create_parameter_bar_chart(analysis), use_container_width=True)

                # Detailed parameter analysis
                with st.expander("📋 Detailed Parameter Analysis", expanded=True):
                    for param_name, param_data in analysis['parameters'].items():
                        classification = param_data['classification']
                        status = classification.get('status', 'unknown')
                        badge = render_status_badge(status)

                        st.markdown(f"### {param_name} {badge}", unsafe_allow_html=True)

                        mc1, mc2 = st.columns([2, 3])
                        with mc1:
                            ref_low = classification.get('low')
                            ref_high = classification.get('high')
                            if ref_low is not None and ref_high is not None:
                                fig = create_gauge_chart(
                                    param_data['value'], ref_low, ref_high,
                                    param_name, param_data.get('unit', '')
                                )
                                st.plotly_chart(fig, use_container_width=True)

                        with mc2:
                            st.markdown(f"**Value:** {param_data['value']} {param_data.get('unit', '')}")
                            st.markdown(f"**Status:** {classification.get('message', '')}")

                            diff = param_data.get('differential')
                            if diff:
                                st.markdown(f"**{diff['title']}**")
                                for i, d in enumerate(diff.get('differentials', []), 1):
                                    st.markdown(
                                        f'<div class="diagnosis-card">'
                                        f'<strong>{i}. {d["condition"]}</strong><br>'
                                        f'{d["discussion"]}</div>',
                                        unsafe_allow_html=True
                                    )

                        st.divider()

                # Calculated indices
                if analysis.get('calculated_indices'):
                    with st.expander("🧮 Calculated Indices", expanded=False):
                        for idx_name, idx_data in analysis['calculated_indices'].items():
                            st.markdown(
                                f'<div class="diagnosis-card">'
                                f'<strong>{idx_name}: {idx_data["value"]}</strong><br>'
                                f'Formula: {idx_data["formula"]}<br>'
                                f'Interpretation: {idx_data["interpretation"]}<br>'
                                f'<em>{idx_data["note"]}</em></div>',
                                unsafe_allow_html=True
                            )

    # ── Tab 4: LFT sub-panel (for combined mode) ───────────────────
    with tab_lft_sub:
        if st.session_state.active_panel == 'Combined':
            render_lft_entry_and_analysis()
        else:
            st.info("Select **Combined Panel** in the sidebar to include LFT analysis here.")

    # ── Tab 5: AI Review ────────────────────────────────────────────
    with tab_ai:
        st.subheader("🤖 AI-Powered Clinical Review (Claude)")

        if not api_key:
            st.warning("Please enter your Claude API key in the sidebar to use AI review.")
        elif not st.session_state.analysis_results:
            st.info("Please run the analysis first before requesting AI review.")
        else:
            review_type = st.radio(
                "Review Type",
                ["Full CBC Review", "Single Parameter Review"],
                horizontal=True
            )

            if review_type == "Full CBC Review":
                if st.button("🧠 Generate AI Review", type="primary", key="ai_full"):
                    with st.spinner("Claude is analyzing your results…"):
                        review = get_ai_review(
                            st.session_state.parameters,
                            st.session_state.analysis_results,
                            st.session_state.patient_info,
                            api_key
                        )
                        st.session_state.ai_review_text = review

                if st.session_state.ai_review_text:
                    st.markdown("---")
                    st.markdown(st.session_state.ai_review_text)
            else:
                if st.session_state.parameters:
                    selected = st.selectbox("Select Parameter", list(st.session_state.parameters.keys()))
                    if st.button("🔍 Review Parameter", key="ai_single"):
                        param_data = st.session_state.parameters[selected]
                        classification = classify_value(selected, param_data['value'], sex)
                        with st.spinner(f"Analyzing {selected}…"):
                            review = get_parameter_specific_ai_review(
                                selected, param_data['value'],
                                param_data.get('unit', ''),
                                classification, api_key
                            )
                        st.markdown(review)

    # ── Tab 6: Report ───────────────────────────────────────────────
    with tab_report:
        st.subheader("📄 Download / Share Report")

        if not st.session_state.analysis_results:
            st.info("Run the analysis first to generate a report.")
        else:
            include_ai = st.checkbox("Include AI Review in PDF", value=bool(st.session_state.ai_review_text))

            if st.button("📥 Generate PDF Report", type="primary", key="gen_pdf"):
                with st.spinner("Generating PDF…"):
                    ai_text = st.session_state.ai_review_text if include_ai else None
                    pdf_bytes = generate_pdf_report(
                        st.session_state.analysis_results,
                        st.session_state.patient_info,
                        ai_text
                    )
                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"blood_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )

            st.markdown("---")
            st.markdown("#### 📝 Text Summary")
            summary = generate_summary_text(
                st.session_state.analysis_results,
                st.session_state.patient_info
            )
            st.text_area("Summary", summary, height=400)
            st.download_button(
                "⬇️ Download Text Summary",
                data=summary,
                file_name=f"blood_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


# ════════════════════════════════════════════════════════════════════
#  LFT PANEL
# ════════════════════════════════════════════════════════════════════

def render_lft_entry_and_analysis():
    """Shared LFT entry and analysis — used by both standalone and combined."""
    st.subheader("🏥 Liver Function Test (LFT) Analyzer")

    # Step 1: Demographics
    with st.expander("👤 Step 1: Patient Demographics", expanded=True):
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            lft_age = st.number_input("Age", 18, 120, value=int(st.session_state.patient_info.get('age', 40) or 40), key="lft_age")
        with dc2:
            lft_sex = st.selectbox("Sex", ["male", "female"],
                                   index=0 if st.session_state.patient_info.get('sex', 'Male') != 'Female' else 1,
                                   key="lft_sex")
        with dc3:
            lft_reason = st.selectbox("Reason for Testing", [
                "routine", "symptoms", "medication", "known_disease", "incidental"
            ], key="lft_reason")

    # Step 2: Clinical Assessment
    with st.expander("🔍 Step 2: Clinical Assessment", expanded=True):
        cc1, cc2 = st.columns(2)
        with cc1:
            shock = st.radio("Shock / hemodynamic instability?", ["no", "yes"], horizontal=True, key="lft_shock")
            biliary = st.radio("Fever, chills, RUQ pain, prior biliary surgery?", ["no", "yes"], horizontal=True, key="lft_biliary")
        with cc2:
            acute_injury = st.radio("Severe acute liver injury (jaundice + AMS/coagulopathy)?", ["no", "yes"], horizontal=True, key="lft_acute")
            hemolysis = st.radio("Suspected hemolytic anemia?", ["no", "yes"], horizontal=True, key="lft_hemolysis")

    st.session_state.lft_clinical = {
        'age': lft_age, 'sex': lft_sex, 'reason': lft_reason,
        'shock': shock, 'biliary': biliary,
        'acute_injury': acute_injury, 'hemolysis': hemolysis
    }

    # Step 3: Lab Values
    with st.expander("🧪 Step 3: Laboratory Values", expanded=True):
        st.markdown("##### Liver Biochemical Tests")
        lb1, lb2, lb3 = st.columns(3)
        with lb1:
            alt = st.number_input("ALT (IU/L)", 0.0, 10000.0, value=st.session_state.lft_parameters.get('alt', 0.0), step=0.1, key="lft_alt")
            ast = st.number_input("AST (IU/L)", 0.0, 10000.0, value=st.session_state.lft_parameters.get('ast', 0.0), step=0.1, key="lft_ast")
        with lb2:
            alp = st.number_input("Alkaline Phosphatase (IU/L)", 0.0, 5000.0, value=st.session_state.lft_parameters.get('alp', 0.0), step=0.1, key="lft_alp")
            total_bili = st.number_input("Total Bilirubin (mg/dL)", 0.0, 50.0, value=st.session_state.lft_parameters.get('total_bili', 0.0), step=0.1, key="lft_tbili")
        with lb3:
            direct_bili = st.number_input("Direct Bilirubin (mg/dL)", 0.0, 30.0, value=st.session_state.lft_parameters.get('direct_bili', 0.0), step=0.1, key="lft_dbili")

        st.markdown("##### Liver Function Tests")
        lf1, lf2, lf3 = st.columns(3)
        with lf1:
            albumin = st.number_input("Albumin (g/dL)", 0.0, 6.0, value=st.session_state.lft_parameters.get('albumin', 0.0), step=0.1, key="lft_alb")
        with lf2:
            pt = st.number_input("PT (seconds)", 0.0, 100.0, value=st.session_state.lft_parameters.get('pt', 0.0), step=0.1, key="lft_pt")
        with lf3:
            inr = st.number_input("INR", 0.0, 20.0, value=st.session_state.lft_parameters.get('inr', 0.0), step=0.1, key="lft_inr")

        st.markdown("##### Additional Tests (optional)")
        at1, at2, at3 = st.columns(3)
        with at1:
            ggt = st.number_input("GGT (IU/L)", 0.0, 5000.0, step=0.1, key="lft_ggt")
        with at2:
            ldh = st.number_input("LDH (IU/L)", 0.0, 5000.0, step=0.1, key="lft_ldh")
        with at3:
            haptoglobin = st.number_input("Haptoglobin (mg/dL)", 0.0, 500.0, step=0.1, key="lft_hapto")

    st.session_state.lft_parameters = {
        'alt': alt, 'ast': ast, 'alp': alp,
        'total_bili': total_bili, 'direct_bili': direct_bili,
        'albumin': albumin, 'pt': pt, 'inr': inr,
        'ggt': ggt if ggt > 0 else None,
        'ldh': ldh if ldh > 0 else None,
        'haptoglobin': haptoglobin if haptoglobin > 0 else None
    }

    # Analyze
    if st.button("🔬 Analyze LFT", type="primary", key="run_lft"):
        if alt <= 0 or alp <= 0 or total_bili <= 0:
            st.error("Please enter at least ALT, ALP, and Total Bilirubin.")
        else:
            with st.spinner("Analyzing LFT…"):
                st.session_state.lft_analysis_results = analyze_lft(
                    st.session_state.lft_parameters,
                    st.session_state.lft_clinical
                )

    # Display results
    if st.session_state.lft_analysis_results:
        display_lft_results(st.session_state.lft_analysis_results)


def display_lft_results(results: Dict):
    """Render the LFT analysis results."""

    # Emergency alert
    if results.get('emergency'):
        st.markdown("""
        <div class="critical-alert">
            <h3>🚨 EMERGENCY PATHWAY ACTIVATED</h3>
            <p>This patient has worrisome clinical findings requiring immediate intervention.
            Do not delay life-saving treatments for diagnostic testing.</p>
        </div>
        """, unsafe_allow_html=True)

    # Summary metrics
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("R Value", results.get('r_value', 'N/A'))
    with mc2:
        st.metric("Pattern", results.get('pattern', 'N/A').replace('_', ' ').title())
    with mc3:
        sev = results.get('severity', {})
        st.metric("Severity", sev.get('grade', 'N/A').upper())
    with mc4:
        st.metric("AST/ALT Ratio", results.get('ast_alt_ratio', 'N/A'))

    # Pattern badge
    pattern = results.get('pattern', '')
    pattern_colors = {
        'hepatocellular': '🔴', 'cholestatic': '🔵',
        'mixed': '🟡', 'isolated_hyperbilirubinemia': '🟣'
    }
    st.markdown(f"### {pattern_colors.get(pattern, '⚪')} Pattern: **{pattern.replace('_', ' ').upper()}**")

    # Pathway
    st.markdown("### 📍 Diagnostic Pathway")
    pathway = results.get('pathway', '')
    pathway_content = results.get('pathway_content', '')
    if pathway_content:
        st.markdown(f'<div class="step-box">{pathway_content}</div>', unsafe_allow_html=True)

    # Step-by-step analysis
    st.markdown("### 🔬 Step-by-Step Analysis")

    # Step 1: R Value
    with st.expander("Step 1: Pattern Recognition (R Value)", expanded=True):
        r_calc = results.get('r_calculation', {})
        st.markdown(f"""
        **R = (ALT / ALT_ULN) / (ALP / ALP_ULN)**

        R = ({r_calc.get('alt', '?')} / {r_calc.get('alt_uln', '?')}) / ({r_calc.get('alp', '?')} / {r_calc.get('alp_uln', '?')})

        R = {r_calc.get('alt_ratio', '?')} / {r_calc.get('alp_ratio', '?')} = **{results.get('r_value', '?')}**

        | R Value | Pattern |
        |---------|---------|
        | ≥ 5 | Hepatocellular |
        | 2-5 | Mixed |
        | ≤ 2 | Cholestatic |
        """)

    # Step 2: Severity
    with st.expander("Step 2: Severity Assessment", expanded=True):
        abnormalities = results.get('abnormalities', {})
        severity_table = results.get('severity_table', [])
        if severity_table:
            df = pd.DataFrame(severity_table)
            st.dataframe(df, use_container_width=True)
        sev = results.get('severity', {})
        st.info(f"**Severity Grade:** {sev.get('grade', '').upper()} — {sev.get('description', '')}")

    # Step 3: Synthetic function
    with st.expander("Step 3: Synthetic Function Assessment", expanded=True):
        synth = results.get('synthetic_function', {})
        for k, v in synth.items():
            st.markdown(f"- **{k}**: {v}")
        if results.get('synthetic_impaired'):
            st.error("⚠️ Abnormal synthetic function suggests significant hepatic impairment.")

    # Step 4: AST/ALT Ratio
    with st.expander("Step 4: AST/ALT Ratio", expanded=True):
        st.markdown(f"**Ratio:** {results.get('ast_alt_ratio', 'N/A')}")
        st.markdown(f"**Interpretation:** {results.get('ast_alt_interpretation', '')}")

    # Differential Diagnosis
    st.markdown("### 🩺 Differential Diagnosis")
    differentials = results.get('differentials', [])
    for i, d in enumerate(differentials, 1):
        st.markdown(
            f'<div class="diagnosis-card">'
            f'<strong>{i}. {d["condition"]}</strong><br>{d["discussion"]}</div>',
            unsafe_allow_html=True
        )

    # Recommendations
    st.markdown("### 📋 Clinical Recommendations")
    recommendations = results.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        st.markdown(
            f'<div class="step-box"><strong>{i}. {rec["title"]}</strong><br>{rec["description"]}</div>',
            unsafe_allow_html=True
        )

    # Educational content
    with st.expander("📚 Educational Summary", expanded=False):
        edu = results.get('educational_content', '')
        st.markdown(edu)


def render_lft_standalone_panel():
    """Render the standalone LFT panel with tabs."""
    tab_entry, tab_ai_lft, tab_report_lft = st.tabs([
        "🧪 LFT Entry & Analysis", "🤖 AI Review", "📄 Report"
    ])

    with tab_entry:
        render_lft_entry_and_analysis()

    with tab_ai_lft:
        st.subheader("🤖 AI Review of LFT Findings")
        if not api_key:
            st.warning("Please enter your Claude API key in the sidebar.")
        elif not st.session_state.lft_analysis_results:
            st.info("Run the LFT analysis first.")
        else:
            if st.button("🧠 Generate LFT AI Review", type="primary", key="ai_lft"):
                with st.spinner("Claude is reviewing LFT findings…"):
                    from utils.ai_review import get_lft_ai_review
                    review = get_lft_ai_review(
                        st.session_state.lft_parameters,
                        st.session_state.lft_analysis_results,
                        st.session_state.lft_clinical,
                        api_key
                    )
                    st.session_state.ai_review_text = review
            if st.session_state.ai_review_text:
                st.markdown(st.session_state.ai_review_text)

    with tab_report_lft:
        st.subheader("📄 LFT Report")
        if st.session_state.lft_analysis_results:
            summary = json.dumps(st.session_state.lft_analysis_results, indent=2, default=str)
            st.text_area("LFT Analysis JSON", summary, height=300)
            st.download_button(
                "⬇️ Download LFT Summary",
                data=summary,
                file_name=f"lft_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info("Run the analysis first.")


# ════════════════════════════════════════════════════════════════════
#  MAIN ROUTING
# ════════════════════════════════════════════════════════════════════

if st.session_state.active_panel == 'CBC':
    render_cbc_panel()
elif st.session_state.active_panel == 'LFT':
    render_lft_standalone_panel()
else:  # Combined
    render_cbc_panel()