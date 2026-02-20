"""
PDF Report Generator
Creates downloadable PDF reports of blood investigation analysis.
"""

import io
from datetime import datetime
from typing import Dict, Optional
from fpdf import FPDF


class HematologyReport(FPDF):
    """Custom PDF class for hematology reports."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'Hematology Blood Investigation Analysis Report', 0, 1, 'C')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.cell(0, 5, 'DISCLAIMER: For educational purposes only. Not for clinical decision-making.', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def safe_text(self, text: str) -> str:
        """Safely encode text for PDF output."""
        if text is None:
            return ''
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    def section_title(self, title: str):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(41, 128, 185)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f'  {self.safe_text(title)}', 0, 1, 'L', fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def sub_section_title(self, title: str):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(214, 234, 248)
        self.cell(0, 7, f'  {self.safe_text(title)}', 0, 1, 'L', fill=True)
        self.ln(1)

    def add_parameter_row(self, param: str, value, unit: str, status: str, ref_range: str):
        self.set_font('Helvetica', '', 9)

        status_lower = str(status).lower()
        if 'critical' in status_lower:
            self.set_fill_color(255, 200, 200)
        elif status_lower in ['low', 'high']:
            self.set_fill_color(255, 235, 200)
        elif status_lower == 'normal':
            self.set_fill_color(200, 255, 200)
        else:
            self.set_fill_color(240, 240, 240)

        col_widths = [45, 30, 25, 35, 55]
        row_data = [
            self.safe_text(str(param)),
            self.safe_text(str(value)),
            self.safe_text(str(unit)),
            self.safe_text(str(status).upper()),
            self.safe_text(str(ref_range))
        ]

        for data, width in zip(row_data, col_widths):
            self.cell(width, 6, data, 1, 0, 'C', fill=True)
        self.ln()


def generate_pdf_report(analysis: Dict, patient_info: Dict,
                        ai_review: Optional[str] = None) -> bytes:
    """Generate a complete PDF report."""
    pdf = HematologyReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ---- PATIENT INFORMATION ----
    if patient_info:
        pdf.section_title('PATIENT INFORMATION')
        pdf.set_font('Helvetica', '', 10)
        for key, value in patient_info.items():
            if value:
                pdf.cell(40, 6, f'{key.capitalize()}:', 0, 0)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 6, pdf.safe_text(str(value)), 0, 1)
                pdf.set_font('Helvetica', '', 10)
        pdf.ln(3)

    # ---- SUMMARY ----
    pdf.section_title('SUMMARY')
    pdf.set_font('Helvetica', '', 10)
    summary_items = [
        ('Total Parameters Analyzed', str(analysis.get('total_parameters', 0))),
        ('Abnormal Values', str(analysis.get('abnormal_count', 0))),
        ('Critical Values', str(analysis.get('critical_count', 0))),
    ]
    for label, val in summary_items:
        pdf.cell(60, 6, f'{label}:', 0, 0)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, val, 0, 1)
        pdf.set_font('Helvetica', '', 10)
    pdf.ln(3)

    # ---- CRITICAL VALUES ----
    if analysis.get('critical_values'):
        pdf.section_title('CRITICAL VALUES ALERT')
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(200, 0, 0)
        for cv in analysis['critical_values']:
            msg = pdf.safe_text(cv.get('message', ''))
            pdf.cell(0, 6, f"  >> {cv['parameter']}: {msg}", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    # ---- QUALITY ASSESSMENT ----
    pdf.section_title('SAMPLE QUALITY ASSESSMENT')
    for check in analysis.get('quality_checks', []):
        severity = check.get('severity', 'info')
        color_map = {
            'pass': (200, 255, 200), 'error': (255, 200, 200),
            'warning': (255, 235, 200), 'info': (214, 234, 248)
        }
        r, g, b = color_map.get(severity, (214, 234, 248))
        pdf.set_fill_color(r, g, b)

        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, pdf.safe_text(f"[{severity.upper()}] {check['rule']}"), 0, 1, fill=True)

        pdf.set_font('Helvetica', '', 8)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(0, 4, pdf.safe_text(f"    Expected: {check.get('expected', 'N/A')}"), 0, 1)
        pdf.cell(0, 4, pdf.safe_text(f"    Actual: {check.get('actual', 'N/A')}"), 0, 1)

        pdf.set_font('Helvetica', 'I', 8)
        interp = pdf.safe_text(check.get('interpretation', ''))
        pdf.multi_cell(0, 4, f"    {interp}")
        pdf.ln(2)

    # ---- PARAMETER RESULTS TABLE ----
    pdf.add_page()
    pdf.section_title('DETAILED PARAMETER RESULTS')

    # Table header
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    col_widths = [45, 30, 25, 35, 55]
    headers = ['Parameter', 'Value', 'Unit', 'Status', 'Reference Range']
    for header, width in zip(headers, col_widths):
        pdf.cell(width, 7, header, 1, 0, 'C', fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    for param_name, param_data in analysis.get('parameters', {}).items():
        classification = param_data.get('classification', {})
        ref_low = classification.get('low')
        ref_high = classification.get('high')
        ref_range = f'{ref_low} - {ref_high}' if ref_low is not None and ref_high is not None else 'N/A'

        pdf.add_parameter_row(
            param_name,
            param_data.get('value', 'N/A'),
            pdf.safe_text(str(param_data.get('unit', ''))),
            classification.get('status', 'unknown'),
            pdf.safe_text(str(ref_range))
        )
    pdf.ln(5)

    # ---- CALCULATED INDICES ----
    if analysis.get('calculated_indices'):
        pdf.section_title('CALCULATED INDICES')
        for idx_name, idx_data in analysis['calculated_indices'].items():
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(55, 6, f'{idx_name}:', 0, 0)
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(25, 6, str(idx_data.get('value', '')), 0, 0)
            pdf.cell(0, 6, pdf.safe_text(str(idx_data.get('interpretation', ''))), 0, 1)
            pdf.set_font('Helvetica', 'I', 7)
            formula = pdf.safe_text(str(idx_data.get('formula', '')))
            note = pdf.safe_text(str(idx_data.get('note', '')))
            pdf.cell(0, 4, f'    Formula: {formula} | Note: {note}', 0, 1)
            pdf.ln(1)
        pdf.ln(3)

    # ---- DIFFERENTIAL DIAGNOSES ----
    if analysis.get('abnormalities'):
        pdf.add_page()
        pdf.section_title('DIFFERENTIAL DIAGNOSES')

        for abn in analysis['abnormalities']:
            param = abn.get('parameter', 'Unknown')
            classification = abn.get('classification', {})
            differential = abn.get('differential')

            status_text = classification.get('status', '').upper()
            pdf.sub_section_title(f'{param} - {status_text}')

            pdf.set_font('Helvetica', '', 9)
            msg = pdf.safe_text(str(classification.get('message', '')))
            pdf.cell(0, 5, f'  Finding: {msg}', 0, 1)
            pdf.ln(1)

            if differential:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 6, pdf.safe_text(f"  {differential.get('title', '')}"), 0, 1)

                for i, d in enumerate(differential.get('differentials', []), 1):
                    condition = pdf.safe_text(str(d.get('condition', '')))
                    discussion = pdf.safe_text(str(d.get('discussion', '')))

                    pdf.set_font('Helvetica', 'B', 8)
                    pdf.cell(0, 5, f'    {i}. {condition}', 0, 1)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(0, 4, f'       {discussion}')
                    pdf.ln(1)

            pdf.ln(3)

    # ---- AI REVIEW ----
    if ai_review and not ai_review.startswith('Error'):
        pdf.add_page()
        pdf.section_title('AI-POWERED CLINICAL REVIEW (Claude AI)')

        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, 'Note: AI analysis is for educational reference only.', 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        lines = ai_review.split('\n')
        for line in lines:
            clean_line = pdf.safe_text(line.strip())
            if not clean_line:
                pdf.ln(2)
                continue

            if clean_line.startswith('**') or clean_line.startswith('##'):
                heading = clean_line.replace('**', '').replace('##', '').strip()
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_fill_color(236, 240, 241)
                pdf.cell(0, 7, f'  {heading}', 0, 1, fill=True)
                pdf.ln(1)
            elif any(clean_line.startswith(f'{i}.') for i in range(1, 20)):
                pdf.set_font('Helvetica', 'B', 9)
                pdf.multi_cell(0, 5, clean_line)
            elif clean_line.startswith('-') or clean_line.startswith('*'):
                pdf.set_font('Helvetica', '', 8)
                bullet_text = clean_line.lstrip('-*').strip()
                pdf.cell(5, 4, '', 0, 0)
                pdf.multi_cell(0, 4, f'  - {bullet_text}')
            else:
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 4, clean_line)

    # ---- DISCLAIMERS ----
    pdf.add_page()
    pdf.section_title('IMPORTANT DISCLAIMERS')
    pdf.set_font('Helvetica', '', 9)

    disclaimers = [
        "1. This report is for EDUCATIONAL and LEARNING purposes only.",
        "",
        "2. NOT intended for clinical decision-making, diagnosis, or treatment.",
        "",
        "3. All results should be interpreted by a qualified physician or hematologist.",
        "",
        "4. Reference ranges may vary between laboratories and instruments.",
        "",
        "5. AI-generated review may contain inaccuracies.",
        "",
        "6. Critical values require immediate clinical correlation.",
        "",
        "7. Quality checks do not replace proper laboratory QC procedures.",
        "",
        "8. Always verify extracted values against the original laboratory report.",
    ]

    for disclaimer in disclaimers:
        pdf.multi_cell(0, 5, pdf.safe_text(disclaimer))

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, pdf.safe_text(f'Report generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'), 0, 1, 'C')

    # Output bytes
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
