"""
AI Review Module using Claude API.
Provides comprehensive AI-powered analysis for CBC and LFT.
"""

import os
from typing import Dict, Optional
import anthropic

# Add this function to the existing ai_review.py

def get_panel_ai_review(all_analyses: Dict, patient_info: Dict, api_key: str) -> Optional[str]:
    """Get AI review across multiple panels."""
    if not api_key:
        return "Error: Claude API key not provided."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        parts = ["Provide a comprehensive clinical review of the following multi-panel laboratory results.\n"]
        
        if patient_info:
            parts.append("PATIENT INFO:")
            for k, v in patient_info.items():
                parts.append(f"  {k}: {v}")
            parts.append("")
        
        for panel_name, analysis in all_analyses.items():
            parts.append(f"\n{'='*40}\n{panel_name} RESULTS:\n{'='*40}")
            for pname, pdata in analysis.get('parameters', {}).items():
                c = pdata.get('classification', {})
                parts.append(f"  {pname}: {pdata.get('value','')} {pdata.get('unit','')} [{c.get('status','').upper()}]")
            if analysis.get('calculated_indices'):
                parts.append("  Calculated Indices:")
                for iname, idata in analysis['calculated_indices'].items():
                    parts.append(f"    {iname}: {idata.get('value','')} — {idata.get('interpretation','')}")
            if analysis.get('pattern_summary'):
                parts.append(f"  Pattern: {analysis['pattern_summary'][:200]}")

        parts.append("""
Provide comprehensive analysis covering:
1. OVERALL CLINICAL IMPRESSION across all panels
2. CROSS-PANEL CORRELATIONS (how findings in one panel relate to another)
3. INTEGRATED DIFFERENTIAL DIAGNOSIS
4. PATTERN RECOGNITION across organ systems
5. PRIORITY FINDINGS requiring immediate attention
6. RECOMMENDED ADDITIONAL INVESTIGATIONS
7. CLINICAL CORRELATION POINTS
8. MONITORING PLAN

Include educational pearls and disclaimer.""")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": "\n".join(parts)}],
            system="You are an expert clinical pathologist reviewing multi-panel laboratory results. "
                   "Provide integrated analysis emphasizing cross-panel correlations and pattern recognition. "
                   "Include educational content. Disclaimer for educational purposes."
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"
def get_ai_review(parameters: Dict, analysis: Dict, patient_info: Dict, api_key: str) -> Optional[str]:
    """Get comprehensive AI review of CBC findings using Claude."""
    if not api_key:
        return "Error: Claude API key not provided. Please enter your API key in the sidebar."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = build_cbc_review_prompt(parameters, analysis, patient_info)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system=(
                "You are an expert hematologist and clinical pathologist. Provide a comprehensive, "
                "structured analysis of the blood investigation results. Use medical terminology appropriately "
                "but explain concepts clearly. Structure your response with clear headings and numbered points. "
                "Always include a disclaimer that this is for educational purposes only."
            )
        )
        return message.content[0].text

    except anthropic.AuthenticationError:
        return "Error: Invalid API key. Please check your Claude API key."
    except anthropic.RateLimitError:
        return "Error: API rate limit reached. Please try again in a few moments."
    except Exception as e:
        return f"Error generating AI review: {str(e)}"


def build_cbc_review_prompt(parameters: Dict, analysis: Dict, patient_info: Dict) -> str:
    """Build a detailed prompt for CBC AI review."""
    parts = ["Please provide a comprehensive hematology review of the following blood investigation results.\n"]

    if patient_info:
        parts.append("PATIENT INFORMATION:")
        for k, v in patient_info.items():
            parts.append(f"  - {k.capitalize()}: {v}")
        parts.append("")

    parts.append("BLOOD INVESTIGATION RESULTS:")
    parts.append("-" * 40)
    for param_name, param_data in analysis.get('parameters', {}).items():
        value = param_data.get('value', 'N/A')
        unit = param_data.get('unit', '')
        c = param_data.get('classification', {})
        status = c.get('status', 'unknown')
        ref_low = c.get('low', '')
        ref_high = c.get('high', '')
        parts.append(f"  {param_name}: {value} {unit} [{status.upper()}] (Ref: {ref_low}-{ref_high})")

    parts.append("\nQUALITY ASSESSMENT FINDINGS:")
    for check in analysis.get('quality_checks', []):
        parts.append(f"  - {check['rule']}: {check['severity'].upper()} — {check['interpretation']}")

    if analysis.get('calculated_indices'):
        parts.append("\nCALCULATED INDICES:")
        for idx_name, idx_data in analysis['calculated_indices'].items():
            parts.append(f"  - {idx_name}: {idx_data['value']} ({idx_data['interpretation']})")

    if analysis.get('abnormalities'):
        parts.append(f"\nABNORMAL PARAMETERS: {len(analysis['abnormalities'])}")
        parts.append(f"CRITICAL VALUES: {analysis.get('critical_count', 0)}")

    parts.append("""
Please provide your analysis covering:
1. **OVERALL IMPRESSION**
2. **SAMPLE QUALITY ASSESSMENT**
3. **RED BLOOD CELL ANALYSIS** (RBC, Hb, HCT, indices, differential diagnoses)
4. **WHITE BLOOD CELL ANALYSIS** (total WBC, differential, abnormalities)
5. **PLATELET ANALYSIS** (count, MPV, significance)
6. **PATTERN RECOGNITION** (pancytopenia, iron deficiency pattern, etc.)
7. **DIFFERENTIAL DIAGNOSIS** (top 3-5, ranked by likelihood)
8. **RECOMMENDED ADDITIONAL INVESTIGATIONS**
9. **CLINICAL CORRELATION**
10. **SUMMARY AND CONCLUSIONS**

Include a disclaimer for educational purposes.
""")
    return "\n".join(parts)


def get_parameter_specific_ai_review(param_name: str, param_value: float, param_unit: str,
                                      classification: Dict, api_key: str) -> Optional[str]:
    """Get AI review for a specific CBC parameter."""
    if not api_key:
        return "Error: Claude API key not provided."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""As an expert hematologist, provide a focused analysis of this blood parameter:

Parameter: {param_name}
Value: {param_value} {param_unit}
Status: {classification.get('status', 'unknown').upper()}
Reference Range: {classification.get('low', 'N/A')} - {classification.get('high', 'N/A')} {param_unit}

Please discuss:
1. What this parameter measures and clinical significance
2. Measurement methodology (impedance, optical, fluorescence)
3. Possible causes of this abnormality (if abnormal)
4. Key differential diagnoses
5. Recommended follow-up tests
6. Common artifacts or spurious causes
7. Clinical correlation points

Include disclaimer for educational use."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert hematologist. Provide concise, clinically relevant analysis."
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


def get_lft_ai_review(labs: Dict, analysis: Dict, clinical: Dict, api_key: str) -> Optional[str]:
    """Get comprehensive AI review of LFT findings using Claude."""
    if not api_key:
        return "Error: Claude API key not provided."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = build_lft_review_prompt(labs, analysis, clinical)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system=(
                "You are an expert hepatologist and clinical pathologist. Provide a comprehensive, "
                "structured analysis of the liver function test results. Use a systematic approach: "
                "pattern recognition, severity assessment, differential diagnosis, and recommendations. "
                "Always include a disclaimer for educational purposes."
            )
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


def build_lft_review_prompt(labs: Dict, analysis: Dict, clinical: Dict) -> str:
    """Build prompt for LFT AI review."""
    parts = ["Please provide a comprehensive hepatology review of the following LFT results.\n"]

    parts.append("CLINICAL INFORMATION:")
    parts.append(f"  Age: {clinical.get('age', 'N/A')}")
    parts.append(f"  Sex: {clinical.get('sex', 'N/A')}")
    parts.append(f"  Reason for testing: {clinical.get('reason', 'N/A')}")
    parts.append(f"  Shock/hemodynamic instability: {clinical.get('shock', 'no')}")
    parts.append(f"  Biliary symptoms: {clinical.get('biliary', 'no')}")
    parts.append(f"  Acute liver injury signs: {clinical.get('acute_injury', 'no')}")
    parts.append(f"  Suspected hemolysis: {clinical.get('hemolysis', 'no')}")
    parts.append("")

    parts.append("LABORATORY VALUES:")
    for k, v in labs.items():
        if v is not None and v != 0:
            parts.append(f"  {k}: {v}")
    parts.append("")

    parts.append("AUTOMATED ANALYSIS:")
    parts.append(f"  R Value: {analysis.get('r_value', 'N/A')}")
    parts.append(f"  Pattern: {analysis.get('pattern', 'N/A')}")
    parts.append(f"  Severity: {analysis.get('severity', {}).get('grade', 'N/A')}")
    parts.append(f"  AST/ALT Ratio: {analysis.get('ast_alt_ratio', 'N/A')}")
    parts.append(f"  Pathway: {analysis.get('pathway', 'N/A')}")
    parts.append(f"  Synthetic impairment: {analysis.get('synthetic_impaired', False)}")
    parts.append("")

    parts.append("""
Please provide your analysis covering:
1. **OVERALL IMPRESSION** of the LFT pattern
2. **PATTERN CLASSIFICATION** with R value interpretation
3. **SEVERITY ASSESSMENT** and prognostic implications
4. **DIFFERENTIAL DIAGNOSIS** (ranked by likelihood based on all available data)
5. **SYNTHETIC FUNCTION ASSESSMENT** (albumin, PT/INR)
6. **AST/ALT RATIO INTERPRETATION** and significance
7. **RECOMMENDED WORKUP** (specific tests, imaging, biopsies)
8. **URGENT CONSIDERATIONS** (any findings requiring immediate action)
9. **MONITORING PLAN** (follow-up timeline and parameters)
10. **EDUCATIONAL PEARLS** for learners

Include disclaimer for educational purposes only.
""")
    return "\n".join(parts)
