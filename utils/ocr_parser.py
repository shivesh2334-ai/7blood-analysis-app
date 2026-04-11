"""
OCR Parser Module
=================
Extracts text from uploaded lab report files (PDF/images) using OCR,
then parses clinical laboratory parameter values and patient information.

Functions:
    process_uploaded_file  -- End-to-end: file → (text, params, grouped, patient_info)
    preprocess_text        -- Clean and normalise raw OCR text
    parse_parameters       -- Extract parameter name/value pairs from text
    extract_patient_info   -- Pull patient demographic fields from text
"""

import re
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parameter aliases — maps common lab-report labels to canonical keys used
# by the analysis engine (keys of REFERENCE_RANGES).
# ---------------------------------------------------------------------------
PARAMETER_ALIASES: Dict[str, str] = {
    # CBC
    "rbc": "RBC", "rbc count": "RBC", "red blood cell": "RBC",
    "red blood cell count": "RBC", "red blood cells": "RBC",
    "haemoglobin": "Hemoglobin", "hemoglobin": "Hemoglobin", "hgb": "Hemoglobin",
    "hb": "Hemoglobin",
    "hematocrit": "Hematocrit", "haematocrit": "Hematocrit", "hct": "Hematocrit",
    "pcv": "Hematocrit",
    "mcv": "MCV", "mean corpuscular volume": "MCV",
    "mch": "MCH", "mean corpuscular hemoglobin": "MCH",
    "mean corpuscular haemoglobin": "MCH",
    "mchc": "MCHC", "mean corpuscular hemoglobin concentration": "MCHC",
    "rdw": "RDW_CV", "rdw-cv": "RDW_CV", "rdw cv": "RDW_CV",
    "rdw-sd": "RDW_SD", "rdw sd": "RDW_SD",
    "wbc": "WBC", "wbc count": "WBC", "white blood cell": "WBC",
    "white blood cell count": "WBC", "white blood cells": "WBC",
    "total wbc count": "WBC", "total leucocyte count": "WBC", "tlc": "WBC",
    "neutrophils": "Neutrophils", "neutrophil": "Neutrophils",
    "lymphocytes": "Lymphocytes", "lymphocyte": "Lymphocytes",
    "monocytes": "Monocytes", "monocyte": "Monocytes",
    "eosinophils": "Eosinophils", "eosinophil": "Eosinophils",
    "basophils": "Basophils", "basophil": "Basophils",
    "bands": "Bands", "band neutrophils": "Bands",
    "platelets": "Platelets", "platelet count": "Platelets", "plt": "Platelets",
    "mpv": "MPV", "mean platelet volume": "MPV",
    "pdw": "PDW", "platelet distribution width": "PDW",
    "pct": "PCT", "plateletcrit": "PCT",
    "esr": "ESR", "erythrocyte sedimentation rate": "ESR", "sed rate": "ESR",
    "reticulocytes": "Reticulocytes", "reticulocyte count": "Reticulocytes",
    "retic count": "Reticulocytes",
    "anc": "ANC", "absolute neutrophil count": "ANC",
    "alc": "ALC", "absolute lymphocyte count": "ALC",

    # LFT
    "alt": "ALT", "sgpt": "ALT", "alanine aminotransferase": "ALT",
    "alanine transaminase": "ALT",
    "ast": "AST", "sgot": "AST", "aspartate aminotransferase": "AST",
    "aspartate transaminase": "AST",
    "alp": "ALP", "alkaline phosphatase": "ALP",
    "ggt": "GGT", "gamma gt": "GGT", "gamma-glutamyl transferase": "GGT",
    "gamma glutamyl transferase": "GGT",
    "ldh": "LDH", "lactate dehydrogenase": "LDH",
    "total bilirubin": "Total_Bilirubin", "bilirubin total": "Total_Bilirubin",
    "bilirubin (total)": "Total_Bilirubin", "t. bilirubin": "Total_Bilirubin",
    "direct bilirubin": "Direct_Bilirubin", "bilirubin direct": "Direct_Bilirubin",
    "conjugated bilirubin": "Direct_Bilirubin",
    "indirect bilirubin": "Indirect_Bilirubin", "bilirubin indirect": "Indirect_Bilirubin",
    "unconjugated bilirubin": "Indirect_Bilirubin",
    "total protein": "Total_Protein", "serum protein": "Total_Protein",
    "albumin": "Albumin", "serum albumin": "Albumin",
    "globulin": "Globulin",
    "a/g ratio": "AG_Ratio", "ag ratio": "AG_Ratio",
    "albumin/globulin ratio": "AG_Ratio", "a:g ratio": "AG_Ratio",
    "pt": "PT", "prothrombin time": "PT",
    "inr": "INR", "international normalized ratio": "INR",
    "aptt": "APTT", "activated partial thromboplastin time": "APTT",
    "ptt": "APTT",
    "serum ammonia": "Serum_Ammonia", "ammonia": "Serum_Ammonia",

    # KFT / Renal
    "serum creatinine": "Serum_Creatinine", "creatinine": "Serum_Creatinine",
    "s. creatinine": "Serum_Creatinine",
    "bun": "BUN", "blood urea nitrogen": "BUN",
    "serum urea": "Serum_Urea", "urea": "Serum_Urea", "blood urea": "Serum_Urea",
    "serum uric acid": "Serum_Uric_Acid", "uric acid": "Serum_Uric_Acid",
    "egfr": "eGFR", "gfr": "eGFR", "estimated gfr": "eGFR",
    "glomerular filtration rate": "eGFR",
    "serum sodium": "Serum_Sodium", "sodium": "Serum_Sodium", "na+": "Serum_Sodium",
    "na": "Serum_Sodium",
    "serum potassium": "Serum_Potassium", "potassium": "Serum_Potassium",
    "k+": "Serum_Potassium", "k": "Serum_Potassium",
    "serum chloride": "Serum_Chloride", "chloride": "Serum_Chloride",
    "cl": "Serum_Chloride",
    "serum bicarbonate": "Serum_Bicarbonate", "bicarbonate": "Serum_Bicarbonate",
    "hco3": "Serum_Bicarbonate",
    "serum calcium": "Serum_Calcium", "calcium": "Serum_Calcium", "ca": "Serum_Calcium",
    "ionised calcium": "Ionised_Calcium", "ionized calcium": "Ionised_Calcium",
    "ionic calcium": "Ionised_Calcium",
    "serum phosphorus": "Serum_Phosphorus", "phosphorus": "Serum_Phosphorus",
    "phosphate": "Serum_Phosphorus",
    "serum magnesium": "Serum_Magnesium", "magnesium": "Serum_Magnesium",
    "mg": "Serum_Magnesium",
    "acr": "ACR", "albumin creatinine ratio": "ACR",
    "albumin-to-creatinine ratio": "ACR",
    "urine microalbumin": "Urine_Microalbumin", "microalbumin": "Urine_Microalbumin",
    "cystatin c": "Cystatin_C", "cystatin-c": "Cystatin_C",

    # Lipid profile
    "total cholesterol": "Total_Cholesterol", "cholesterol": "Total_Cholesterol",
    "cholesterol total": "Total_Cholesterol", "serum cholesterol": "Total_Cholesterol",
    "hdl cholesterol": "HDL_Cholesterol", "hdl": "HDL_Cholesterol",
    "hdl-c": "HDL_Cholesterol", "hdl-cholesterol": "HDL_Cholesterol",
    "ldl cholesterol": "LDL_Cholesterol", "ldl": "LDL_Cholesterol",
    "ldl-c": "LDL_Cholesterol", "ldl-cholesterol": "LDL_Cholesterol",
    "vldl cholesterol": "VLDL_Cholesterol", "vldl": "VLDL_Cholesterol",
    "vldl-c": "VLDL_Cholesterol",
    "triglycerides": "Triglycerides", "triglyceride": "Triglycerides",
    "tg": "Triglycerides", "trigs": "Triglycerides",
    "non-hdl cholesterol": "Non_HDL_Cholesterol", "non hdl cholesterol": "Non_HDL_Cholesterol",
    "tc/hdl ratio": "TC_HDL_Ratio", "tc:hdl ratio": "TC_HDL_Ratio",
    "total cholesterol/hdl ratio": "TC_HDL_Ratio",
    "ldl/hdl ratio": "LDL_HDL_Ratio", "ldl:hdl ratio": "LDL_HDL_Ratio",
    "lipoprotein a": "Lipoprotein_a", "lipoprotein(a)": "Lipoprotein_a",
    "lp(a)": "Lipoprotein_a",
    "apoa1": "ApoA1", "apolipoprotein a1": "ApoA1", "apo a-1": "ApoA1",
    "apob": "ApoB", "apolipoprotein b": "ApoB", "apo b": "ApoB",

    # Diabetes
    "fasting blood glucose": "Fasting_Blood_Glucose", "fasting glucose": "Fasting_Blood_Glucose",
    "fbg": "Fasting_Blood_Glucose", "fbs": "Fasting_Blood_Glucose",
    "fasting blood sugar": "Fasting_Blood_Glucose",
    "postprandial glucose": "Postprandial_Glucose", "ppg": "Postprandial_Glucose",
    "pp glucose": "Postprandial_Glucose", "ppbs": "Postprandial_Glucose",
    "postprandial blood sugar": "Postprandial_Glucose",
    "random blood glucose": "Random_Blood_Glucose", "rbg": "Random_Blood_Glucose",
    "random blood sugar": "Random_Blood_Glucose", "rbs": "Random_Blood_Glucose",
    "hba1c": "HbA1c", "glycated hemoglobin": "HbA1c", "glycated haemoglobin": "HbA1c",
    "a1c": "HbA1c", "hemoglobin a1c": "HbA1c",
    "eag": "eAG", "estimated average glucose": "eAG",
    "fasting insulin": "Fasting_Insulin", "insulin fasting": "Fasting_Insulin",
    "homa-ir": "HOMA_IR", "homa ir": "HOMA_IR",
    "c-peptide": "C_Peptide", "c peptide": "C_Peptide",

    # Thyroid
    "tsh": "TSH", "thyroid stimulating hormone": "TSH",
    "free t3": "Free_T3", "ft3": "Free_T3",
    "total t3": "Total_T3", "t3": "Total_T3",
    "free t4": "Free_T4", "ft4": "Free_T4",
    "total t4": "Total_T4", "t4": "Total_T4",
    "anti-tpo": "Anti_TPO", "anti tpo": "Anti_TPO", "tpo antibodies": "Anti_TPO",
    "anti-thyroglobulin": "Anti_Thyroglobulin", "anti thyroglobulin": "Anti_Thyroglobulin",
    "tsh receptor antibodies": "TSH_Receptor_Ab", "trab": "TSH_Receptor_Ab",
    "thyroglobulin": "Thyroglobulin",
    "calcitonin": "Calcitonin",

    # Vitamins
    "vitamin d": "Vitamin_D_25OH", "vit d": "Vitamin_D_25OH",
    "25-oh vitamin d": "Vitamin_D_25OH", "25 oh vitamin d": "Vitamin_D_25OH",
    "vitamin d 25-oh": "Vitamin_D_25OH", "vitamin d3": "Vitamin_D3",
    "cholecalciferol": "Vitamin_D3",
    "pth": "PTH", "parathyroid hormone": "PTH",
    "vitamin b12": "Vitamin_B12", "vit b12": "Vitamin_B12",
    "cyanocobalamin": "Vitamin_B12", "cobalamin": "Vitamin_B12",
    "serum folate": "Serum_Folate", "folate": "Serum_Folate",
    "folic acid": "Serum_Folate",
    "rbc folate": "RBC_Folate", "red cell folate": "RBC_Folate",
    "homocysteine": "Homocysteine",

    # Rheumatology
    "ra factor": "RA_Factor", "rheumatoid factor": "RA_Factor", "rf": "RA_Factor",
    "anti-ccp": "Anti_CCP", "anti ccp": "Anti_CCP", "acpa": "Anti_CCP",
    "crp": "CRP", "c-reactive protein": "CRP", "c reactive protein": "CRP",
    "hs-crp": "hs_CRP", "hs crp": "hs_CRP",
    "high sensitivity crp": "hs_CRP",
    "anti-dsdna": "Anti_dsDNA", "anti dsdna": "Anti_dsDNA",
    "c3 complement": "C3_Complement", "c3": "C3_Complement",
    "complement c3": "C3_Complement",
    "c4 complement": "C4_Complement", "c4": "C4_Complement",
    "complement c4": "C4_Complement",
    "aso titre": "ASO_Titre", "aso": "ASO_Titre",
    "anti-streptolysin o": "ASO_Titre",

    # Iron studies
    "ferritin": "Ferritin", "serum ferritin": "Ferritin",
    "serum iron": "Serum_Iron", "iron": "Serum_Iron",
    "tibc": "TIBC", "total iron binding capacity": "TIBC",
    "transferrin saturation": "Transferrin_Saturation",
    "tsat": "Transferrin_Saturation",

    # Oncology markers
    "psa": "PSA_Total", "psa total": "PSA_Total", "total psa": "PSA_Total",
    "psa free": "PSA_Free", "free psa": "PSA_Free",
    "cea": "CEA", "carcinoembryonic antigen": "CEA",
    "ca-125": "CA_125", "ca 125": "CA_125",
    "ca-19-9": "CA_19_9", "ca 19-9": "CA_19_9", "ca19.9": "CA_19_9",
    "ca-15-3": "CA_15_3", "ca 15-3": "CA_15_3",
    "ca-72-4": "CA_72_4", "ca 72-4": "CA_72_4",
    "afp": "AFP", "alpha-fetoprotein": "AFP", "alpha fetoprotein": "AFP",
    "beta hcg": "Beta_HCG", "beta-hcg": "Beta_HCG", "bhcg": "Beta_HCG",
    "nse": "NSE", "neuron specific enolase": "NSE",
    "cyfra 21-1": "CYFRA_21_1", "cyfra": "CYFRA_21_1",
    "scc antigen": "SCC_Antigen", "scc": "SCC_Antigen",
    "chromogranin a": "Chromogranin_A", "cga": "Chromogranin_A",
    "he4": "HE4",

    # Urine
    "urine ph": "Urine_pH",
    "urine specific gravity": "Urine_Specific_Gravity",
    "specific gravity": "Urine_Specific_Gravity",
    "urine pus cells": "Urine_Pus_Cells", "pus cells": "Urine_Pus_Cells",
    "urine rbc": "Urine_RBC",
}

# Build a sorted list for regex matching (longer aliases first to avoid partial matches)
_SORTED_ALIASES = sorted(PARAMETER_ALIASES.keys(), key=len, reverse=True)


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

def preprocess_text(raw_text: str) -> str:
    """Clean and normalise raw OCR text for parameter extraction.

    Handles common OCR artefacts such as extra whitespace, inconsistent
    separators, and unicode quirks.

    Args:
        raw_text: Raw string extracted from OCR or pasted by user.

    Returns:
        Normalised text suitable for ``parse_parameters``.
    """
    if not raw_text:
        return ""

    text = raw_text

    # Normalise unicode dashes, bullets, and whitespace
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2022", " ").replace("\u00b7", " ")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')

    # Collapse multiple spaces / tabs but keep newlines
    text = re.sub(r"[^\S\n]+", " ", text)

    # Normalise line endings
    text = re.sub(r"\r\n?", "\n", text)

    # Remove very long runs of the same character (OCR artefacts)
    text = re.sub(r"(.)\1{10,}", r"\1\1\1", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

# Regex to capture a floating-point or integer number
_NUM_RE = r"(\d+(?:\.\d+)?)"


def parse_parameters(text: str) -> Dict[str, Dict[str, Any]]:
    """Extract laboratory parameter values from preprocessed text.

    Scans the text for known parameter names (via ``PARAMETER_ALIASES``)
    followed by a numeric value.  Returns a dictionary keyed by the
    canonical parameter name with sub-keys ``"value"`` and ``"raw_match"``.

    Longer aliases are matched first; overlapping text spans are skipped
    to prevent short aliases (e.g. "t4") from shadowing longer matches
    (e.g. "free t4").

    Args:
        text: Preprocessed lab report text (output of ``preprocess_text``).

    Returns:
        Dictionary mapping canonical parameter keys to
        ``{"value": float, "raw_match": str}``.
    """
    if not text:
        return {}

    results: Dict[str, Dict[str, Any]] = {}
    text_lower = text.lower()
    matched_spans: List[Tuple[int, int]] = []  # track (start, end) of matched regions

    def _overlaps(start: int, end: int) -> bool:
        """Check whether (start, end) overlaps any already-matched span."""
        for ms, me in matched_spans:
            if start < me and end > ms:
                return True
        return False

    for alias in _SORTED_ALIASES:
        canonical = PARAMETER_ALIASES[alias]
        if canonical in results:
            continue  # already found via a longer/earlier alias

        # Build a pattern that looks for the alias followed by a number
        escaped = re.escape(alias)
        pattern = (
            rf"(?:^|[\s,;:(])"     # word boundary / separator before
            rf"{escaped}"
            rf"[\s:=\-–]*"         # separator between name and value
            rf"{_NUM_RE}"           # the numeric value
        )

        match = re.search(pattern, text_lower)
        if match:
            if _overlaps(match.start(), match.end()):
                continue  # this text region was already consumed
            try:
                value = float(match.group(1))
                results[canonical] = {
                    "value": value,
                    "raw_match": match.group(0).strip(),
                }
                matched_spans.append((match.start(), match.end()))
            except (ValueError, IndexError):
                continue

    return results


# ---------------------------------------------------------------------------
# Patient info extraction
# ---------------------------------------------------------------------------

def extract_patient_info(text: str) -> Dict[str, str]:
    """Extract patient demographic information from report text.

    Looks for common fields: name, age, sex/gender, date, lab/hospital,
    and patient/sample ID.

    Args:
        text: Raw or preprocessed report text.

    Returns:
        Dictionary with found patient info fields (may be empty).
    """
    info: Dict[str, str] = {}
    if not text:
        return info

    # Name
    name_match = re.search(
        r"(?:patient\s*(?:name)?|name)\s*[:=\-]\s*([A-Za-z .\-']{2,40})",
        text, re.IGNORECASE,
    )
    if name_match:
        info["name"] = name_match.group(1).strip()

    # Age
    age_match = re.search(
        r"(?:age)\s*[:=\-]\s*(\d{1,3})\s*(?:y(?:ears?|rs?)?)?",
        text, re.IGNORECASE,
    )
    if age_match:
        info["age"] = age_match.group(1).strip()

    # Sex / Gender
    sex_match = re.search(
        r"(?:sex|gender)\s*[:=\-]\s*(male|female|m|f)\b",
        text, re.IGNORECASE,
    )
    if sex_match:
        raw = sex_match.group(1).strip().lower()
        info["sex"] = "male" if raw in ("m", "male") else "female"

    # Date
    date_match = re.search(
        r"(?:date|collected|reported|sample date)\s*[:=\-]\s*"
        r"(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        text, re.IGNORECASE,
    )
    if date_match:
        info["date"] = date_match.group(1).strip()

    # Lab / Hospital
    lab_match = re.search(
        r"(?:lab(?:oratory)?|hospital|clinic|centre|center)\s*[:=\-]\s*(.{2,50})",
        text, re.IGNORECASE,
    )
    if lab_match:
        info["lab"] = lab_match.group(1).strip().split("\n")[0]

    # Patient / Sample ID
    id_match = re.search(
        r"(?:patient\s*id|sample\s*id|mrn|uhid|reg(?:istration)?\.?\s*no)\s*[:=\-]\s*(\S+)",
        text, re.IGNORECASE,
    )
    if id_match:
        info["id"] = id_match.group(1).strip()

    return info


# ---------------------------------------------------------------------------
# File processing (OCR / text extraction)
# ---------------------------------------------------------------------------

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using available libraries.

    Tries pdfplumber first, falls back to PyPDF2, then to pytesseract
    via pdf2image for scanned PDFs.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Extracted text string.
    """
    text = ""

    # Strategy 1: pdfplumber (best for digital PDFs)
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except Exception as exc:
        logger.debug("pdfplumber failed: %s", exc)

    # Strategy 2: PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if text.strip():
            return text
    except Exception as exc:
        logger.debug("PyPDF2 failed: %s", exc)

    # Strategy 3: OCR via pdf2image + pytesseract (for scanned PDFs)
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        images = convert_from_bytes(file_bytes)
        for img in images:
            page_text = pytesseract.image_to_string(img)
            if page_text:
                text += page_text + "\n"
    except Exception as exc:
        logger.debug("pdf2image/pytesseract OCR failed: %s", exc)

    return text


def _extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from an image file using pytesseract OCR.

    Args:
        file_bytes: Raw bytes of the image file.

    Returns:
        Extracted text string.
    """
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img)
    except Exception as exc:
        logger.warning("Image OCR failed: %s", exc)
        return ""


def process_uploaded_file(
    uploaded_file,
) -> Tuple[str, Dict[str, Dict[str, Any]], Dict[str, list], Dict[str, str]]:
    """Process an uploaded lab report file end-to-end.

    Reads the file, extracts text (via OCR or text extraction), preprocesses
    it, parses parameter values, and extracts patient information.

    Args:
        uploaded_file: A file-like object (e.g. Streamlit ``UploadedFile``)
            with ``.name`` and ``.read()`` attributes.

    Returns:
        A 4-tuple of:
            - raw_text (str): The raw extracted text.
            - params (dict): Parsed parameters keyed by canonical name.
            - grouped (dict): Parameters grouped by panel (for convenience).
            - patient_info (dict): Extracted patient demographics.

    Raises:
        ValueError: If the file type is unsupported.
    """
    filename = getattr(uploaded_file, "name", "unknown")
    file_bytes = uploaded_file.read()

    # Reset the stream position so the caller can re-read if needed
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
        raw_text = _extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    processed_text = preprocess_text(raw_text)
    params = parse_parameters(processed_text)
    patient_info = extract_patient_info(raw_text)  # use raw for names/dates

    # Group parameters by panel (import lazily to avoid circular deps)
    try:
        from utils.analysis_engine import PANEL_PARAMETER_MAP
    except ImportError:
        from analysis_engine import PANEL_PARAMETER_MAP

    grouped: Dict[str, list] = {}
    for panel_key, panel_params in PANEL_PARAMETER_MAP.items():
        found = [p for p in panel_params if p in params]
        if found:
            grouped[panel_key] = found

    return raw_text, params, grouped, patient_info
