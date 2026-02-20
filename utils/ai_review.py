"""
AI Review Module using Claude API
Provides comprehensive AI-powered analysis of blood investigation results.
"""

import os
from typing import Dict, Optional
import anthropic


def get_ai_review(parameters: Dict, analysis: Dict, patient_info: Dict, api_key: str) -> Optional[str]:
    """Get comprehensive AI review of blood investigation findings using Claude."""
    if not api_key:
        return "Error: Claude API key not provided. Please enter your API key in the sidebar."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = build_review_prompt(parameters, analysis, patient_info)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert hematologist and clinical pathologist. Provide a comprehensive, "
                   "structured analysis of the blood investigation results. Use medical terminology appropriately "
                   "but explain concepts clearly. Structure your response with clear headings and numbered points. "
                   "Always include a disclaimer that this is for educational purposes only."
        )

        return message.content[0].text

    except anthropic.AuthenticationError:
        return "Error: Invalid API key. Please check your Claude API key."
    except anthropic.RateLimitError:
        return "Error: API rate limit reached. Please try again in a few moments."
    except Exception as e:
        return f"Error generating AI review: {str(e)}"


def build_review_prompt(parameters: Dict, analysis: Dict, patient_info: Dict) -> str:
    """Build a detailed prompt for AI review."""
    prompt_parts = []
    prompt_parts.append("Please provide a comprehensive hematology review of the following blood investigation results.\n")

    if patient_info:
        prompt_parts.append("PATIENT INFORMATION:")
        for key, value in patient_info.items():
            if value:
                prompt_parts.append(f"  - {key.capitalize()}: {value}")
        prompt_parts.append("")

    prompt_parts.append("BLOOD INVESTIGATION RESULTS:")
    prompt_parts.append("-" * 40)

    for param_name, param_data in analysis.get('parameters', {}).items():
        value = param_data.get('value', 'N/A')
        unit = param_data.get('unit', '')
        classification = param_data.get('classification', {})
        status = classification.get('status', 'unknown')
        ref_low = classification.get('low', '')
        ref_high = classification.get('high', '')
        prompt_parts.append(f"  {param_name}: {value} {unit} [{status.upper()}] (Ref: {ref_low}-{ref_high})")

    prompt_parts.append("")

    prompt_parts.append("QUALITY ASSESSMENT FINDINGS:")
    for check in analysis.get('quality_checks', []):
        prompt_parts.append(f"  - {check['rule']}: {check['severity'].upper()} - {check['interpretation']}")
    prompt_parts.append("")

    if analysis.get('calculated_indices'):
        prompt_parts.append("CALCULATED INDICES:")
        for idx_name, idx_data in analysis['calculated_indices'].items():
            prompt_parts.append(f"  - {idx_name}: {idx_data['value']} ({idx_data['interpretation']})")
        prompt_parts.append("")

    if analysis.get('abnormalities'):
        prompt_parts.append(f"NUMBER OF ABNORMAL PARAMETERS: {len(analysis['abnormalities'])}")
        prompt_parts.append(f"NUMBER OF CRITICAL VALUES: {analysis.get('critical_count', 0)}")
        prompt_parts.append("")

    prompt_parts.append("""
Please provide your analysis in the following format:

1. **OVERALL IMPRESSION**: Brief summary of the CBC findings
2. **SAMPLE QUALITY ASSESSMENT**: Comment on reliability based on internal consistency checks
3. **RED BLOOD CELL ANALYSIS**: RBC count, hemoglobin, hematocrit, indices. Classify anemia type if present.
4. **WHITE BLOOD CELL ANALYSIS**: Total WBC and differential. Discuss abnormalities.
5. **PLATELET ANALYSIS**: Platelet count and MPV. Discuss significance.
6. **PATTERN RECOGNITION**: Identify recognizable patterns across parameters.
7. **DIFFERENTIAL DIAGNOSIS** (ranked by likelihood): Top 3-5 with reasoning.
8. **RECOMMENDED ADDITIONAL INVESTIGATIONS**: Specific tests with rationale.
9. **CLINICAL CORRELATION**: Urgent findings and relevant history to obtain.
10. **SUMMARY AND CONCLUSIONS**

Include a disclaimer that this is for educational purposes only.
""")

    return "\n".join(prompt_parts)


def get_parameter_specific_ai_review(param_name: str, param_value: float, param_unit: str,
                                      classification: Dict, api_key: str) -> Optional[str]:
    """Get AI review for a specific parameter."""
    if not api_key:
        return "Error: Claude API key not provided."

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""As an expert hematologist, provide a focused analysis of this specific blood parameter:

Parameter: {param_name}
Value: {param_value} {param_unit}
Status: {classification.get('status', 'unknown').upper()}
Reference Range: {classification.get('low', 'N/A')} - {classification.get('high', 'N/A')} {param_unit}

Please discuss:
1. What this parameter measures and its clinical significance
2. The methodology used to measure it (impedance, optical, fluorescence)
3. Possible causes of this abnormality (if abnormal)
4. Key differential diagnoses to consider
5. Recommended follow-up tests
6. Common artifacts or spurious causes to rule out
7. Clinical correlation points

Keep the response focused and clinically relevant. Include educational disclaimer."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert hematologist. Provide concise, clinically relevant analysis. "
                   "Include a brief disclaimer about educational use."
        )

        return message.content[0].text

    except Exception as e:
        return f"Error: {str(e)}"
