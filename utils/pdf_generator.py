"""
PDF Report Generator — creates downloadable PDF reports.
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
        self.cell(0, 10, 'Blood Investigation Analysis Report', 0, 1, 'C')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.cell(0, 5, 'DISCLAIMER: For educational purposes only. Not for clinical decision-making.', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def section_title(self, title: str):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(41, 128, 185)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f'  {self._clean(title)}', 0, 1, 'L', fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def sub_section_title(self, title: str):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(214, 234, 248)
        self.cell(0, 7, f'  {self._clean(title)}', 0, 1, 'L', fill=True)
        self.ln(1)

    def add_parameter_row(self, param: str, value, unit: str, status: str, ref_range: str):
        self.set_font('Helvetica', '', 9)
        if 'critical' in status.lower():
            self.set_fill_color(255, 200, 200)
        elif status.lower() in ('low', 'high'):
            self.set_fill_color(255, 235, 200)
        else:
            self.set_fill_color(200, 255, 200)

        col_widths = [45, 30, 25, 35, 55]
        row_data = [param, str(value), self._clean(unit), status.upper(), self._clean(ref_range)]
        for data, width in zip(row_data, col_widths):
            self.cell(width, 6, str(data)[:25], 1, 0, 'C', fill=True)
        self.ln()

    def add_wrapped_text(self, text: str, font_size: int = 9):
        self.set_font('Helvetica', '', font_size)
        self.multi_cell(0, 5, self._clean(text))
        self.ln(1)

    @staticmethod
    def _clean(text: str) -> str:
        """Clean text for latin-1 encoding."""
        if text is None:
            return ''
        return str(text).encode('latin-1', 'replace').decode('latin-1')


def generate_pdf_report(analysis: Dict, patient_info: Dict,
                        ai_review: Optional[str] = None) -> bytes:
    """Generate a complete PDF report and return bytes."""
    pdf = HematologyReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    _clean = HematologyReport._clean

    # ── Patient Information ──────────────────────────────
    if patient_info:
        pdf.section_title('PATIENT INFORMATION')
        pdf.set_font('Helvetica', '', 10)
        for key, value in patient_info.items():
            pdf.cell(40, 6, f'{key.capitalize()}:', 0, 0)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, _clean(str(value)), 0, 1)
            pdf.set_font('Helvetica', '', 10)
        pdf.ln(3)

    # ── Summary ──────────────────────────────────────────
    pdf.section_title('SUMMARY')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(60, 6, 'Total Parameters Analyzed:', 0, 0)
    pdf.cell(0, 6, str(analysis.get('total_parameters', 0)), 0, 1)
    pdf.cell(60, 6, 'Abnormal Values:', 0, 0)
    pdf.cell(0, 6, str(analysis.get('abnormal_count', 0)), 0, 1)
    pdf.cell(60, 6, 'Critical Values:', 0, 0)
    pdf.cell(0, 6, str(analysis.get('critical_count', 0)), 0, 1)
    pdf.ln(3)

    # ── Critical Values Alert ────────────────────────────
    if analysis.get('critical_values'):
        pdf.section_title('CRITICAL VALUES ALERT')
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(255, 0, 0)
        for cv in analysis['critical_values']:
            pdf.cell(0, 6, _clean(f"  {cv['parameter']}: {cv['message']}"), 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    # ── Quality Assessment ───────────────────────────────
    pdf.section_title('SAMPLE QUALITY ASSESSMENT')
    for check in analysis.get('quality_checks', []):
        severity = check.get('severity', 'info')
        colors = {'pass': (200, 255, 200), 'error': (255, 200, 200),
                  'warning': (255, 235, 200), 'info': (214, 234, 248)}
        r, g, b = colors.get(severity, (214, 234, 248))
        pdf.set_fill_color(r, g, b)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, _clean(f"[{severity.upper()}] {check['rule']}"), 0, 1, fill=True)
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, _clean(f"  {check.get('interpretation', '')}"))
        pdf.ln(2)

    # ── Parameter Results Table ──────────────────────────
    pdf.add_page()
    pdf.section_title('DETAILED PARAMETER RESULTS')
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    col_widths = [45, 30, 25, 35, 55]
    headers = ['Parameter', 'Value', 'Unit', 'Status', 'Reference Range']
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, 1, 0, 'C', fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    for param_name, param_data in analysis.get('parameters', {}).items():
        c = param_data.get('classification', {})
        ref_low = c.get('low', '')
        ref_high = c.get('high', '')
        ref_range = f'{ref_low} - {ref_high}' if ref_low is not None else 'N/A'
        pdf.add_parameter_row(
            param_name, param_data.get('value', 'N/A'),
            str(param_data.get('unit', '')),
            c.get('status', 'unknown'),
            str(ref_range)
        )
    pdf.ln(5)

    # ── Calculated Indices ───────────────────────────────
    if analysis.get('calculated_indices'):
        pdf.section_title('CALCULATED INDICES')
        for idx_name, idx_data in analysis['calculated_indices'].items():
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(50, 6, f'{idx_name}:', 0, 0)
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(30, 6, str(idx_data['value']), 0, 0)
            pdf.cell(0, 6, _clean(str(idx_data.get('interpretation', ''))), 0, 1)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.cell(0, 4, _clean(f'  ({idx_data.get("note", "")})'), 0, 1)
        pdf.ln(3)

    # ── Differential Diagnoses ───────────────────────────
    if analysis.get('abnormalities'):
        pdf.add_page()
        pdf.section_title('DIFFERENTIAL DIAGNOSES')
        for abn in analysis['abnormalities']:
            param = abn['parameter']
            classification = abn['classification']
            differential = abn.get('differential')

            pdf.sub_section_title(f'{param} - {classification.get("status", "").upper()}')
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 5, _clean(f'  Value: {classification.get("message", "")}'), 0, 1)

            if differential:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 6, _clean(f'  {differential.get("title", "")}'), 0, 1)
                pdf.set_font('Helvetica', '', 8)
                for i, d in enumerate(differential.get('differentials', []), 1):
                    pdf.set_font('Helvetica', 'B', 8)
                    pdf.cell(0, 5, _clean(f'    {i}. {d.get("condition", "")}'), 0, 1)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(0, 4, _clean(f'       {d.get("discussion", "")}'))
                    pdf.ln(1)
            pdf.ln(3)

    # ── AI Review ────────────────────────────────────────
    if ai_review:
        pdf.add_page()
        pdf.section_title('AI-POWERED CLINICAL REVIEW (Claude)')
        pdf.set_font('Helvetica', '', 9)
        # Split into paragraphs for better formatting
        paragraphs = ai_review.split('\n')
        for para in paragraphs:
            para = para.strip()
            if not para:
                pdf.ln(3)
                continue
            if para.startswith('**') or para.startswith('#'):
                pdf.set_font('Helvetica', 'B', 10)
                clean_para = para.replace('**', '').replace('#', '').strip()
                pdf.multi_cell(0, 5, _clean(clean_para))
                pdf.set_font('Helvetica', '', 9)
            else:
                pdf.multi_cell(0, 4, _clean(para))
            pdf.ln(1)

    # ── Final Disclaimer ─────────────────────────────────
    pdf.add_page()
    pdf.section_title('DISCLAIMER')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, _clean(
        'This report is generated by an automated analysis tool for educational and learning purposes only. '
        'It is NOT intended for clinical decision-making, diagnosis, or treatment of any medical condition. '
        'The information provided should not be used as a substitute for professional medical advice, '
        'diagnosis, or treatment. Always seek the advice of a qualified physician or other qualified '
        'health provider with any questions regarding a medical condition. '
        'The developers and operators of this tool assume no liability for any actions taken based on '
        'the information provided in this report.'
    ))

    # Output
    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()
