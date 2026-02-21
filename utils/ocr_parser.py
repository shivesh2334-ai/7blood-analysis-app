"""
OCR and Document Parsing Module.
Handles extraction of blood parameters from uploaded documents.
"""

import re
import io
from typing import Dict, Tuple
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


PARAMETER_PATTERNS = {
    'RBC': {
        'patterns': [
            r'(?:RBC|Red\s*Blood\s*Cell(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
            r'(?:Erythrocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10\u00b9\u00b2/L',
        'alt_units': ['million/\u00b5L', 'M/\u00b5L', '10^12/L']
    },
    'Hemoglobin': {
        'patterns': [
            r'(?:Hemoglobin|Haemoglobin|Hgb|Hb|HGB)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'g/dL',
        'alt_units': ['g/L', 'g/dl']
    },
    'Hematocrit': {
        'patterns': [
            r'(?:Hematocrit|Haematocrit|HCT|Hct|PCV|Packed\s*Cell\s*Volume)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'L/L']
    },
    'MCV': {
        'patterns': [r'(?:MCV|Mean\s*Corpuscular\s*Volume)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'fL', 'alt_units': ['fl', 'fL']
    },
    'MCH': {
        'patterns': [r'(?:MCH|Mean\s*Corpuscular\s*Hemoglobin|Mean\s*Corpuscular\s*Haemoglobin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pg', 'alt_units': ['pg']
    },
    'MCHC': {
        'patterns': [r'(?:MCHC|Mean\s*Corpuscular\s*(?:Hemoglobin|Haemoglobin)\s*Conc(?:entration)?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'g/dL', 'alt_units': ['g/dL', 'g/L']
    },
    'RDW': {
        'patterns': [r'(?:RDW(?:\-?CV)?|Red\s*Cell\s*Distribution\s*Width)\s*[:\-]?\s*([\d.]+)'],
        'unit': '%', 'alt_units': ['%']
    },
    'RDW_SD': {
        'patterns': [r'(?:RDW[\-\s]?SD)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'fL', 'alt_units': ['fL']
    },
    'WBC': {
        'patterns': [
            r'(?:WBC|White\s*Blood\s*Cell(?:s)?(?:\s*Count)?|Total\s*Leucocyte\s*Count|TLC)\s*[:\-]?\s*([\d.]+)',
            r'(?:Leukocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10\u2079/L', 'alt_units': ['K/\u00b5L', '10^9/L']
    },
    'Neutrophils': {
        'patterns': [
            r'(?:Neutrophil(?:s)?|NEUT|Seg(?:mented)?)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Neutrophil(?:s)?|NEUT)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'Lymphocytes': {
        'patterns': [
            r'(?:Lymphocyte(?:s)?|LYMPH|LY)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Lymphocyte(?:s)?|LYMPH|LY)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'Monocytes': {
        'patterns': [
            r'(?:Monocyte(?:s)?|MONO|MO)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Monocyte(?:s)?|MONO|MO)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'Eosinophils': {
        'patterns': [
            r'(?:Eosinophil(?:s)?|EOS|EO)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Eosinophil(?:s)?|EOS|EO)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'Basophils': {
        'patterns': [
            r'(?:Basophil(?:s)?|BASO|BA)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Basophil(?:s)?|BASO|BA)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'Platelets': {
        'patterns': [
            r'(?:Platelet(?:s)?(?:\s*Count)?|PLT|Plt)\s*[:\-]?\s*([\d.]+)',
            r'(?:Thrombocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10\u2079/L', 'alt_units': ['K/\u00b5L', '10^9/L']
    },
    'MPV': {
        'patterns': [r'(?:MPV|Mean\s*Platelet\s*Volume)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'fL', 'alt_units': ['fL']
    },
    'PDW': {
        'patterns': [r'(?:PDW|Platelet\s*Distribution\s*Width)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'fL', 'alt_units': ['fL', '%']
    },
    'Reticulocytes': {
        'patterns': [
            r'(?:Reticulocyte(?:s)?(?:\s*Count)?|RETIC|Ret)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Reticulocyte(?:s)?(?:\s*Count)?|RETIC|Ret)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%', 'alt_units': ['%']
    },
    'ESR': {
        'patterns': [r'(?:ESR|Erythrocyte\s*Sedimentation\s*Rate)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mm/hr', 'alt_units': ['mm/hr']
    },
    'ANC': {
        'patterns': [r'(?:ANC|Absolute\s*Neutrophil\s*Count)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'x10\u2079/L', 'alt_units': ['cells/\u00b5L']
    },
    'ALC': {
        'patterns': [r'(?:ALC|Absolute\s*Lymphocyte\s*Count)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'x10\u2079/L', 'alt_units': ['cells/\u00b5L']
    },
    # LFT parameters for OCR extraction
    'ALT': {
        'patterns': [r'(?:ALT|SGPT|Alanine\s*(?:Amino)?transferase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L', 'IU/L']
    },
    'AST': {
        'patterns': [r'(?:AST|SGOT|Aspartate\s*(?:Amino)?transferase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L', 'IU/L']
    },
    'ALP': {
        'patterns': [r'(?:ALP|Alkaline\s*Phosphatase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L', 'IU/L']
    },
    'Total_Bilirubin': {
        'patterns': [r'(?:Total\s*Bilirubin|T[\.\s]*Bili(?:rubin)?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mg/dL', 'umol/L']
    },
    'Direct_Bilirubin': {
        'patterns': [r'(?:Direct\s*Bilirubin|D[\.\s]*Bili(?:rubin)?|Conjugated\s*Bilirubin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mg/dL']
    },
    'Albumin': {
        'patterns': [r'(?:Albumin|ALB)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'g/dL', 'alt_units': ['g/dL', 'g/L']
    },
    'GGT': {
        'patterns': [r'(?:GGT|Gamma[\s\-]*(?:Glutamyl)?[\s\-]*Transferase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L']
    },
}


def extract_text_from_image(image: Image.Image) -> str:
    """Extract text from an image using Tesseract OCR."""
    if pytesseract is None:
        return "Error: pytesseract not installed."
    try:
        image = image.convert('L')
        text = pytesseract.image_to_string(image, config='--psm 6 --oem 3')
        return text
    except Exception as e:
        return f"OCR Error: {str(e)}"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    all_text = ""
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                all_text += " ".join([str(c) if c else "" for c in row]) + "\n"
        except Exception:
            pass

    if len(all_text.strip()) < 50:
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=300)
            for img in images:
                all_text += extract_text_from_image(img) + "\n"
        except Exception as e:
            all_text += f"\nPDF Image OCR Error: {str(e)}"

    return all_text


def parse_parameters(text: str) -> Dict:
    """Parse blood parameters from extracted text."""
    results = {}
    for param_name, config in PARAMETER_PATTERNS.items():
        for pattern in config['patterns']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    results[param_name] = {
                        'value': value,
                        'unit': config['unit'],
                        'raw_match': match.group(0)
                    }
                    break
                except (ValueError, IndexError):
                    continue
    return results


def extract_patient_info(text: str) -> Dict:
    """Extract patient demographic information from text."""
    info = {}
    name_match = re.search(r'(?:Patient\s*Name|Name|Patient)\s*[:\-]?\s*([A-Za-z\s.]+?)(?:\n|$|Age|Sex)', text, re.IGNORECASE)
    if name_match:
        info['name'] = name_match.group(1).strip()

    age_match = re.search(r'(?:Age)\s*[:\-]?\s*(\d+)\s*(?:years?|yrs?|Y)?', text, re.IGNORECASE)
    if age_match:
        info['age'] = age_match.group(1)

    sex_match = re.search(r'(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)', text, re.IGNORECASE)
    if sex_match:
        val = sex_match.group(1).strip().upper()
        info['sex'] = 'Male' if val in ['M', 'MALE'] else 'Female'

    date_match = re.search(r'(?:Date|Collection\s*Date|Report\s*Date)\s*[:\-]?\s*([\d/\-\.]+)', text, re.IGNORECASE)
    if date_match:
        info['date'] = date_match.group(1)

    return info


def process_uploaded_file(uploaded_file) -> Tuple[str, Dict, Dict]:
    """Process an uploaded file and return extracted text, parameters, and patient info."""
    file_type = uploaded_file.type
    file_bytes = uploaded_file.read()
    extracted_text = ""

    if 'pdf' in file_type:
        extracted_text = extract_text_from_pdf(file_bytes)
    elif 'image' in file_type or file_type in ['image/jpeg', 'image/jpg', 'image/png']:
        image = Image.open(io.BytesIO(file_bytes))
        extracted_text = extract_text_from_image(image)
    else:
        extracted_text = "Unsupported file format"

    parameters = parse_parameters(extracted_text)
    patient_info = extract_patient_info(extracted_text)
    return extracted_text, parameters, patient_info
