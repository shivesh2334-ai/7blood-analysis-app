"""
Hematology Blood Investigation Analysis Tool
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import io

from utils.ocr_parser import process_uploaded_file, PARAMETER_PATTERNS
from utils.analysis_engine import (
    analyze_all_parameters,
    classify_value,
    get_reference_range,
    REFERENCE_RANGES,
    get_differential_diagnosis,
    check_sample_quality,
    generate_summary_text,
)
from utils.ai_review import get_ai_review, get_parameter_specific_ai_review
from utils.pdf_generator import generate_pdf_report

# =============================================
# PAGE CONFIG
# =============================================
st.set_page_config(
    page_title="Hematology Blood Analysis Tool",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CUSTOM CSS
# =============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1a5276;
        text-align: center;
        padding: 10px;
        border-bottom: 3px solid #2980b9;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #5d6d7e;
        text-align: center;
        margin-bottom: 20px;
    }
    .critical-alert {
        background-color: #fdedec;
        border-left: 5px solid #e74c3c;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .warning-alert {
        background-color: #fef9e7;
        border-left: 5px solid #f39c12;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .normal-alert {
        background-color: #eafaf1;
        border-left: 5px solid #27ae60;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .info-alert {
        background-color: #ebf5fb;
        border-left: 5px solid #3498db;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .param-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
    }
    .stMetric > div {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# SESSION STATE INITIALIZATION
# =============================================
if 'parameters' not in st.session_state:
    st.session_state.parameters = {}
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'ai_review_text' not in st.session_state:
    st.session_state.ai_review_text = None
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = False

# =============================================
# SIDEBAR
# =============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/blood-sample.png", width=80)
    st.title("🩸 Hematology Analyzer")
    st.markdown("---")

    # API Key
    st.subheader("🔑 Claude AI Configuration")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Claude API key for AI-powered review",
        placeholder="sk-ant-..."
    )

    st.markdown("---")

    # Patient Demographics
    st.subheader("👤 Patient Demographics")
    patient_name = st.text_input("Patient Name", value=st.session_state.patient_info.get('name', ''))
    patient_age = st.text_input("Age", value=st.session_state.patient_info.get('age', ''))
    patient_sex = st.selectbox("Sex", ['Default', 'Male', 'Female'],
                                index=['Default', 'Male', 'Female'].index(
                                    st.session_state.patient_info.get('sex', 'Default')
                                ) if st.session_state.patient_info.get('sex', 'Default') in ['Default', 'Male', 'Female'] else 0)
    patient_date = st.text_input("Report Date", value=st.session_state.patient_info.get('date', ''))
    patient_lab = st.text_input("Laboratory", value=st.session_state.patient_info.get('lab', ''))

    if st.button("Update Patient Info", use_container_width=True):
        st.session_state.patient_info = {
            'name': patient_name,
            'age': patient_age,
            'sex': patient_sex,
            'date': patient_date,
            'lab': patient_lab
        }
        st.success("Patient info updated!")

    st.markdown("---")
    st.subheader("ℹ️ About")
    st.markdown("""
    This tool provides automated analysis of blood investigation reports 
    including CBC parameters, differential diagnosis, and AI-powered review.

    **Supported formats:** PDF, JPG, JPEG, PNG

    **Disclaimer:** For educational purposes only.
    """)

    # Reset button
    st.markdown("---")
    if st.button("🔄 Reset All Data", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# =============================================
# MAIN CONTENT
# =============================================
st.markdown('<div class="main-header">🩸 Hematology Blood Investigation Analysis Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated CBC Analysis • Differential Diagnosis • AI-Powered Review</div>', unsafe_allow_html=True)

# =============================================
# TAB LAYOUT
# =============================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📤 Upload & Extract",
    "✏️ Edit Parameters",
    "🔬 Analysis",
    "📊 Visualizations",
    "🤖 AI Review",
    "📄 Report"
])

# =============================================
# TAB 1: UPLOAD & EXTRACT
# =============================================
with tab1:
    st.header("📤 Upload Blood Investigation Reports")
    st.markdown("Upload one or more blood investigation reports (PDF, JPG, JPEG, PNG) for automated extraction.")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Upload blood investigation reports in PDF or image format"
    )

    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} file(s) uploaded")

        if st.button("🔍 Process Files", type="primary", use_container_width=True):
            all_text = ""
            all_parameters = {}

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing: {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))

                try:
                    text, params, pat_info = process_uploaded_file(uploaded_file)
                    all_text += f"\n--- File: {uploaded_file.name} ---\n{text}\n"

                    # Merge parameters (later files override earlier ones)
                    for param_name, param_data in params.items():
                        all_parameters[param_name] = param_data

                    # Merge patient info (non-empty values override)
                    for key, value in pat_info.items():
                        if value:
                            if key not in st.session_state.patient_info or not st.session_state.patient_info[key]:
                                st.session_state.patient_info[key] = value

                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")

            progress_bar.progress(1.0)
            status_text.text("Processing complete!")

            st.session_state.extracted_text = all_text
            st.session_state.parameters = all_parameters
            st.session_state.files_processed = True

            st.success(f"✅ Extracted {len(all_parameters)} parameters from {len(uploaded_files)} file(s)")

        # Show extracted text
        if st.session_state.extracted_text:
            with st.expander("📝 View Extracted Text", expanded=False):
                st.text_area("Raw OCR Text", st.session_state.extracted_text, height=300, disabled=True)

        # Show extracted parameters
        if st.session_state.parameters:
            st.subheader("📋 Extracted Parameters")
            param_df_data = []
            for param_name, param_data in st.session_state.parameters.items():
                param_df_data.append({
                    'Parameter': param_name,
                    'Value': param_data.get('value', 'N/A'),
                    'Unit': param_data.get('unit', ''),
                    'Raw Match': param_data.get('raw_match', '')
                })

            if param_df_data:
                df = pd.DataFrame(param_df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.markdown("""
        <div class="info-alert">
            <h4>📋 How to use:</h4>
            <ol>
                <li>Upload one or more blood investigation reports (PDF or image)</li>
                <li>Click "Process Files" to extract parameters via OCR</li>
                <li>Review and edit extracted values in the "Edit Parameters" tab</li>
                <li>View analysis, visualizations, and AI review in respective tabs</li>
                <li>Download the complete report as PDF</li>
            </ol>
            <p><strong>Tip:</strong> You can also manually enter parameters in the "Edit Parameters" tab without uploading files.</p>
        </div>
        """, unsafe_allow_html=True)

# =============================================
# TAB 2: EDIT PARAMETERS
# =============================================
with tab2:
    st.header("✏️ Edit Blood Parameters")
    st.markdown("Review, add, edit, or delete extracted parameters. You can also manually enter values.")

    sex = st.session_state.patient_info.get('sex', 'Default')

    # Organize parameters by category
    categories = {
        'RBC Parameters': ['RBC', 'Hemoglobin', 'Hematocrit', 'MCV', 'MCH', 'MCHC', 'RDW', 'RDW_SD'],
        'WBC Parameters': ['WBC', 'Neutrophils', 'Lymphocytes', 'Monocytes', 'Eosinophils', 'Basophils', 'ANC', 'ALC'],
        'Platelet Parameters': ['Platelets', 'MPV', 'PDW'],
        'Other Parameters': ['Reticulocytes', 'ESR']
    }

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("➕ Add Parameter")
        all_params = []
        for cat_params in categories.values():
            all_params.extend(cat_params)

        # Add custom option
        new_param = st.selectbox("Select Parameter", ['-- Select --'] + all_params)
        new_value = st.number_input("Value", value=0.0, format="%.2f", step=0.1)
        new_unit = st.text_input("Unit (auto-filled)", value='')

        if new_param != '-- Select --' and new_param in REFERENCE_RANGES:
            ref = get_reference_range(new_param, sex)
            if ref and not new_unit:
                new_unit = ref.get('unit', '')
                st.caption(f"Reference: {ref.get('low', '')}-{ref.get('high', '')} {new_unit}")

        if st.button("Add Parameter", type="primary", use_container_width=True):
            if new_param != '-- Select --' and new_value != 0:
                st.session_state.parameters[new_param] = {
                    'value': new_value,
                    'unit': new_unit if new_unit else REFERENCE_RANGES.get(new_param, {}).get('Default', {}).get('unit', ''),
                    'raw_match': 'Manual Entry'
                }
                st.success(f"Added {new_param}: {new_value}")
                st.rerun()
            else:
                st.warning("Please select a parameter and enter a value.")

        # Custom parameter
        st.markdown("---")
        st.subheader("🆕 Custom Parameter")
        custom_name = st.text_input("Parameter Name")
        custom_value = st.number_input("Custom Value", value=0.0, format="%.2f", step=0.1, key="custom_val")
        custom_unit = st.text_input("Custom Unit")

        if st.button("Add Custom", use_container_width=True):
            if custom_name and custom_value != 0:
                st.session_state.parameters[custom_name] = {
                    'value': custom_value,
                    'unit': custom_unit,
                    'raw_match': 'Custom Entry'
                }
                st.success(f"Added {custom_name}: {custom_value}")
                st.rerun()

    with col1:
        st.subheader("📊 Current Parameters")

        if not st.session_state.parameters:
            st.info("No parameters loaded. Upload a report or add parameters manually.")
        else:
            for category, param_list in categories.items():
                category_params = {k: v for k, v in st.session_state.parameters.items() if k in param_list}
                if category_params:
                    st.markdown(f"#### {category}")

                    for param_name, param_data in category_params.items():
                        col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 1])

                        with col_a:
                            st.markdown(f"**{param_name}**")

                        with col_b:
                            new_val = st.number_input(
                                f"Value##{param_name}",
                                value=float(param_data.get('value', 0)),
                                format="%.2f",
                                step=0.1,
                                label_visibility="collapsed",
                                key=f"edit_{param_name}"
                            )
                            if new_val != param_data.get('value'):
                                st.session_state.parameters[param_name]['value'] = new_val

                        with col_c:
                            ref = get_reference_range(param_name, sex)
                            if ref:
                                classification = classify_value(param_name, new_val, sex)
                                status = classification.get('status', 'unknown')
                                color_map = {
                                    'normal': '🟢', 'low': '🟡', 'high': '🟡',
                                    'critical_low': '🔴', 'critical_high': '🔴', 'unknown': '⚪'
                                }
                                st.markdown(f"{color_map.get(status, '⚪')} {status.upper()}")
                                st.caption(f"Ref: {ref.get('low', '')}-{ref.get('high', '')} {ref.get('unit', '')}")
                            else:
                                st.markdown("⚪ No ref range")

                        with col_d:
                            if st.button("🗑️", key=f"del_{param_name}", help=f"Delete {param_name}"):
                                del st.session_state.parameters[param_name]
                                st.rerun()

                    st.markdown("---")

            # Show any parameters not in predefined categories
            all_categorized = []
            for params in categories.values():
                all_categorized.extend(params)
            uncategorized = {k: v for k, v in st.session_state.parameters.items() if k not in all_categorized}

            if uncategorized:
                st.markdown("#### Other/Custom Parameters")
                for param_name, param_data in uncategorized.items():
                    col_a, col_b, col_c = st.columns([3, 3, 1])
                    with col_a:
                        st.markdown(f"**{param_name}**: {param_data.get('value', 'N/A')} {param_data.get('unit', '')}")
                    with col_b:
                        st.caption(f"Source: {param_data.get('raw_match', 'Unknown')}")
                    with col_c:
                        if st.button("🗑️", key=f"del_custom_{param_name}"):
                            del st.session_state.parameters[param_name]
                            st.rerun()

# =============================================
# TAB 3: ANALYSIS
# =============================================
with tab3:
    st.header("🔬 Comprehensive Analysis")

    if not st.session_state.parameters:
        st.warning("⚠️ No parameters available. Please upload a report or add parameters manually.")
    else:
        sex = st.session_state.patient_info.get('sex', 'Default')

        # Run analysis
        if st.button("🔬 Run Analysis", type="primary", use_container_width=True):
            st.session_state.analysis = analyze_all_parameters(st.session_state.parameters, sex)

        if st.session_state.analysis:
            analysis = st.session_state.analysis

            # Summary Metrics
            st.subheader("📈 Summary")
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Total Parameters", analysis['total_parameters'])
            with metric_cols[1]:
                st.metric("Normal Values", analysis['total_parameters'] - analysis['abnormal_count'])
            with metric_cols[2]:
                st.metric("Abnormal Values", analysis['abnormal_count'])
            with metric_cols[3]:
                st.metric("Critical Values", analysis['critical_count'])

            # Critical Values Alert
            if analysis['critical_values']:
                st.markdown("---")
                st.subheader("🚨 Critical Values Alert")
                for cv in analysis['critical_values']:
                    st.markdown(f"""
                    <div class="critical-alert">
                        <strong>⚠️ {cv['parameter']}</strong>: {cv['message']}
                    </div>
                    """, unsafe_allow_html=True)

            # Quality Assessment
            st.markdown("---")
            st.subheader("🧪 Sample Quality Assessment")

            for check in analysis['quality_checks']:
                severity = check.get('severity', 'info')
                css_class = {
                    'pass': 'normal-alert',
                    'info': 'info-alert',
                    'warning': 'warning-alert',
                    'error': 'critical-alert'
                }.get(severity, 'info-alert')

                icon = {'pass': '✅', 'info': 'ℹ️', 'warning': '⚠️', 'error': '❌'}.get(severity, 'ℹ️')

                st.markdown(f"""
                <div class="{css_class}">
                    <strong>{icon} {check['rule']}</strong><br>
                    Expected: {check['expected']} | Actual: {check['actual']} | Deviation: {check['deviation']}<br>
                    <em>{check['interpretation']}</em>
                </div>
                """, unsafe_allow_html=True)

            # Calculated Indices
            if analysis.get('calculated_indices'):
                st.markdown("---")
                st.subheader("🔢 Calculated Indices")

                idx_cols = st.columns(min(len(analysis['calculated_indices']), 3))
                for i, (idx_name, idx_data) in enumerate(analysis['calculated_indices'].items()):
                    with idx_cols[i % len(idx_cols)]:
                        st.markdown(f"""
                        <div class="param-box">
                            <strong>{idx_name}</strong><br>
                            <span style="font-size: 1.5em; color: #2980b9;">{idx_data['value']}</span><br>
                            <small>{idx_data['interpretation']}</small><br>
                            <small><em>Formula: {idx_data['formula']}</em></small><br>
                            <small>{idx_data['note']}</small>
                        </div>
                        """, unsafe_allow_html=True)

            # Detailed Parameter Analysis with Differential Diagnoses
            st.markdown("---")
            st.subheader("📋 Detailed Parameter Analysis & Differential Diagnoses")

            for param_name, param_data in analysis['parameters'].items():
                classification = param_data.get('classification', {})
                status = classification.get('status', 'unknown')
                differential = param_data.get('differential')

                # Color coding
                if 'critical' in status:
                    border_color = '#e74c3c'
                    bg_color = '#fdedec'
                elif status in ['low', 'high']:
                    border_color = '#f39c12'
                    bg_color = '#fef9e7'
                elif status == 'normal':
                    border_color = '#27ae60'
                    bg_color = '#eafaf1'
                else:
                    border_color = '#95a5a6'
                    bg_color = '#f8f9fa'

                with st.expander(f"{'🔴' if 'critical' in status else '🟡' if status in ['low', 'high'] else '🟢'} {param_name}: {param_data['value']} {param_data['unit']} — {status.upper()}", expanded=('critical' in status)):

                    st.markdown(f"""
                    **Value:** {param_data['value']} {param_data['unit']}  
                    **Status:** {status.upper()}  
                    **Reference Range:** {classification.get('low', 'N/A')} - {classification.get('high', 'N/A')} {classification.get('unit', '')}
                    """)

                    if differential:
                        st.markdown(f"#### 📖 {differential['title']}")
                        st.markdown("**Differential Diagnoses:**")

                        for i, d in enumerate(differential['differentials'], 1):
                            st.markdown(f"""
                            **{i}. {d['condition']}**  
                            {d['discussion']}
                            """)
                            st.markdown("---")

                    # Parameter-specific AI review button
                    if api_key:
                        if st.button(f"🤖 AI Review for {param_name}", key=f"ai_param_{param_name}"):
                            with st.spinner(f"Getting AI review for {param_name}..."):
                                param_ai = get_parameter_specific_ai_review(
                                    param_name, param_data['value'], param_data['unit'],
                                    classification, api_key
                                )
                                if param_ai:
                                    st.markdown("#### 🤖 AI Analysis")
                                    st.markdown(param_ai)

# =============================================
# TAB 4: VISUALIZATIONS
# =============================================
with tab4:
    st.header("📊 Data Visualizations")

    if not st.session_state.parameters:
        st.warning("⚠️ No parameters available for visualization.")
    else:
        sex = st.session_state.patient_info.get('sex', 'Default')

        # Run analysis if not done
        if not st.session_state.analysis:
            st.session_state.analysis = analyze_all_parameters(st.session_state.parameters, sex)

        analysis = st.session_state.analysis

        # 1. Parameter Status Overview (Donut Chart)
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Parameter Status Overview")
            normal_count = analysis['total_parameters'] - analysis['abnormal_count']
            abnormal_non_critical = analysis['abnormal_count'] - analysis['critical_count']
            critical_count = analysis['critical_count']

            fig_donut = go.Figure(data=[go.Pie(
                labels=['Normal', 'Abnormal', 'Critical'],
                values=[normal_count, abnormal_non_critical, critical_count],
                hole=0.5,
                marker_colors=['#27ae60', '#f39c12', '#e74c3c'],
                textinfo='label+value'
            )])
            fig_donut.update_layout(
                height=350,
                margin=dict(t=30, b=30, l=30, r=30),
                showlegend=True
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            st.subheader("Abnormality Breakdown")
            if analysis['abnormalities']:
                abn_data = []
                for abn in analysis['abnormalities']:
                    abn_data.append({
                        'Parameter': abn['parameter'],
                        'Status': abn['classification']['status'].replace('_', ' ').upper(),
                        'Value': abn['classification']['value']
                    })
                abn_df = pd.DataFrame(abn_data)

                fig_bar = px.bar(
                    abn_df,
                    x='Parameter',
                    y='Value',
                    color='Status',
                    color_discrete_map={
                        'LOW': '#3498db', 'HIGH': '#e67e22',
                        'CRITICAL LOW': '#e74c3c', 'CRITICAL HIGH': '#c0392b'
                    },
                    title='Abnormal Parameters'
                )
                fig_bar.update_layout(height=350)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.success("✅ All parameters are within normal range!")

        # 2. RBC Parameters Gauge Charts
        st.markdown("---")
        st.subheader("🔴 RBC Parameters")

        rbc_params = ['RBC', 'Hemoglobin', 'Hematocrit', 'MCV', 'MCH', 'MCHC', 'RDW']
        rbc_available = [p for p in rbc_params if p in st.session_state.parameters]

        if rbc_available:
            cols = st.columns(min(len(rbc_available), 4))
            for i, param in enumerate(rbc_available):
                with cols[i % len(cols)]:
                    value = st.session_state.parameters[param]['value']
                    ref = get_reference_range(param, sex)
                    if ref:
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=value,
                            title={'text': param, 'font': {'size': 14}},
                            gauge={
                                'axis': {
                                    'range': [
                                        ref.get('critical_low', ref['low'] * 0.5),
                                        ref.get('critical_high', ref['high'] * 1.5)
                                    ]
                                },
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [ref.get('critical_low', 0), ref['low']], 'color': '#fadbd8'},
                                    {'range': [ref['low'], ref['high']], 'color': '#d5f5e3'},
                                    {'range': [ref['high'], ref.get('critical_high', ref['high'] * 1.5)], 'color': '#fadbd8'}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 2},
                                    'thickness': 0.75,
                                    'value': value
                                }
                            }
                        ))
                        fig_gauge.update_layout(height=250, margin=dict(t=40, b=10, l=30, r=30))
                        st.plotly_chart(fig_gauge, use_container_width=True)

        # 3. WBC Differential Pie Chart
        st.markdown("---")
        st.subheader("⚪ WBC Differential")

        wbc_diff_params = ['Neutrophils', 'Lymphocytes', 'Monocytes', 'Eosinophils', 'Basophils']
        wbc_diff_available = {p: st.session_state.parameters[p]['value']
                             for p in wbc_diff_params
                             if p in st.session_state.parameters}

        if wbc_diff_available:
            col1, col2 = st.columns(2)

            with col1:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(wbc_diff_available.keys()),
                    values=list(wbc_diff_available.values()),
                    marker_colors=['#3498db', '#2ecc71', '#9b59b6', '#e67e22', '#e74c3c'],
                    textinfo='label+percent'
                )])
                fig_pie.update_layout(
                    title='WBC Differential Distribution',
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # WBC comparison bar chart
                wbc_ref_data = []
                for param in wbc_diff_available:
                    ref = get_reference_range(param, sex)
                    if ref:
                        wbc_ref_data.append({
                            'Parameter': param,
                            'Value': wbc_diff_available[param],
                            'Low Ref': ref['low'],
                            'High Ref': ref['high']
                        })

                if wbc_ref_data:
                    wbc_df = pd.DataFrame(wbc_ref_data)
                    fig_wbc = go.Figure()
                    fig_wbc.add_trace(go.Bar(
                        name='Value', x=wbc_df['Parameter'], y=wbc_df['Value'],
                        marker_color='#3498db'
                    ))
                    fig_wbc.add_trace(go.Scatter(
                        name='Low Ref', x=wbc_df['Parameter'], y=wbc_df['Low Ref'],
                        mode='markers+lines', marker=dict(color='orange', size=8)
                    ))
                    fig_wbc.add_trace(go.Scatter(
                        name='High Ref', x=wbc_df['Parameter'], y=wbc_df['High Ref'],
                        mode='markers+lines', marker=dict(color='red', size=8)
                    ))
                    fig_wbc.update_layout(title='WBC vs Reference Range', height=400, barmode='group')
                    st.plotly_chart(fig_wbc, use_container_width=True)

        # 4. All Parameters vs Reference Range
        st.markdown("---")
        st.subheader("📊 All Parameters vs Reference Range (Normalized)")

        if analysis['parameters']:
            norm_data = []
            for param_name, param_data in analysis['parameters'].items():
                classification = param_data['classification']
                ref_low = classification.get('low')
                ref_high = classification.get('high')
                value = param_data['value']

                if ref_low is not None and ref_high is not None and (ref_high - ref_low) > 0:
                    midpoint = (ref_low + ref_high) / 2
                    range_size = ref_high - ref_low
                    normalized = ((value - midpoint) / (range_size / 2)) * 100

                    norm_data.append({
                        'Parameter': param_name,
                        'Normalized (%)': normalized,
                        'Status': classification.get('status', 'unknown')
                    })

            if norm_data:
                norm_df = pd.DataFrame(norm_data)
                colors = []
                for _, row in norm_df.iterrows():
                    if 'critical' in row['Status']:
                        colors.append('#e74c3c')
                    elif row['Status'] in ['low', 'high']:
                        colors.append('#f39c12')
                    else:
                        colors.append('#27ae60')

                fig_norm = go.Figure(data=[
                    go.Bar(
                        x=norm_df['Parameter'],
                        y=norm_df['Normalized (%)'],
                        marker_color=colors,
                        text=[f"{v:.0f}%" for v in norm_df['Normalized (%)']],
                        textposition='auto'
                    )
                ])
                fig_norm.add_hline(y=100, line_dash="dash", line_color="red",
                                   annotation_text="Upper Limit")
                fig_norm.add_hline(y=-100, line_dash="dash", line_color="red",
                                   annotation_text="Lower Limit")
                fig_norm.add_hrect(y0=-100, y1=100, fillcolor="green", opacity=0.05)
                fig_norm.update_layout(
                    title='Normalized Parameter Values (0% = midpoint of reference range)',
                    yaxis_title='Deviation from midpoint (%)',
                    height=500
                )
                st.plotly_chart(fig_norm, use_container_width=True)

# =============================================
# TAB 5: AI REVIEW
# =============================================
with tab5:
    st.header("🤖 AI-Powered Clinical Review")
    st.markdown("Get a comprehensive AI review of the blood investigation findings using Claude AI.")

    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to use AI review features.")
        st.markdown("""
        **How to get an API key:**
        1. Visit [console.anthropic.com](https://console.anthropic.com)
        2. Create an account or sign in
        3. Generate an API key
        4. Paste it in the sidebar
        """)
    elif not st.session_state.parameters:
        st.warning("⚠️ No parameters available. Please upload a report or add parameters manually.")
    else:
        sex = st.session_state.patient_info.get('sex', 'Default')

        # Ensure analysis is run
        if not st.session_state.analysis:
            st.session_state.analysis = analyze_all_parameters(st.session_state.parameters, sex)

        st.markdown("""
        <div class="info-alert">
            <strong>ℹ️ About AI Review:</strong> The AI review uses Claude to provide a comprehensive 
            analysis including pattern recognition, differential diagnoses, recommended investigations, 
            and clinical correlation. This is for educational purposes only.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🤖 Generate AI Review", type="primary", use_container_width=True):
            with st.spinner("🔄 Generating comprehensive AI review... This may take a moment."):
                ai_text = get_ai_review(
                    st.session_state.parameters,
                    st.session_state.analysis,
                    st.session_state.patient_info,
                    api_key
                )
                st.session_state.ai_review_text = ai_text

        if st.session_state.ai_review_text:
            if st.session_state.ai_review_text.startswith('Error'):
                st.error(st.session_state.ai_review_text)
            else:
                st.markdown("---")
                st.subheader("📝 AI Clinical Review")
                st.markdown(st.session_state.ai_review_text)

                # Copy button
                st.markdown("---")
                st.download_button(
                    label="📋 Download AI Review as Text",
                    data=st.session_state.ai_review_text,
                    file_name=f"ai_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

# =============================================
# TAB 6: REPORT
# =============================================
with tab6:
    st.header("📄 Generate & Download Report")

    if not st.session_state.parameters:
        st.warning("⚠️ No parameters available. Please upload a report or add parameters first.")
    else:
        sex = st.session_state.patient_info.get('sex', 'Default')

        # Ensure analysis is run
        if not st.session_state.analysis:
            st.session_state.analysis = analyze_all_parameters(st.session_state.parameters, sex)

        st.markdown("""
        <div class="info-alert">
            <strong>📄 Report Options:</strong>
            <ul>
                <li><strong>Text Summary:</strong> Quick text summary of findings</li>
                <li><strong>PDF Report:</strong> Comprehensive formatted report with all findings</li>
                <li><strong>PDF with AI Review:</strong> Full report including AI-generated clinical analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Report Options
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📝 Text Summary")
            if st.button("Generate Text Summary", use_container_width=True):
                summary = generate_summary_text(st.session_state.analysis, st.session_state.patient_info)
                st.text_area("Summary", summary, height=400)
                st.download_button(
                    label="📥 Download Text Summary",
                    data=summary,
                    file_name=f"blood_analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        with col2:
            st.subheader("📄 PDF Report")
            if st.button("Generate PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_bytes = generate_pdf_report(
                            st.session_state.analysis,
                            st.session_state.patient_info,
                            ai_review=None
                        )
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"blood_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("✅ PDF generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")

        with col3:
            st.subheader("📄 PDF + AI Review")
            if st.session_state.ai_review_text and not st.session_state.ai_review_text.startswith('Error'):
                if st.button("Generate Full PDF with AI", type="primary", use_container_width=True):
                    with st.spinner("Generating comprehensive PDF..."):
                        try:
                            pdf_bytes = generate_pdf_report(
                                st.session_state.analysis,
                                st.session_state.patient_info,
                                ai_review=st.session_state.ai_review_text
                            )
                            st.download_button(
                                label="📥 Download Full PDF Report",
                                data=pdf_bytes,
                                file_name=f"blood_analysis_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ Full PDF generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
            else:
                st.info("Generate an AI review first (in the AI Review tab) to include it in the PDF.")

        # Data Export Options
        st.markdown("---")
        st.subheader("📊 Data Export")

        col_a, col_b = st.columns(2)

        with col_a:
            # Export as CSV
            if st.session_state.analysis:
                csv_data = []
                for param_name, param_data in st.session_state.analysis['parameters'].items():
                    classification = param_data.get('classification', {})
                    csv_data.append({
                        'Parameter': param_name,
                        'Value': param_data.get('value', ''),
                        'Unit': param_data.get('unit', ''),
                        'Status': classification.get('status', ''),
                        'Reference Low': classification.get('low', ''),
                        'Reference High': classification.get('high', ''),
                    })

                if csv_data:
                    csv_df = pd.DataFrame(csv_data)
                    csv_buffer = csv_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_buffer,
                        file_name=f"blood_parameters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        with col_b:
            # Export as JSON
            if st.session_state.analysis:
                export_data = {
                    'patient_info': st.session_state.patient_info,
                    'parameters': {},
                    'summary': {
                        'total_parameters': st.session_state.analysis['total_parameters'],
                        'abnormal_count': st.session_state.analysis['abnormal_count'],
                        'critical_count': st.session_state.analysis['critical_count'],
                    },
                    'generated_at': datetime.now().isoformat()
                }

                for param_name, param_data in st.session_state.analysis['parameters'].items():
                    classification = param_data.get('classification', {})
                    export_data['parameters'][param_name] = {
                        'value': param_data.get('value'),
                        'unit': param_data.get('unit'),
                        'status': classification.get('status'),
                        'reference_low': classification.get('low'),
                        'reference_high': classification.get('high'),
                    }

                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name=f"blood_parameters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

# =============================================
# FOOTER
# =============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #95a5a6; font-size: 0.85em; padding: 20px;">
    <strong>⚠️ Disclaimer:</strong> This application is designed as an educational and learning tool only. 
    It is NOT intended for clinical decision-making, diagnosis, or treatment. 
    All blood investigation results should be interpreted by qualified medical professionals 
    in the context of the patient's clinical condition.<br><br>
    Built with Streamlit | Powered by Claude AI | © 2024 Hematology Analysis Tool
</div>
""", unsafe_allow_html=True)
