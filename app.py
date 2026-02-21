"""
🩸 Comprehensive Laboratory Investigation Analysis Tool
Multi-panel blood & urine investigation analysis with AI-powered review.
Supports: CBC, LFT, KFT, Lipid Profile, Blood Sugar, Urine R/M, TFT, 
          Rheumatology Markers, Oncology Markers
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

from utils.ocr_parser import process_uploaded_file, PARAMETER_PATTERNS
from utils.analysis_engine import (
    analyze_all_parameters, classify_value, get_reference_range,
    check_sample_quality, generate_summary_text, REFERENCE_RANGES,
    get_differential_diagnosis, calculate_additional_indices
)
from utils.lft_engine import analyze_lft, LFT_REFERENCE_RANGES
from utils.kft_engine import analyze_kft, KFT_REFERENCE_RANGES
from utils.lipid_engine import analyze_lipid, LIPID_REFERENCE_RANGES
from utils.sugar_engine import analyze_sugar, SUGAR_REFERENCE_RANGES
from utils.urine_engine import analyze_urine, URINE_REFERENCE_RANGES
from utils.tft_engine import analyze_tft, TFT_REFERENCE_RANGES
from utils.rheumatology_engine import analyze_rheumatology, RHEUM_REFERENCE_RANGES
from utils.oncology_engine import analyze_oncology, ONCO_REFERENCE_RANGES
from utils.ai_review import get_ai_review, get_panel_ai_review
from utils.pdf_generator import generate_pdf_report, generate_multi_panel_pdf
from utils.learning_engine import get_learning_content, get_parameter_education
from utils.panel_registry import PANEL_REGISTRY, get_all_panels, get_panel_parameters

# ── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="🩸 Lab Investigation Analysis Tool",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white; padding: 20px 30px; border-radius: 15px;
        margin-bottom: 20px; text-align: center;
    }
    .main-header h1 { font-size: 2.2em; margin-bottom: 5px; }
    .main-header p { opacity: 0.9; font-size: 1.05em; }
    .metric-card {
        background: white; border-radius: 12px; padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea; margin-bottom: 10px;
    }
    .critical-alert {
        background: #fee; border: 2px solid #e74c3c;
        border-radius: 10px; padding: 15px; margin: 10px 0;
    }
    .normal-badge {
        background: #d4edda; color: #155724; padding: 3px 10px;
        border-radius: 20px; font-weight: bold; font-size: 0.85em;
    }
    .abnormal-badge {
        background: #fff3cd; color: #856404; padding: 3px 10px;
        border-radius: 20px; font-weight: bold; font-size: 0.85em;
    }
    .critical-badge {
        background: #f8d7da; color: #721c24; padding: 3px 10px;
        border-radius: 20px; font-weight: bold; font-size: 0.85em;
    }
    .diagnosis-card {
        background: #f8f9fa; border-left: 4px solid #4ecdc4;
        padding: 12px 15px; margin: 8px 0; border-radius: 0 8px 8px 0;
    }
    .learning-card {
        background: #f0f4ff; border-left: 4px solid #667eea;
        padding: 15px; margin: 10px 0; border-radius: 0 10px 10px 0;
    }
    .step-box {
        background: white; padding: 18px; margin: 10px 0;
        border-radius: 10px; border-left: 4px solid #4ecdc4;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .panel-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 10px 20px; border-radius: 10px;
        margin: 15px 0 10px 0; font-weight: bold;
    }
    .quality-pass { border-left-color: #27ae60; }
    .quality-warning { border-left-color: #f39c12; }
    .quality-error { border-left-color: #e74c3c; }
    .quality-info { border-left-color: #3498db; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ──────────────────────────────────────────
PANELS = ['CBC', 'LFT', 'KFT', 'Lipid', 'Sugar', 'Urine', 'TFT', 'Rheumatology', 'Oncology']

for panel in PANELS:
    if f'{panel}_params' not in st.session_state:
        st.session_state[f'{panel}_params'] = {}
    if f'{panel}_analysis' not in st.session_state:
        st.session_state[f'{panel}_analysis'] = None
    if f'{panel}_clinical' not in st.session_state:
        st.session_state[f'{panel}_clinical'] = {}

if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'ai_review_text' not in st.session_state:
    st.session_state.ai_review_text = None
if 'active_panels' not in st.session_state:
    st.session_state.active_panels = ['CBC']

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚕️ Configuration")
    
    api_key = st.text_input(
        "Claude API Key", type="password",
        help="Enter your Anthropic API key for AI analysis",
        value=os.environ.get("ANTHROPIC_API_KEY", "")
    )
    
    st.divider()
    st.subheader("🔬 Active Panels")
    st.session_state.active_panels = st.multiselect(
        "Select investigation panels",
        PANELS,
        default=st.session_state.active_panels,
        help="Choose which panels to analyze"
    )
    
    st.divider()
    st.subheader("👤 Patient Info")
    sex = st.selectbox("Sex", ["Default", "Male", "Female"])
    st.session_state.patient_info['sex'] = sex
    age = st.number_input("Age", 0, 120, 
                          value=int(st.session_state.patient_info.get('age', 0) or 0))
    st.session_state.patient_info['age'] = str(age) if age > 0 else ''
    
    st.divider()
    st.warning("⚠️ **Educational tool only.** Not for clinical decisions.")

# ── Header ──────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🩸 Comprehensive Lab Investigation Analysis Tool</h1>
    <p>AI-Powered Multi-Panel Clinical Laboratory Analysis Platform</p>
    <p style="font-size:0.85em; opacity:0.8;">CBC • LFT • KFT • Lipid Profile • Blood Sugar • Urine R/M • TFT • Rheumatology • Oncology</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def render_status_badge(status: str) -> str:
    if 'critical' in str(status):
        return '<span class="critical-badge">⚠️ CRITICAL</span>'
    elif status in ('low', 'high', 'abnormal'):
        icon = '⬆' if status == 'high' else '⬇' if status == 'low' else '⚡'
        return f'<span class="abnormal-badge">{icon} ABNORMAL</span>'
    elif status == 'normal':
        return '<span class="normal-badge">✅ NORMAL</span>'
    return ''


def create_gauge_chart(value, low, high, title, unit):
    span = high - low if high != low else 1
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': f"{title} ({unit})", 'font': {'size': 13}},
        number={'font': {'size': 18}},
        gauge={
            'axis': {'range': [low - span, high + span]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [low - span, low], 'color': '#fee'},
                {'range': [low, high], 'color': '#d4edda'},
                {'range': [high, high + span], 'color': '#fff3cd'},
            ],
            'threshold': {'line': {'color': "red", 'width': 2}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=35, b=15))
    return fig


def create_panel_deviation_chart(analysis_results: Dict) -> go.Figure:
    params = analysis_results.get('parameters', {})
    names, devs, colors = [], [], []
    for name, data in params.items():
        c = data.get('classification', {})
        low, high, val = c.get('low'), c.get('high'), data.get('value')
        if low is None or high is None or val is None:
            continue
        mid = (low + high) / 2
        span = (high - low) / 2
        if span == 0:
            continue
        dev = ((val - mid) / span) * 100
        status = c.get('status', 'normal')
        color = '#e74c3c' if 'critical' in str(status) else '#f39c12' if status in ('low', 'high') else '#27ae60'
        names.append(name)
        devs.append(dev)
        colors.append(color)

    fig = go.Figure(go.Bar(
        x=devs, y=names, orientation='h', marker_color=colors,
        text=[f"{d:+.0f}%" for d in devs], textposition='outside'
    ))
    fig.add_vrect(x0=-100, x1=100, fillcolor="green", opacity=0.05, line_width=0)
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Parameter Deviation from Normal",
        xaxis_title="% Deviation", yaxis_title="",
        height=max(250, len(names) * 30),
        margin=dict(l=140, r=40, t=40, b=30)
    )
    return fig


def render_parameter_entry(panel_name: str, param_configs: List[Dict]):
    """Generic parameter entry widget for any panel."""
    params = st.session_state.get(f'{panel_name}_params', {})
    
    # Group into rows of 3-4
    cols_per_row = 3
    for i in range(0, len(param_configs), cols_per_row):
        batch = param_configs[i:i + cols_per_row]
        cols = st.columns(len(batch))
        for j, cfg in enumerate(batch):
            with cols[j]:
                key = cfg['key']
                label = cfg.get('label', key)
                unit = cfg.get('unit', '')
                mn = cfg.get('min', 0.0)
                mx = cfg.get('max', 10000.0)
                step = cfg.get('step', 0.1)
                is_text = cfg.get('text', False)
                
                current = params.get(key, {}).get('value', 0.0 if not is_text else '')
                
                if is_text:
                    val = st.text_input(
                        f"{label} ({unit})" if unit else label,
                        value=str(current) if current else '',
                        key=f"entry_{panel_name}_{key}"
                    )
                    if val:
                        params[key] = {'value': val, 'unit': unit}
                else:
                    val = st.number_input(
                        f"{label} ({unit})" if unit else label,
                        min_value=float(mn), max_value=float(mx),
                        value=float(current) if current else 0.0,
                        step=float(step),
                        key=f"entry_{panel_name}_{key}"
                    )
                    if val > 0:
                        params[key] = {'value': val, 'unit': unit}
    
    st.session_state[f'{panel_name}_params'] = params


def render_analysis_results(panel_name: str, analysis: Dict):
    """Generic analysis results renderer."""
    if not analysis:
        st.info("Run the analysis to see results.")
        return
    
    # Summary metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Parameters", analysis.get('total_parameters', 0))
    with cols[1]:
        st.metric("Abnormal", analysis.get('abnormal_count', 0),
                  delta=f"{analysis.get('abnormal_count',0)} abnormal" if analysis.get('abnormal_count',0) > 0 else None,
                  delta_color="inverse")
    with cols[2]:
        st.metric("Critical", analysis.get('critical_count', 0),
                  delta="⚠️ ALERT" if analysis.get('critical_count',0) > 0 else None,
                  delta_color="inverse")
    with cols[3]:
        normal = analysis.get('total_parameters', 0) - analysis.get('abnormal_count', 0)
        st.metric("Normal", normal)
    
    # Critical alerts
    if analysis.get('critical_values'):
        st.error("🚨 **CRITICAL VALUES DETECTED**")
        for cv in analysis['critical_values']:
            st.markdown(f"**{cv['parameter']}**: {cv.get('message', cv.get('value', ''))}")
    
    # Quality checks
    if analysis.get('quality_checks'):
        with st.expander("🔍 Quality Assessment", expanded=True):
            for check in analysis['quality_checks']:
                sev = check.get('severity', 'info')
                icon = {'pass':'✅','info':'ℹ️','warning':'⚠️','error':'❌'}.get(sev,'❓')
                css = f"quality-{sev}"
                st.markdown(
                    f'<div class="diagnosis-card {css}"><strong>{icon} {check.get("rule","")}</strong><br>'
                    f'{check.get("interpretation","")}</div>', unsafe_allow_html=True
                )
    
    # Deviation chart
    if analysis.get('parameters'):
        fig = create_panel_deviation_chart(analysis)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed parameters
    with st.expander("📋 Detailed Parameter Analysis", expanded=True):
        for pname, pdata in analysis.get('parameters', {}).items():
            c = pdata.get('classification', {})
            status = c.get('status', 'unknown')
            badge = render_status_badge(status)
            st.markdown(f"### {pname} {badge}", unsafe_allow_html=True)
            
            c1, c2 = st.columns([2, 3])
            with c1:
                low, high = c.get('low'), c.get('high')
                if low is not None and high is not None and isinstance(pdata.get('value'), (int, float)):
                    fig = create_gauge_chart(pdata['value'], low, high, pname, pdata.get('unit',''))
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown(f"**Value:** {pdata.get('value','')} {pdata.get('unit','')}")
                st.markdown(f"**Status:** {c.get('message','')}")
                
                diff = pdata.get('differential')
                if diff:
                    st.markdown(f"**{diff.get('title','')}**")
                    for k, d in enumerate(diff.get('differentials',[]), 1):
                        st.markdown(
                            f'<div class="diagnosis-card"><strong>{k}. {d["condition"]}</strong><br>'
                            f'{d["discussion"]}</div>', unsafe_allow_html=True
                        )
                
                # Learning content
                learning = pdata.get('learning')
                if learning:
                    st.markdown(
                        f'<div class="learning-card">📚 <strong>Learning Point:</strong> {learning}</div>',
                        unsafe_allow_html=True
                    )
            st.divider()
    
    # Calculated indices
    if analysis.get('calculated_indices'):
        with st.expander("🧮 Calculated Indices", expanded=False):
            for idx_name, idx_data in analysis['calculated_indices'].items():
                st.markdown(
                    f'<div class="diagnosis-card"><strong>{idx_name}: {idx_data.get("value","")}</strong><br>'
                    f'Formula: {idx_data.get("formula","")}<br>'
                    f'Interpretation: {idx_data.get("interpretation","")}<br>'
                    f'<em>{idx_data.get("note","")}</em></div>', unsafe_allow_html=True
                )
    
    # Overall pattern / summary
    if analysis.get('pattern_summary'):
        with st.expander("🔬 Pattern Recognition & Summary", expanded=True):
            st.markdown(analysis['pattern_summary'])
    
    # Recommendations
    if analysis.get('recommendations'):
        with st.expander("📋 Recommendations", expanded=False):
            for i, rec in enumerate(analysis['recommendations'], 1):
                st.markdown(
                    f'<div class="step-box"><strong>{i}. {rec.get("title","")}</strong><br>'
                    f'{rec.get("description","")}</div>', unsafe_allow_html=True
                )
    
    # Educational content
    if analysis.get('educational_content'):
        with st.expander("📚 Educational Summary & Learning Points", expanded=False):
            st.markdown(analysis['educational_content'])


def render_delete_section(panel_name: str):
    """Generic parameter deletion section."""
    params = st.session_state.get(f'{panel_name}_params', {})
    if params:
        st.markdown("#### 🗑️ Remove Parameters")
        to_delete = st.multiselect(
            "Select parameters to remove",
            options=list(params.keys()),
            key=f"del_{panel_name}"
        )
        if st.button(f"🗑️ Remove Selected", key=f"delbtn_{panel_name}"):
            for p in to_delete:
                del st.session_state[f'{panel_name}_params'][p]
            st.rerun()


def render_add_custom_section(panel_name: str):
    """Allow adding custom parameters not in the predefined list."""
    st.markdown("#### ➕ Add Custom Parameter")
    ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 1])
    with ac1:
        custom_name = st.text_input("Parameter Name", key=f"custom_name_{panel_name}")
    with ac2:
        custom_value = st.text_input("Value", key=f"custom_val_{panel_name}")
    with ac3:
        custom_unit = st.text_input("Unit", key=f"custom_unit_{panel_name}")
    with ac4:
        st.write("")
        st.write("")
        if st.button("➕ Add", key=f"custom_add_{panel_name}"):
            if custom_name and custom_value:
                try:
                    val = float(custom_value)
                except ValueError:
                    val = custom_value
                st.session_state[f'{panel_name}_params'][custom_name] = {
                    'value': val, 'unit': custom_unit
                }
                st.rerun()


def render_current_params_table(panel_name: str):
    """Show current parameters as a table."""
    params = st.session_state.get(f'{panel_name}_params', {})
    if params:
        st.markdown("#### 📋 Current Parameters")
        rows = []
        for name, data in params.items():
            rows.append({
                'Parameter': name,
                'Value': data.get('value', ''),
                'Unit': data.get('unit', '')
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
# PANEL CONFIGURATIONS (parameter entry definitions)
# ═══════════════════════════════════════════════════════════

CBC_PARAMS = [
    {'key': 'RBC', 'label': 'RBC', 'unit': 'x10¹²/L', 'max': 10.0, 'step': 0.01},
    {'key': 'Hemoglobin', 'label': 'Hemoglobin', 'unit': 'g/dL', 'max': 25.0},
    {'key': 'Hematocrit', 'label': 'Hematocrit', 'unit': '%', 'max': 70.0},
    {'key': 'MCV', 'label': 'MCV', 'unit': 'fL', 'max': 150.0},
    {'key': 'MCH', 'label': 'MCH', 'unit': 'pg', 'max': 50.0},
    {'key': 'MCHC', 'label': 'MCHC', 'unit': 'g/dL', 'max': 45.0},
    {'key': 'RDW', 'label': 'RDW-CV', 'unit': '%', 'max': 35.0},
    {'key': 'Reticulocytes', 'label': 'Reticulocytes', 'unit': '%', 'max': 20.0},
    {'key': 'WBC', 'label': 'WBC', 'unit': 'x10⁹/L', 'max': 100.0},
    {'key': 'Neutrophils', 'label': 'Neutrophils', 'unit': '%', 'max': 100.0},
    {'key': 'Lymphocytes', 'label': 'Lymphocytes', 'unit': '%', 'max': 100.0},
    {'key': 'Monocytes', 'label': 'Monocytes', 'unit': '%', 'max': 30.0},
    {'key': 'Eosinophils', 'label': 'Eosinophils', 'unit': '%', 'max': 30.0},
    {'key': 'Basophils', 'label': 'Basophils', 'unit': '%', 'max': 10.0},
    {'key': 'Platelets', 'label': 'Platelets', 'unit': 'x10⁹/L', 'max': 1500.0, 'step': 1.0},
    {'key': 'MPV', 'label': 'MPV', 'unit': 'fL', 'max': 20.0},
    {'key': 'PDW', 'label': 'PDW', 'unit': 'fL', 'max': 30.0},
    {'key': 'ESR', 'label': 'ESR', 'unit': 'mm/hr', 'max': 150.0, 'step': 1.0},
]

LFT_PARAMS = [
    {'key': 'ALT', 'label': 'ALT (SGPT)', 'unit': 'IU/L', 'max': 10000.0},
    {'key': 'AST', 'label': 'AST (SGOT)', 'unit': 'IU/L', 'max': 10000.0},
    {'key': 'ALP', 'label': 'Alkaline Phosphatase', 'unit': 'IU/L', 'max': 5000.0},
    {'key': 'GGT', 'label': 'GGT', 'unit': 'IU/L', 'max': 5000.0},
    {'key': 'Total_Bilirubin', 'label': 'Total Bilirubin', 'unit': 'mg/dL', 'max': 50.0},
    {'key': 'Direct_Bilirubin', 'label': 'Direct Bilirubin', 'unit': 'mg/dL', 'max': 30.0},
    {'key': 'Indirect_Bilirubin', 'label': 'Indirect Bilirubin', 'unit': 'mg/dL', 'max': 30.0},
    {'key': 'Total_Protein', 'label': 'Total Protein', 'unit': 'g/dL', 'max': 15.0},
    {'key': 'Albumin', 'label': 'Albumin', 'unit': 'g/dL', 'max': 6.0},
    {'key': 'Globulin', 'label': 'Globulin', 'unit': 'g/dL', 'max': 10.0},
    {'key': 'AG_Ratio', 'label': 'A/G Ratio', 'unit': '', 'max': 5.0, 'step': 0.01},
    {'key': 'LDH', 'label': 'LDH', 'unit': 'IU/L', 'max': 5000.0},
    {'key': 'PT', 'label': 'PT', 'unit': 'seconds', 'max': 100.0},
    {'key': 'INR', 'label': 'INR', 'unit': '', 'max': 20.0, 'step': 0.01},
]

KFT_PARAMS = [
    {'key': 'Creatinine', 'label': 'Creatinine', 'unit': 'mg/dL', 'max': 30.0, 'step': 0.01},
    {'key': 'BUN', 'label': 'BUN', 'unit': 'mg/dL', 'max': 200.0},
    {'key': 'Urea', 'label': 'Urea', 'unit': 'mg/dL', 'max': 400.0},
    {'key': 'Uric_Acid', 'label': 'Uric Acid', 'unit': 'mg/dL', 'max': 20.0},
    {'key': 'eGFR', 'label': 'eGFR', 'unit': 'mL/min/1.73m²', 'max': 200.0, 'step': 1.0},
    {'key': 'Cystatin_C', 'label': 'Cystatin C', 'unit': 'mg/L', 'max': 10.0, 'step': 0.01},
    {'key': 'Sodium', 'label': 'Sodium', 'unit': 'mEq/L', 'max': 180.0, 'step': 0.1},
    {'key': 'Potassium', 'label': 'Potassium', 'unit': 'mEq/L', 'max': 10.0, 'step': 0.01},
    {'key': 'Chloride', 'label': 'Chloride', 'unit': 'mEq/L', 'max': 130.0},
    {'key': 'Bicarbonate', 'label': 'Bicarbonate (CO2)', 'unit': 'mEq/L', 'max': 50.0},
    {'key': 'Calcium', 'label': 'Calcium', 'unit': 'mg/dL', 'max': 20.0, 'step': 0.01},
    {'key': 'Phosphorus', 'label': 'Phosphorus', 'unit': 'mg/dL', 'max': 15.0, 'step': 0.1},
    {'key': 'Magnesium', 'label': 'Magnesium', 'unit': 'mg/dL', 'max': 10.0, 'step': 0.01},
]

LIPID_PARAMS = [
    {'key': 'Total_Cholesterol', 'label': 'Total Cholesterol', 'unit': 'mg/dL', 'max': 600.0, 'step': 1.0},
    {'key': 'HDL', 'label': 'HDL-C', 'unit': 'mg/dL', 'max': 200.0, 'step': 1.0},
    {'key': 'LDL', 'label': 'LDL-C', 'unit': 'mg/dL', 'max': 500.0, 'step': 1.0},
    {'key': 'VLDL', 'label': 'VLDL-C', 'unit': 'mg/dL', 'max': 200.0, 'step': 1.0},
    {'key': 'Triglycerides', 'label': 'Triglycerides', 'unit': 'mg/dL', 'max': 2000.0, 'step': 1.0},
    {'key': 'Non_HDL', 'label': 'Non-HDL Cholesterol', 'unit': 'mg/dL', 'max': 500.0, 'step': 1.0},
    {'key': 'TC_HDL_Ratio', 'label': 'TC/HDL Ratio', 'unit': '', 'max': 20.0, 'step': 0.1},
    {'key': 'LDL_HDL_Ratio', 'label': 'LDL/HDL Ratio', 'unit': '', 'max': 15.0, 'step': 0.1},
    {'key': 'ApoA1', 'label': 'Apolipoprotein A1', 'unit': 'mg/dL', 'max': 300.0},
    {'key': 'ApoB', 'label': 'Apolipoprotein B', 'unit': 'mg/dL', 'max': 300.0},
    {'key': 'Lp_a', 'label': 'Lipoprotein(a)', 'unit': 'nmol/L', 'max': 500.0},
]

SUGAR_PARAMS = [
    {'key': 'Fasting_Glucose', 'label': 'Fasting Blood Glucose', 'unit': 'mg/dL', 'max': 600.0, 'step': 1.0},
    {'key': 'Random_Glucose', 'label': 'Random Blood Glucose', 'unit': 'mg/dL', 'max': 800.0, 'step': 1.0},
    {'key': 'PP_Glucose', 'label': 'Post-Prandial Glucose', 'unit': 'mg/dL', 'max': 600.0, 'step': 1.0},
    {'key': 'HbA1c', 'label': 'HbA1c', 'unit': '%', 'max': 20.0, 'step': 0.1},
    {'key': 'eAG', 'label': 'Estimated Average Glucose', 'unit': 'mg/dL', 'max': 500.0, 'step': 1.0},
    {'key': 'Insulin', 'label': 'Fasting Insulin', 'unit': 'µIU/mL', 'max': 200.0, 'step': 0.1},
    {'key': 'C_Peptide', 'label': 'C-Peptide', 'unit': 'ng/mL', 'max': 20.0, 'step': 0.01},
    {'key': 'HOMA_IR', 'label': 'HOMA-IR', 'unit': '', 'max': 30.0, 'step': 0.1},
]

URINE_PARAMS = [
    {'key': 'Urine_Color', 'label': 'Color', 'unit': '', 'text': True},
    {'key': 'Urine_Appearance', 'label': 'Appearance', 'unit': '', 'text': True},
    {'key': 'Urine_pH', 'label': 'pH', 'unit': '', 'max': 14.0, 'step': 0.1},
    {'key': 'Specific_Gravity', 'label': 'Specific Gravity', 'unit': '', 'max': 1.1, 'min': 1.0, 'step': 0.001},
    {'key': 'Urine_Protein', 'label': 'Protein', 'unit': '', 'text': True},
    {'key': 'Urine_Glucose', 'label': 'Glucose', 'unit': '', 'text': True},
    {'key': 'Urine_Ketones', 'label': 'Ketones', 'unit': '', 'text': True},
    {'key': 'Urine_Bilirubin', 'label': 'Bilirubin', 'unit': '', 'text': True},
    {'key': 'Urine_Urobilinogen', 'label': 'Urobilinogen', 'unit': '', 'text': True},
    {'key': 'Urine_Blood', 'label': 'Blood/Hemoglobin', 'unit': '', 'text': True},
    {'key': 'Urine_Nitrite', 'label': 'Nitrite', 'unit': '', 'text': True},
    {'key': 'Urine_Leukocyte_Esterase', 'label': 'Leukocyte Esterase', 'unit': '', 'text': True},
    {'key': 'Urine_RBC', 'label': 'RBC (/hpf)', 'unit': '/hpf', 'max': 500.0, 'step': 1.0},
    {'key': 'Urine_WBC', 'label': 'WBC (/hpf)', 'unit': '/hpf', 'max': 500.0, 'step': 1.0},
    {'key': 'Urine_Epithelial', 'label': 'Epithelial Cells (/hpf)', 'unit': '/hpf', 'max': 100.0, 'step': 1.0},
    {'key': 'Urine_Casts', 'label': 'Casts', 'unit': '', 'text': True},
    {'key': 'Urine_Crystals', 'label': 'Crystals', 'unit': '', 'text': True},
    {'key': 'Urine_Bacteria', 'label': 'Bacteria', 'unit': '', 'text': True},
    {'key': 'Urine_Yeast', 'label': 'Yeast', 'unit': '', 'text': True},
    {'key': 'Protein_Creatinine_Ratio', 'label': 'Protein/Creatinine Ratio', 'unit': 'mg/g', 'max': 5000.0},
    {'key': 'Albumin_Creatinine_Ratio', 'label': 'Albumin/Creatinine Ratio', 'unit': 'mg/g', 'max': 5000.0},
    {'key': 'Microalbumin', 'label': 'Microalbumin', 'unit': 'mg/L', 'max': 500.0},
]

TFT_PARAMS = [
    {'key': 'TSH', 'label': 'TSH', 'unit': 'mIU/L', 'max': 100.0, 'step': 0.01},
    {'key': 'T3', 'label': 'Total T3', 'unit': 'ng/dL', 'max': 500.0},
    {'key': 'T4', 'label': 'Total T4', 'unit': 'µg/dL', 'max': 25.0, 'step': 0.1},
    {'key': 'FT3', 'label': 'Free T3', 'unit': 'pg/mL', 'max': 20.0, 'step': 0.01},
    {'key': 'FT4', 'label': 'Free T4', 'unit': 'ng/dL', 'max': 10.0, 'step': 0.01},
    {'key': 'Reverse_T3', 'label': 'Reverse T3', 'unit': 'ng/dL', 'max': 100.0},
    {'key': 'T3_Uptake', 'label': 'T3 Uptake', 'unit': '%', 'max': 60.0},
    {'key': 'Anti_TPO', 'label': 'Anti-TPO', 'unit': 'IU/mL', 'max': 2000.0},
    {'key': 'Anti_Thyroglobulin', 'label': 'Anti-Thyroglobulin', 'unit': 'IU/mL', 'max': 2000.0},
    {'key': 'TSH_Receptor_Ab', 'label': 'TSH Receptor Antibody', 'unit': 'IU/L', 'max': 50.0},
    {'key': 'Thyroglobulin', 'label': 'Thyroglobulin', 'unit': 'ng/mL', 'max': 500.0},
]

RHEUM_PARAMS = [
    {'key': 'RF', 'label': 'Rheumatoid Factor', 'unit': 'IU/mL', 'max': 1000.0},
    {'key': 'Anti_CCP', 'label': 'Anti-CCP', 'unit': 'U/mL', 'max': 500.0},
    {'key': 'ANA', 'label': 'ANA Titer', 'unit': '', 'text': True},
    {'key': 'ANA_Pattern', 'label': 'ANA Pattern', 'unit': '', 'text': True},
    {'key': 'Anti_dsDNA', 'label': 'Anti-dsDNA', 'unit': 'IU/mL', 'max': 1000.0},
    {'key': 'Anti_Smith', 'label': 'Anti-Smith', 'unit': 'U/mL', 'max': 500.0},
    {'key': 'Complement_C3', 'label': 'Complement C3', 'unit': 'mg/dL', 'max': 300.0},
    {'key': 'Complement_C4', 'label': 'Complement C4', 'unit': 'mg/dL', 'max': 80.0},
    {'key': 'Anti_Phospholipid_IgG', 'label': 'Anti-Phospholipid IgG', 'unit': 'GPL', 'max': 200.0},
    {'key': 'Anti_Phospholipid_IgM', 'label': 'Anti-Phospholipid IgM', 'unit': 'MPL', 'max': 200.0},
    {'key': 'Anti_Cardiolipin_IgG', 'label': 'Anti-Cardiolipin IgG', 'unit': 'GPL', 'max': 200.0},
    {'key': 'Anti_Cardiolipin_IgM', 'label': 'Anti-Cardiolipin IgM', 'unit': 'MPL', 'max': 200.0},
    {'key': 'Lupus_Anticoagulant', 'label': 'Lupus Anticoagulant', 'unit': '', 'text': True},
    {'key': 'Beta2_Glycoprotein', 'label': 'Beta-2 Glycoprotein', 'unit': 'U/mL', 'max': 200.0},
    {'key': 'CRP', 'label': 'CRP', 'unit': 'mg/L', 'max': 500.0},
    {'key': 'hs_CRP', 'label': 'hs-CRP', 'unit': 'mg/L', 'max': 50.0, 'step': 0.01},
    {'key': 'ASO', 'label': 'ASO Titer', 'unit': 'IU/mL', 'max': 1000.0},
    {'key': 'HLA_B27', 'label': 'HLA-B27', 'unit': '', 'text': True},
]

ONCO_PARAMS = [
    {'key': 'AFP', 'label': 'AFP', 'unit': 'ng/mL', 'max': 50000.0},
    {'key': 'CEA', 'label': 'CEA', 'unit': 'ng/mL', 'max': 1000.0},
    {'key': 'Onco_LDH', 'label': 'LDH', 'unit': 'IU/L', 'max': 5000.0},
    {'key': 'Beta2_Microglobulin', 'label': 'Beta-2 Microglobulin', 'unit': 'mg/L', 'max': 30.0},
    {'key': 'CA_19_9', 'label': 'CA 19-9', 'unit': 'U/mL', 'max': 50000.0},
    {'key': 'CA_72_4', 'label': 'CA 72-4', 'unit': 'U/mL', 'max': 500.0},
    {'key': 'CA_15_3', 'label': 'CA 15-3', 'unit': 'U/mL', 'max': 500.0},
    {'key': 'CA_27_29', 'label': 'CA 27-29', 'unit': 'U/mL', 'max': 500.0},
    {'key': 'CA_125', 'label': 'CA 125', 'unit': 'U/mL', 'max': 5000.0},
    {'key': 'HE4', 'label': 'HE4', 'unit': 'pmol/L', 'max': 2000.0},
    {'key': 'ROMA_Index', 'label': 'ROMA Index', 'unit': '%', 'max': 100.0},
    {'key': 'Total_PSA', 'label': 'Total PSA', 'unit': 'ng/mL', 'max': 500.0, 'step': 0.01},
    {'key': 'Free_PSA', 'label': 'Free PSA', 'unit': 'ng/mL', 'max': 100.0, 'step': 0.01},
    {'key': 'PSA_Ratio', 'label': 'Free/Total PSA Ratio', 'unit': '%', 'max': 100.0},
    {'key': 'Beta_hCG', 'label': 'Beta-hCG', 'unit': 'mIU/mL', 'max': 500000.0},
    {'key': 'NSE', 'label': 'NSE', 'unit': 'ng/mL', 'max': 200.0},
    {'key': 'CYFRA_21_1', 'label': 'CYFRA 21-1', 'unit': 'ng/mL', 'max': 200.0},
    {'key': 'SCC', 'label': 'SCC Antigen', 'unit': 'ng/mL', 'max': 100.0},
    {'key': 'ProGRP', 'label': 'ProGRP', 'unit': 'pg/mL', 'max': 5000.0},
    {'key': 'Calcitonin', 'label': 'Calcitonin', 'unit': 'pg/mL', 'max': 1000.0},
    {'key': 'Onco_Thyroglobulin', 'label': 'Thyroglobulin', 'unit': 'ng/mL', 'max': 500.0},
    {'key': 'Chromogranin_A', 'label': 'Chromogranin A', 'unit': 'ng/mL', 'max': 1000.0},
    {'key': 'Ki_67', 'label': 'Ki-67', 'unit': '%', 'max': 100.0},
]

PANEL_PARAM_MAP = {
    'CBC': CBC_PARAMS,
    'LFT': LFT_PARAMS,
    'KFT': KFT_PARAMS,
    'Lipid': LIPID_PARAMS,
    'Sugar': SUGAR_PARAMS,
    'Urine': URINE_PARAMS,
    'TFT': TFT_PARAMS,
    'Rheumatology': RHEUM_PARAMS,
    'Oncology': ONCO_PARAMS,
}

PANEL_ANALYZER = {
    'CBC': lambda p, s: analyze_all_parameters(p, s),
    'LFT': lambda p, s: analyze_lft(p, {'sex': s.lower() if s != 'Default' else 'male'}),
    'KFT': lambda p, s: analyze_kft(p, s),
    'Lipid': lambda p, s: analyze_lipid(p, s),
    'Sugar': lambda p, s: analyze_sugar(p, s),
    'Urine': lambda p, s: analyze_urine(p, s),
    'TFT': lambda p, s: analyze_tft(p, s),
    'Rheumatology': lambda p, s: analyze_rheumatology(p, s),
    'Oncology': lambda p, s: analyze_oncology(p, s),
}

PANEL_ICONS = {
    'CBC': '🔴', 'LFT': '🟤', 'KFT': '🟡', 'Lipid': '🟠',
    'Sugar': '🍬', 'Urine': '🧪', 'TFT': '🦋', 
    'Rheumatology': '🦴', 'Oncology': '🎗️',
}


# ═══════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════

main_tabs = st.tabs([
    "📤 Upload & Extract",
    "✏️ Manual Entry",
    "📊 Analysis",
    "🤖 AI Review",
    "📄 Report"
])

# ── TAB 1: Upload & Extract ─────────────────────────────────
with main_tabs[0]:
    st.subheader("📤 Upload Blood Investigation Reports")
    st.write("Upload PDF or image files. The system will auto-extract parameters into the appropriate panels.")
    
    uploaded_files = st.file_uploader(
        "Choose file(s)",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uf in uploaded_files:
            with st.expander(f"📄 {uf.name}", expanded=True):
                c1, c2 = st.columns([1, 1])
                with c1:
                    if uf.type in ['image/jpeg', 'image/jpg', 'image/png']:
                        from PIL import Image
                        img = Image.open(uf)
                        st.image(img, caption=uf.name, use_container_width=True)
                        uf.seek(0)
                with c2:
                    with st.spinner("Extracting data..."):
                        text, params, info = process_uploaded_file(uf)
                    
                    st.text_area("Extracted Text", text, height=200, key=f"txt_{uf.name}")
                    
                    if params:
                        st.success(f"✅ Extracted {len(params)} parameters")
                        # Route to correct panel
                        for pname, pdata in params.items():
                            routed = False
                            for panel, pcfg_list in PANEL_PARAM_MAP.items():
                                panel_keys = [c['key'] for c in pcfg_list]
                                if pname in panel_keys:
                                    st.session_state[f'{panel}_params'][pname] = pdata
                                    routed = True
                                    break
                            if not routed:
                                st.session_state['CBC_params'][pname] = pdata
                    else:
                        st.warning("No parameters auto-extracted. Use manual entry.")
                    
                    if info:
                        for k, v in info.items():
                            st.session_state.patient_info[k] = v
                    
                    st.session_state.extracted_text += text + "\n"
        
        # Show summary
        st.markdown("### 📊 Extraction Summary")
        for panel in PANELS:
            count = len(st.session_state.get(f'{panel}_params', {}))
            if count > 0:
                st.write(f"{PANEL_ICONS.get(panel,'')} **{panel}**: {count} parameters extracted")

# ── TAB 2: Manual Entry ─────────────────────────────────────
with main_tabs[1]:
    st.subheader("✏️ Manual Parameter Entry & Editing")
    
    # Patient info section
    with st.expander("👤 Patient Information", expanded=False):
        pi1, pi2, pi3 = st.columns(3)
        with pi1:
            st.session_state.patient_info['name'] = st.text_input(
                "Name", value=st.session_state.patient_info.get('name', ''))
        with pi2:
            st.session_state.patient_info['age'] = st.text_input(
                "Age", value=st.session_state.patient_info.get('age', ''))
        with pi3:
            st.session_state.patient_info['date'] = st.text_input(
                "Report Date", value=st.session_state.patient_info.get('date', ''))
    
    # Panel entry tabs
    active = st.session_state.active_panels
    if not active:
        st.info("Select at least one panel in the sidebar.")
    else:
        panel_tabs = st.tabs([f"{PANEL_ICONS.get(p,'')} {p}" for p in active])
        
        for idx, panel in enumerate(active):
            with panel_tabs[idx]:
                st.markdown(f'<div class="panel-header">{PANEL_ICONS.get(panel,"")} {panel} Parameters</div>',
                           unsafe_allow_html=True)
                
                param_cfgs = PANEL_PARAM_MAP.get(panel, [])
                if param_cfgs:
                    render_parameter_entry(panel, param_cfgs)
                
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    render_add_custom_section(panel)
                with col_b:
                    render_delete_section(panel)
                
                render_current_params_table(panel)

# ── TAB 3: Analysis ──────────────────────────────────────────
with main_tabs[2]:
    st.subheader("📊 Analysis Results")
    
    active = st.session_state.active_panels
    if not active:
        st.info("Select panels in the sidebar.")
    else:
        # Run all analyses button
        if st.button("🔬 Run All Analyses", type="primary"):
            for panel in active:
                params = st.session_state.get(f'{panel}_params', {})
                if params:
                    with st.spinner(f"Analyzing {panel}..."):
                        analyzer = PANEL_ANALYZER.get(panel)
                        if analyzer:
                            try:
                                result = analyzer(params, sex)
                                st.session_state[f'{panel}_analysis'] = result
                            except Exception as e:
                                st.error(f"Error analyzing {panel}: {e}")
        
        # Display results per panel
        analysis_tabs = st.tabs([f"{PANEL_ICONS.get(p,'')} {p}" for p in active])
        
        for idx, panel in enumerate(active):
            with analysis_tabs[idx]:
                analysis = st.session_state.get(f'{panel}_analysis')
                params = st.session_state.get(f'{panel}_params', {})
                
                if not params:
                    st.info(f"No {panel} parameters entered yet.")
                elif not analysis:
                    st.info(f"Click 'Run All Analyses' or enter {panel} values first.")
                else:
                    render_analysis_results(panel, analysis)

# ── TAB 4: AI Review ─────────────────────────────────────────
with main_tabs[3]:
    st.subheader("🤖 AI-Powered Clinical Review (Claude)")
    
    if not api_key:
        st.warning("Enter your Claude API key in the sidebar.")
    else:
        review_panel = st.selectbox(
            "Select panel for AI review",
            ['All Active Panels'] + st.session_state.active_panels
        )
        
        if st.button("🧠 Generate AI Review", type="primary"):
            with st.spinner("Claude is analyzing..."):
                if review_panel == 'All Active Panels':
                    all_data = {}
                    for p in st.session_state.active_panels:
                        a = st.session_state.get(f'{p}_analysis')
                        if a:
                            all_data[p] = a
                    if all_data:
                        review = get_panel_ai_review(
                            all_data, st.session_state.patient_info, api_key
                        )
                        st.session_state.ai_review_text = review
                    else:
                        st.warning("Run analyses first.")
                else:
                    a = st.session_state.get(f'{review_panel}_analysis')
                    if a:
                        review = get_panel_ai_review(
                            {review_panel: a}, st.session_state.patient_info, api_key
                        )
                        st.session_state.ai_review_text = review
                    else:
                        st.warning(f"Run {review_panel} analysis first.")
        
        if st.session_state.ai_review_text:
            st.markdown("---")
            st.markdown(st.session_state.ai_review_text)

# ── TAB 5: Report ────────────────────────────────────────────
with main_tabs[4]:
    st.subheader("📄 Download / Share Report")
    
    has_analysis = any(
        st.session_state.get(f'{p}_analysis') is not None 
        for p in st.session_state.active_panels
    )
    
    if not has_analysis:
        st.info("Run analyses first to generate a report.")
    else:
        include_ai = st.checkbox("Include AI Review", value=bool(st.session_state.ai_review_text))
        
        if st.button("📥 Generate PDF Report", type="primary"):
            with st.spinner("Generating PDF..."):
                all_analyses = {}
                for p in st.session_state.active_panels:
                    a = st.session_state.get(f'{p}_analysis')
                    if a:
                        all_analyses[p] = a
                
                ai_text = st.session_state.ai_review_text if include_ai else None
                pdf_bytes = generate_multi_panel_pdf(
                    all_analyses,
                    st.session_state.patient_info,
                    ai_text
                )
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"lab_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        
        # Text summary
        st.markdown("---")
        summary_parts = []
        for p in st.session_state.active_panels:
            a = st.session_state.get(f'{p}_analysis')
            if a and a.get('parameters'):
                summary_parts.append(f"\n{'='*50}\n{p} ANALYSIS\n{'='*50}")
                for pname, pdata in a['parameters'].items():
                    c = pdata.get('classification', {})
                    summary_parts.append(
                        f"  {pname}: {pdata.get('value','')} {pdata.get('unit','')} "
                        f"[{c.get('status','').upper()}]"
                    )
        
        if summary_parts:
            summary_text = "\n".join(summary_parts)
            st.text_area("Summary", summary_text, height=300)
            st.download_button(
                "⬇️ Download Text",
                data=summary_text,
                file_name=f"lab_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
