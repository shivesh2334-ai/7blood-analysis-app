"""
Blood Analysis App - Streamlit application for extracting and analyzing blood reports.
"""

import streamlit as st
from utils.ocr_parser import process_uploaded_file
from utils.analysis_engine import analyze_all_parameters, generate_summary_text

st.set_page_config(page_title="Blood Analysis App", page_icon="🩸", layout="wide")
st.title("🩸 Blood Investigation Analysis Tool")

tab_upload, tab_analysis = st.tabs(["Upload & Extract", "Analysis"])

# ─── Session state ────────────────────────────────────────────────────────────
if "parameters" not in st.session_state:
    st.session_state.parameters = {}
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {}
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ─── Upload & Extract Tab ─────────────────────────────────────────────────────
with tab_upload:
    st.header("Upload Blood Report")
    uploaded_file = st.file_uploader(
        "Upload a blood report (PDF, JPG, PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
    )

    if uploaded_file is not None:
        with st.spinner("Extracting data from file…"):
            try:
                # Unpack all 5 return values from process_uploaded_file
                extracted_text, parameters, patient_info, parsing_steps, quality_metrics = (
                    process_uploaded_file(uploaded_file)
                )

                # Persist results in session state
                # Convert ParsedValue objects to plain dicts for the analysis engine
                st.session_state.parameters = {
                    name: {"value": pv.value, "unit": pv.unit}
                    for name, pv in parameters.items()
                }
                st.session_state.patient_info = patient_info
                st.session_state.extracted_text = extracted_text

                st.success("File processed successfully!")

                # ── Quality Metrics ────────────────────────────────────────
                st.subheader("Parsing Quality")
                metrics = quality_metrics.to_dict()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Parameters Found", metrics["total_parameters_found"])
                col2.metric("Reliable", metrics["reliable_parameters"])
                col3.metric("Questionable", metrics["questionable_parameters"])
                col4.metric(
                    "Avg Confidence",
                    f"{metrics['average_confidence'] * 100:.0f}%",
                )
                st.caption(f"Parsing success rate: {metrics['parsing_success_rate']}")

                # ── Extracted Parameters ───────────────────────────────────
                if parameters:
                    st.subheader("Extracted Parameters")
                    for name, pv in parameters.items():
                        status_icon = (
                            "✅" if pv.validation_status == "valid"
                            else "⚠️" if pv.validation_status == "questionable"
                            else "❌"
                        )
                        st.write(
                            f"{status_icon} **{name}**: {pv.value} {pv.unit} "
                            f"(confidence: {pv.confidence_score * 100:.0f}%)"
                        )
                else:
                    st.warning("No blood parameters could be extracted from the file.")

                # ── Patient Info ───────────────────────────────────────────
                if patient_info:
                    st.subheader("Patient Information")
                    for key, value in patient_info.items():
                        st.write(f"**{key.capitalize()}**: {value}")

                # ── Parsing Steps (debug) ──────────────────────────────────
                with st.expander("Parsing Steps (debug)"):
                    for step in parsing_steps:
                        step_dict = step.to_dict()
                        st.write(
                            f"**{step_dict['step_name']}** — {step_dict['status'].upper()}: "
                            f"found {step_dict['items_found']} item(s)"
                        )
                        if step_dict["errors"]:
                            for err in step_dict["errors"]:
                                st.error(err)
                        if step_dict["warnings"]:
                            for warn in step_dict["warnings"]:
                                st.warning(warn)

                # ── Raw Extracted Text ─────────────────────────────────────
                with st.expander("Raw Extracted Text"):
                    st.text(extracted_text if extracted_text else "(no text extracted)")

            except Exception as e:
                st.error(f"An error occurred while processing the file: {e}")

    # ── Manual Parameter Entry ─────────────────────────────────────────────────
    st.subheader("Manual Parameter Entry")
    st.caption("Add or override individual parameters below.")
    col_name, col_value, col_unit, col_add = st.columns([3, 2, 2, 1])
    with col_name:
        manual_name = st.text_input("Parameter name", key="manual_name", label_visibility="collapsed", placeholder="e.g. Hemoglobin")
    with col_value:
        manual_value = st.number_input("Value", key="manual_value", label_visibility="collapsed", min_value=0.0, value=0.0, format="%.2f")
    with col_unit:
        manual_unit = st.text_input("Unit", key="manual_unit", label_visibility="collapsed", placeholder="e.g. g/dL")
    with col_add:
        if st.button("Add"):
            if manual_name:
                st.session_state.parameters[manual_name] = {"value": manual_value, "unit": manual_unit}
                st.success(f"Added {manual_name}.")
            else:
                st.warning("Please enter a parameter name.")

# ─── Analysis Tab ─────────────────────────────────────────────────────────────
with tab_analysis:
    st.header("Analysis")
    if not st.session_state.parameters:
        st.info("Upload a file or add parameters manually in the 'Upload & Extract' tab.")
    else:
        patient_info = st.session_state.patient_info
        sex = patient_info.get("sex", "Default")

        analysis = analyze_all_parameters(st.session_state.parameters, sex=sex)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Parameters", analysis["total_parameters"])
        col_b.metric("Abnormal", analysis["abnormal_count"])
        col_c.metric("Critical", analysis["critical_count"])

        if analysis["critical_values"]:
            st.error("⚠️ Critical values detected:")
            for cv in analysis["critical_values"]:
                st.write(f"- **{cv['parameter']}**: {cv['value']} — {cv['message']}")

        st.subheader("Parameter Results")
        for param, data in analysis["parameters"].items():
            classification = data["classification"]
            status = classification.get("status", "unknown")
            status_icon = (
                "🟢" if status == "normal"
                else "🔴" if "critical" in status
                else "🟡"
            )
            st.write(
                f"{status_icon} **{param}**: {data['value']} {data['unit']} — "
                f"{classification.get('message', '')}"
            )

        if analysis.get("calculated_indices"):
            st.subheader("Calculated Indices")
            for idx_name, idx_data in analysis["calculated_indices"].items():
                st.write(f"**{idx_name}**: {idx_data.get('value', '')} — {idx_data.get('interpretation', '')}")

        summary = generate_summary_text(analysis, patient_info)
        with st.expander("Full Report Text"):
            st.text(summary)