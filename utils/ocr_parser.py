"""
OCR and Document Parsing Module
Handles extraction of blood parameters from uploaded documents.
"""

import re
import io
from typing import Dict, List, Tuple, Optional
from PIL import Image
import pytesseract
import pdfplumber


# Common blood parameter patterns for OCR extraction
PARAMETER_PATTERNS = {
    # RBC Parameters
    'RBC': {
        'patterns': [
            r'(?:RBC|Red\s*Blood\s*Cell(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
            r'(?:Erythrocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10¹²/L',
        'alt_units': ['million/µL', 'M/µL', '10^12/L', 'x10^12/L']
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
        'patterns': [
            r'(?:MCV|Mean\s*Corpuscular\s*Volume)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'fL',
        'alt_units': ['fl', 'fL']
    },
    'MCH': {
        'patterns': [
            r'(?:MCH|Mean\s*Corpuscular\s*Hemoglobin|Mean\s*Corpuscular\s*Haemoglobin)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'pg',
        'alt_units': ['pg']
    },
    'MCHC': {
        'patterns': [
            r'(?:MCHC|Mean\s*Corpuscular\s*(?:Hemoglobin|Haemoglobin)\s*Conc(?:entration)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'g/dL',
        'alt_units': ['g/dL', 'g/L']
    },
    'RDW': {
        'patterns': [
            r'(?:RDW(?:\-?CV)?|Red\s*Cell\s*Distribution\s*Width)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%']
    },
    'RDW_SD': {
        'patterns': [
            r'(?:RDW[\-\s]?SD)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'fL',
        'alt_units': ['fL']
    },
    # WBC Parameters
    'WBC': {
        'patterns': [
            r'(?:WBC|White\s*Blood\s*Cell(?:s)?(?:\s*Count)?|Total\s*Leucocyte\s*Count|TLC)\s*[:\-]?\s*([\d.]+)',
            r'(?:Leukocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L',
        'alt_units': ['K/µL', '10^9/L', 'x10^9/L', 'thou/µL']
    },
    'Neutrophils': {
        'patterns': [
            r'(?:Neutrophil(?:s)?|NEUT|Seg(?:mented)?(?:\s*Neutrophil(?:s)?)?)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Neutrophil(?:s)?|NEUT)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    'Lymphocytes': {
        'patterns': [
            r'(?:Lymphocyte(?:s)?|LYMPH|LY)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Lymphocyte(?:s)?|LYMPH|LY)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    'Monocytes': {
        'patterns': [
            r'(?:Monocyte(?:s)?|MONO|MO)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Monocyte(?:s)?|MONO|MO)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    'Eosinophils': {
        'patterns': [
            r'(?:Eosinophil(?:s)?|EOS|EO)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Eosinophil(?:s)?|EOS|EO)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    'Basophils': {
        'patterns': [
            r'(?:Basophil(?:s)?|BASO|BA)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Basophil(?:s)?|BASO|BA)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    # Platelet Parameters
    'Platelets': {
        'patterns': [
            r'(?:Platelet(?:s)?(?:\s*Count)?|PLT|Plt)\s*[:\-]?\s*([\d.]+)',
            r'(?:Thrombocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L',
        'alt_units': ['K/µL', '10^9/L', 'x10^9/L', 'thou/µL', 'lakhs']
    },
    'MPV': {
        'patterns': [
            r'(?:MPV|Mean\s*Platelet\s*Volume)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'fL',
        'alt_units': ['fL']
    },
    'PDW': {
        'patterns': [
            r'(?:PDW|Platelet\s*Distribution\s*Width)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'fL',
        'alt_units': ['fL', '%']
    },
    # Reticulocytes
    'Reticulocytes': {
        'patterns': [
            r'(?:Reticulocyte(?:s)?(?:\s*Count)?|RETIC|Ret)\s*[:\-]?\s*([\d.]+)\s*%',
            r'(?:Reticulocyte(?:s)?(?:\s*Count)?|RETIC|Ret)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'x10⁹/L']
    },
    # ESR
    'ESR': {
        'patterns': [
            r'(?:ESR|Erythrocyte\s*Sedimentation\s*Rate)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'mm/hr',
        'alt_units': ['mm/hr', 'mm/1st hr']
    },
    # Absolute Counts
    'ANC': {
        'patterns': [
            r'(?:ANC|Absolute\s*Neutrophil\s*Count)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L',
        'alt_units': ['cells/µL', '/µL']
    },
    'ALC': {
        'patterns': [
            r'(?:ALC|Absolute\s*Lymphocyte\s*Count)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L',
        'alt_units': ['cells/µL', '/µL']
    },
}


def extract_text_from_image(image: Image.Image) -> str:
    """Extract text from an image using Tesseract OCR."""
    try:
        # Preprocess image for better OCR
        image = image.convert('L')  # Grayscale
        # Apply threshold for better text recognition
        text = pytesseract.image_to_string(
            image,
            config='--psm 6 --oem 3'
        )
        return text
    except Exception as e:
        return f"OCR Error: {str(e)}"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    all_text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

                # Also extract tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            row_text = " ".join([str(cell) if cell else "" for cell in row])
                            all_text += row_text + "\n"
    except Exception:
        pass

    # If pdfplumber didn't extract enough text, try OCR on PDF images
    if len(all_text.strip()) < 50:
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=300)
            for img in images:
                all_text += extract_text_from_image(img) + "\n"
        except Exception as e:
            all_text += f"\nPDF Image OCR Error: {str(e)}"

    return all_text


def parse_parameters(text: str) -> Dict[str, Dict]:
    """Parse blood parameters from extracted text."""
    results = {}
    text_upper = text.upper()

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


def extract_patient_info(text: str) -> Dict[str, str]:
    """Extract patient demographic information from text."""
    info = {}

    # Patient Name
    name_match = re.search(
        r'(?:Patient\s*Name|Name|Patient)\s*[:\-]?\s*([A-Za-z\s.]+?)(?:\n|$|Age|Sex|Gender|DOB)',
        text, re.IGNORECASE
    )
    if name_match:
        info['name'] = name_match.group(1).strip()

    # Age
    age_match = re.search(
        r'(?:Age)\s*[:\-]?\s*(\d+)\s*(?:years?|yrs?|Y)?',
        text, re.IGNORECASE
    )
    if age_match:
        info['age'] = age_match.group(1)

    # Sex/Gender
    sex_match = re.search(
        r'(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)',
        text, re.IGNORECASE
    )
    if sex_match:
        sex_val = sex_match.group(1).strip().upper()
        if sex_val in ['M', 'MALE']:
            info['sex'] = 'Male'
        elif sex_val in ['F', 'FEMALE']:
            info['sex'] = 'Female'

    # Date
    date_match = re.search(
        r'(?:Date|Collection\s*Date|Report\s*Date|Sample\s*Date)\s*[:\-]?\s*([\d/\-\.]+)',
        text, re.IGNORECASE
    )
    if date_match:
        info['date'] = date_match.group(1)

    # Lab / Hospital
    lab_match = re.search(
        r'(?:Lab(?:oratory)?|Hospital|Clinic|Center|Centre)\s*[:\-]?\s*(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if lab_match:
        info['lab'] = lab_match.group(1).strip()

    return info


def process_uploaded_file(uploaded_file) -> Tuple[str, Dict[str, Dict], Dict[str, str]]:
    """
    Process an uploaded file and return extracted text, parameters, and patient info.
    """
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
