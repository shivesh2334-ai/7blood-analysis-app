"""
ocr_parser.py — Comprehensive Lab Report OCR & Parsing Module
==============================================================
Extracts text from PDF / image lab reports and parses values for:

  CBC  · LFT  · KFT  · LIPID  · DIABETES  · TFT
  VIT_D · VIT_B12 · URINE_RM · RHEUMA · ONCOLOGY

Public API
----------
  process_uploaded_file(file)       → (text, params, grouped, patient_info)
  parse_parameters(text)            → flat {key: {value, unit, panel, raw}}
  parse_panel(panel_key, text)      → {key: {value, unit, panel, raw}}
  group_parameters(parsed)          → {panel_key: {key: ...}}
  extract_patient_info(text)        → {name, age, sex, date, lab_ref, doctor}
  preprocess_text(text)             → normalised string
  compute_derived(results)          → results + calculated fields
"""

from __future__ import annotations
import re
import io
from typing import Any, Dict, Optional, Tuple
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# ── Separator: colon / pipe / dash / spaces / tabs in any combo ─────────────
SEP = r"[\s:|.\-]*\s*"

# ── Qualitative dipstick values ─────────────────────────────────────────────
QUAL = r"(Nil|Absent|None|Trace|Negative|Positive|\+{1,4}|[\d.]+)"

# ── Panel display names ──────────────────────────────────────────────────────
PANEL_LABELS = {
    "CBC":      "Complete Blood Count",
    "LFT":      "Liver Function Tests",
    "KFT":      "Kidney Function Tests",
    "LIPID":    "Lipid Profile",
    "DIABETES": "Diabetes Markers",
    "TFT":      "Thyroid Function Tests",
    "VIT_D":    "Vitamin D",
    "VIT_B12":  "Vitamin B12 / Folate",
    "URINE_RM": "Urine Routine & Microscopy",
    "RHEUMA":   "Rheumatology Markers",
    "ONCOLOGY": "Oncology / Tumour Markers",
}

# ============================================================================
# MASTER PARAMETER PATTERN TABLE
# ============================================================================
# Each entry:
#   patterns   — ordered list; first match wins
#   unit       — preferred display unit
#   panel      — panel key
#   text_value — True for qualitative results (stored as string, not float)

PARAMETER_PATTERNS: Dict[str, Any] = {

    # ========================================================================
    # CBC — Complete Blood Count
    # ========================================================================
    "RBC": {
        "patterns": [
            r"(?:RBC|Red\s*Blood\s*Cells?(?:\s*Count)?|Total\s*RBC|Erythrocytes?(?:\s*Count)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10¹²/L", "panel": "CBC",
    },
    "Hemoglobin": {
        "patterns": [
            r"(?:H(?:a?e)?moglobin|Hgb|HGB|\bHb\b)" + SEP + r"([\d.]+)",
        ],
        "unit": "g/dL", "panel": "CBC",
    },
    "Hematocrit": {
        "patterns": [
            r"(?:H(?:a?)ematocrit|HCT|Hct|PCV|Packed\s*Cell\s*Volume)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "MCV": {
        "patterns": [
            r"(?:MCV|Mean\s*Corpuscular\s*Volume|Mean\s*Cell\s*Volume)" + SEP + r"([\d.]+)",
        ],
        "unit": "fL", "panel": "CBC",
    },
    "MCH": {
        "patterns": [
            r"(?:MCH|Mean\s*Corpuscular\s*H(?:a?e)moglobin)(?!C)" + SEP + r"([\d.]+)",
        ],
        "unit": "pg", "panel": "CBC",
    },
    "MCHC": {
        "patterns": [
            r"(?:MCHC|Mean\s*Corpuscular\s*H(?:a?e)moglobin\s*Conc(?:entration)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "g/dL", "panel": "CBC",
    },
    "RDW_CV": {
        "patterns": [
            r"(?:RDW[\-\s]?CV|Red\s*(?:Cell|Blood\s*Cell)\s*Distribution\s*Width[\-\s]?CV)" + SEP + r"([\d.]+)",
            r"(?:RDW|Red\s*Cell\s*Distribution\s*Width)(?![\-\s]?SD)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "RDW_SD": {
        "patterns": [
            r"(?:RDW[\-\s]?SD|Red\s*(?:Cell|Blood\s*Cell)\s*Distribution\s*Width[\-\s]?SD)" + SEP + r"([\d.]+)",
        ],
        "unit": "fL", "panel": "CBC",
    },
    "WBC": {
        "patterns": [
            r"(?:WBC|White\s*Blood\s*Cells?(?:\s*Count)?|Total\s*(?:WBC|Leuco?cyte\s*Count)|TLC)" + SEP + r"([\d.]+)",
            r"Leuco?cyte(?:s)?(?:\s*Count)?" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "Neutrophils": {
        "patterns": [
            r"(?:Neutrophils?|NEUTS?|Seg(?:mented)?(?:\s*Neutrophils?)?)" + SEP + r"([\d.]+)\s*%",
            r"(?:Neutrophils?|NEUTS?)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Lymphocytes": {
        "patterns": [
            r"(?:Lymphocytes?|LYMPH|LYM?)" + SEP + r"([\d.]+)\s*%",
            r"(?:Lymphocytes?|LYMPH|LYM?)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Monocytes": {
        "patterns": [
            r"(?:Monocytes?|MONO|MO)" + SEP + r"([\d.]+)\s*%",
            r"(?:Monocytes?|MONO)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Eosinophils": {
        "patterns": [
            r"(?:Eosinophils?|EOS(?:IN)?|EO)" + SEP + r"([\d.]+)\s*%",
            r"(?:Eosinophils?|EOS(?:IN)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Basophils": {
        "patterns": [
            r"(?:Basophils?|BASO|BA)" + SEP + r"([\d.]+)\s*%",
            r"(?:Basophils?|BASO)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Bands": {
        "patterns": [
            r"(?:Bands?(?:\s*Neutrophils?)?|Stabs?)" + SEP + r"([\d.]+)\s*%",
            r"(?:Bands?(?:\s*Neutrophils?)?|Stabs?)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "Immature_Granulocytes": {
        "patterns": [
            r"(?:Immature\s*Granulocytes?|IG|Metamyelocytes?|Myelocytes?)" + SEP + r"([\d.]+)\s*%",
            r"(?:Immature\s*Granulocytes?|IG)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "ANC": {
        "patterns": [
            r"(?:ANC|Absolute\s*Neutrophil\s*Count|Neutrophils?\s*Abs(?:olute)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "ALC": {
        "patterns": [
            r"(?:ALC|Absolute\s*Lymphocyte\s*Count|Lymphocytes?\s*Abs(?:olute)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "AMC": {
        "patterns": [
            r"(?:AMC|Absolute\s*Monocyte\s*Count|Monocytes?\s*Abs(?:olute)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "AEC": {
        "patterns": [
            r"(?:AEC|Absolute\s*Eosinophil\s*Count|Eosinophils?\s*Abs(?:olute)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "Platelets": {
        "patterns": [
            r"(?:Platelets?(?:\s*Count)?|PLT|Plt|Thrombocytes?(?:\s*Count)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "×10⁹/L", "panel": "CBC",
    },
    "MPV": {
        "patterns": [r"(?:MPV|Mean\s*Platelet\s*Volume)" + SEP + r"([\d.]+)"],
        "unit": "fL", "panel": "CBC",
    },
    "PDW": {
        "patterns": [r"(?:PDW|Platelet\s*Distribution\s*Width)" + SEP + r"([\d.]+)"],
        "unit": "fL", "panel": "CBC",
    },
    "PCT": {
        "patterns": [r"(?:PCT|Plateletcrit|Platelet\s*Crit)(?!\s*\w)" + SEP + r"([\d.]+)"],
        "unit": "%", "panel": "CBC",
    },
    "Reticulocytes": {
        "patterns": [
            r"(?:Reticulocytes?(?:\s*Count)?|RETIC|Retic)" + SEP + r"([\d.]+)\s*%",
            r"(?:Reticulocytes?(?:\s*Count)?|RETIC)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "CBC",
    },
    "ESR": {
        "patterns": [r"(?:ESR|Erythrocyte\s*Sedimentation\s*Rate)" + SEP + r"([\d.]+)"],
        "unit": "mm/hr", "panel": "CBC",
    },
    "NRBC": {
        "patterns": [r"(?:NRBC|Nucleated\s*RBC|Nucleated\s*Red\s*(?:Blood\s*)?Cells?)" + SEP + r"([\d.]+)"],
        "unit": "/100 WBC", "panel": "CBC",
    },

    # ========================================================================
    # LFT — Liver Function Tests
    # ========================================================================
    "ALT": {
        "patterns": [r"(?:ALT|SGPT|Alanine\s*(?:Amino)?transf(?:erase)?)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "LFT",
    },
    "AST": {
        "patterns": [r"(?:AST|SGOT|Aspartate\s*(?:Amino)?transf(?:erase)?)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "LFT",
    },
    "ALP": {
        "patterns": [r"(?:ALP|Alkaline\s*Phosphatase)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "LFT",
    },
    "GGT": {
        "patterns": [r"(?:GGT|GGTP|Gamma[\s\-]*(?:GT|Glutamyl)?[\s\-]*(?:Transferase|Transpeptidase)?)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "LFT",
    },
    "LDH": {
        "patterns": [r"(?:LDH|Lactate\s*Dehydrogenase|Lactic\s*(?:Acid\s*)?Dehydrogenase)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "LFT",
    },
    "Total_Bilirubin": {
        "patterns": [
            r"(?:Total\s*Bilirubin|T\.?\s*Bili(?:rubin)?|Bilirubin[\s,]*Total|S(?:erum)?\s*Bilirubin[\s\-]*Total)" + SEP + r"([\d.]+)",
            r"Bilirubin[\s,]*T(?:otal)?" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LFT",
    },
    "Direct_Bilirubin": {
        "patterns": [
            r"(?:Direct\s*Bilirubin|D\.?\s*Bili(?:rubin)?|Conjugated\s*Bilirubin|Bilirubin[\s,]*Direct)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LFT",
    },
    "Indirect_Bilirubin": {
        "patterns": [
            r"(?:Indirect\s*Bilirubin|I\.?\s*Bili(?:rubin)?|Unconjugated\s*Bilirubin|Bilirubin[\s,]*Indirect)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LFT",
    },
    "Total_Protein": {
        "patterns": [
            r"(?:Total\s*Protein|Protein[\s,]*Total|Serum\s*Total\s*Protein)" + SEP + r"([\d.]+)",
        ],
        "unit": "g/dL", "panel": "LFT",
    },
    "Albumin": {
        "patterns": [r"(?:Albumin|ALB|Serum\s*Albumin)(?!\s*Creatinine)" + SEP + r"([\d.]+)"],
        "unit": "g/dL", "panel": "LFT",
    },
    "Globulin": {
        "patterns": [r"(?:Globulin|GLOB|Serum\s*Globulin)" + SEP + r"([\d.]+)"],
        "unit": "g/dL", "panel": "LFT",
    },
    "AG_Ratio": {
        "patterns": [r"(?:A[\s/]?G\s*Ratio|Albumin[\s/]Globulin\s*Ratio|A/G)" + SEP + r"([\d.]+)"],
        "unit": "ratio", "panel": "LFT",
    },
    "PT": {
        "patterns": [r"(?:PT|Prothrombin\s*Time)(?!\s*INR|\s*APTT)" + SEP + r"([\d.]+)"],
        "unit": "sec", "panel": "LFT",
    },
    "INR": {
        "patterns": [r"(?:INR|International\s*Normalized\s*Ratio|PT[\-\s]*INR)" + SEP + r"([\d.]+)"],
        "unit": "", "panel": "LFT",
    },
    "APTT": {
        "patterns": [r"(?:APTT|aPTT|Activated\s*Partial\s*Thromboplastin\s*Time)" + SEP + r"([\d.]+)"],
        "unit": "sec", "panel": "LFT",
    },
    "Serum_Ammonia": {
        "patterns": [r"(?:Ammonia|Serum\s*Ammonia|NH3)" + SEP + r"([\d.]+)"],
        "unit": "µmol/L", "panel": "LFT",
    },

    # ========================================================================
    # KFT — Kidney Function Tests
    # ========================================================================
    "Serum_Creatinine": {
        "patterns": [
            r"(?:S(?:erum)?\s*Creatinine|Creatinine(?:\s*Serum)?)(?!\s*Ratio)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "KFT",
    },
    "BUN": {
        "patterns": [
            r"(?:BUN|Blood\s*Urea\s*Nitrogen|Urea\s*Nitrogen)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "KFT",
    },
    "Serum_Urea": {
        "patterns": [
            r"(?:Serum\s*Urea|Blood\s*Urea)(?!\s*Nitrogen)" + SEP + r"([\d.]+)",
            r"\bUrea\b(?!\s*Nitrogen)(?!\s*Acid)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "KFT",
    },
    "Serum_Uric_Acid": {
        "patterns": [
            r"(?:(?:Serum\s*)?Uric\s*Acid|S\.?\s*Uric\s*Acid)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "KFT",
    },
    "eGFR": {
        "patterns": [
            r"(?:eGFR|Estimated\s*GFR|Glomerular\s*Filtration\s*Rate)" + SEP + r"([\d.]+)",
        ],
        "unit": "mL/min/1.73m²", "panel": "KFT",
    },
    "Serum_Sodium": {
        "patterns": [r"(?:Sodium|Na\+?|Serum\s*Sodium|S\.?\s*Na)(?!\s*Pot)" + SEP + r"([\d.]+)"],
        "unit": "mEq/L", "panel": "KFT",
    },
    "Serum_Potassium": {
        "patterns": [r"(?:Potassium|K\+?|Serum\s*Potassium|S\.?\s*K)" + SEP + r"([\d.]+)"],
        "unit": "mEq/L", "panel": "KFT",
    },
    "Serum_Chloride": {
        "patterns": [r"(?:Chloride|Cl[\-]?|Serum\s*Chloride|S\.?\s*Cl)" + SEP + r"([\d.]+)"],
        "unit": "mEq/L", "panel": "KFT",
    },
    "Serum_Bicarbonate": {
        "patterns": [r"(?:Bicarbonate|HCO3[\-]?|CO2|Serum\s*Bicarbonate|TCO2)" + SEP + r"([\d.]+)"],
        "unit": "mEq/L", "panel": "KFT",
    },
    "Serum_Calcium": {
        "patterns": [
            r"(?:(?:Serum\s*)?Calcium|Ca\+?\+?|S\.?\s*Ca)(?!\s*Ion|\s*Phos)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "KFT",
    },
    "Ionised_Calcium": {
        "patterns": [r"(?:Ionis[ez]ed?\s*Calcium|Ca\+?\+?\s*Ion(?:is[ez]ed?)?|iCa)" + SEP + r"([\d.]+)"],
        "unit": "mmol/L", "panel": "KFT",
    },
    "Serum_Phosphorus": {
        "patterns": [r"(?:Phosphorus|Phosphate|Inorganic\s*Phosphate|PO4|Serum\s*Phosphorus)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "KFT",
    },
    "Serum_Magnesium": {
        "patterns": [r"(?:Magnesium|Mg\+?\+?|Serum\s*Magnesium|S\.?\s*Mg)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "KFT",
    },
    "ACR": {
        "patterns": [r"(?:ACR|Albumin[\s/]*Creatinine\s*Ratio|Urine\s*ACR)" + SEP + r"([\d.]+)"],
        "unit": "mg/g", "panel": "KFT",
    },
    "Urine_Microalbumin": {
        "patterns": [r"(?:Microalbumin(?:uria)?|Urine\s*Microalbumin|Spot\s*Microalbumin)" + SEP + r"([\d.]+)"],
        "unit": "mg/L", "panel": "KFT",
    },
    "Cystatin_C": {
        "patterns": [r"(?:Cystatin[\-\s]*C)" + SEP + r"([\d.]+)"],
        "unit": "mg/L", "panel": "KFT",
    },

    # ========================================================================
    # LIPID — Lipid Profile
    # ========================================================================
    "Total_Cholesterol": {
        "patterns": [
            r"(?:Total\s*Cholesterol|Cholesterol[\s,]*Total|T\.?\s*Cholesterol|\bTC\b)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "HDL_Cholesterol": {
        "patterns": [
            r"(?:HDL[\s\-]*C(?:holesterol)?|High\s*Density\s*Lipoprotein(?:\s*Cholesterol)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "LDL_Cholesterol": {
        "patterns": [
            r"(?:LDL[\s\-]*C(?:holesterol)?|Low\s*Density\s*Lipoprotein(?:\s*Cholesterol)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "VLDL_Cholesterol": {
        "patterns": [
            r"(?:VLDL[\s\-]*C(?:holesterol)?|Very\s*Low\s*Density\s*Lipoprotein(?:\s*Cholesterol)?)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "Triglycerides": {
        "patterns": [
            r"(?:Triglycerides?|TG|Triacylglycerol|Serum\s*TG)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "Non_HDL_Cholesterol": {
        "patterns": [r"(?:Non[\s\-]*HDL[\s\-]*C(?:holesterol)?|Non\s*HDL)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "TC_HDL_Ratio": {
        "patterns": [r"(?:TC[\s/]*HDL\s*Ratio|Cholesterol[\s/]*HDL\s*Ratio|Total\s*Cholesterol[\s/]*HDL)" + SEP + r"([\d.]+)"],
        "unit": "ratio", "panel": "LIPID",
    },
    "LDL_HDL_Ratio": {
        "patterns": [r"(?:LDL[\s/]*HDL\s*Ratio)" + SEP + r"([\d.]+)"],
        "unit": "ratio", "panel": "LIPID",
    },
    "Lipoprotein_a": {
        "patterns": [r"(?:Lp\s*\(?a\)?|Lipoprotein[\s\-]*\(?a\)?)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "ApoA1": {
        "patterns": [r"(?:Apo(?:lipoprotein)?\s*A[\-\s]?1|ApoA1)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "LIPID",
    },
    "ApoB": {
        "patterns": [r"(?:Apo(?:lipoprotein)?\s*B[\-\s]?(?:100)?|ApoB)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "LIPID",
    },

    # ========================================================================
    # DIABETES — Diabetes Markers
    # ========================================================================
    "Fasting_Blood_Glucose": {
        "patterns": [
            r"(?:Fasting\s*(?:Blood\s*)?(?:Glucose|Sugar)|FBS|FBG|FPG)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "DIABETES",
    },
    "Postprandial_Glucose": {
        "patterns": [
            r"(?:Post\s*Prandial|PP\s*Blood\s*Sugar|PPBS|2\s*Hr\s*PP|Post\s*Meal\s*Glucose)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "DIABETES",
    },
    "Random_Blood_Glucose": {
        "patterns": [
            r"(?:Random\s*Blood\s*(?:Glucose|Sugar)|RBS|RBG|Random\s*Glucose)" + SEP + r"([\d.]+)",
        ],
        "unit": "mg/dL", "panel": "DIABETES",
    },
    "HbA1c": {
        "patterns": [
            r"(?:HbA1c|HBA1C|Hb\s*A1\s*C|Glycated\s*H(?:a?e)moglobin|Glycosylated\s*H(?:a?e)moglobin|A1C)" + SEP + r"([\d.]+)",
        ],
        "unit": "%", "panel": "DIABETES",
    },
    "eAG": {
        "patterns": [r"(?:eAG|Estimated\s*Average\s*Glucose|Average\s*Glucose)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "DIABETES",
    },
    "Fasting_Insulin": {
        "patterns": [r"(?:Fasting\s*Insulin|Insulin(?:\s*Fasting)?)" + SEP + r"([\d.]+)"],
        "unit": "µIU/mL", "panel": "DIABETES",
    },
    "HOMA_IR": {
        "patterns": [r"(?:HOMA[\s\-]*IR|Homeostasis\s*Model\s*Assessment)" + SEP + r"([\d.]+)"],
        "unit": "", "panel": "DIABETES",
    },
    "C_Peptide": {
        "patterns": [r"(?:C[\s\-]*Peptide|Connecting\s*Peptide)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "DIABETES",
    },
    "Microalbumin_24hr": {
        "patterns": [r"(?:Microalbumin(?:uria)?\s*24\s*Hr|24\s*Hr\s*Microalbumin)" + SEP + r"([\d.]+)"],
        "unit": "mg/24hr", "panel": "DIABETES",
    },

    # ========================================================================
    # TFT — Thyroid Function Tests
    # ========================================================================
    "TSH": {
        "patterns": [
            r"(?:TSH|Thyroid\s*Stimulating\s*Hormone|Thyrotropin)" + SEP + r"([\d.]+)",
        ],
        "unit": "µIU/mL", "panel": "TFT",
    },
    "Free_T3": {
        "patterns": [r"(?:Free\s*T3|FT3|Free\s*Tri[\s\-]*iodothyronine)" + SEP + r"([\d.]+)"],
        "unit": "pg/mL", "panel": "TFT",
    },
    "Total_T3": {
        "patterns": [
            r"(?:Total\s*T3|T3[\s\-]*Total|Tri[\s\-]*iodothyronine)(?!\s*Free)" + SEP + r"([\d.]+)",
        ],
        "unit": "ng/dL", "panel": "TFT",
    },
    "Free_T4": {
        "patterns": [r"(?:Free\s*T4|FT4|Free\s*Thyroxine)" + SEP + r"([\d.]+)"],
        "unit": "ng/dL", "panel": "TFT",
    },
    "Total_T4": {
        "patterns": [
            r"(?:Total\s*T4|T4[\s\-]*Total|Thyroxine)(?!\s*Free)" + SEP + r"([\d.]+)",
        ],
        "unit": "µg/dL", "panel": "TFT",
    },
    "Anti_TPO": {
        "patterns": [
            r"(?:Anti[\s\-]*TPO|Anti[\s\-]*Thyroid\s*Peroxidase|TPOAb|Anti[\s\-]*Microsomal)" + SEP + r"([\d.]+)",
        ],
        "unit": "IU/mL", "panel": "TFT",
    },
    "Anti_Thyroglobulin": {
        "patterns": [r"(?:Anti[\s\-]*Thyroglobulin|TgAb|Anti[\s\-]*Tg)" + SEP + r"([\d.]+)"],
        "unit": "IU/mL", "panel": "TFT",
    },
    "TSH_Receptor_Ab": {
        "patterns": [r"(?:TSH\s*Receptor\s*Antibody|TRAb|TSHR\s*Ab)" + SEP + r"([\d.]+)"],
        "unit": "IU/L", "panel": "TFT",
    },
    "Thyroglobulin": {
        "patterns": [r"(?:Thyroglobulin|Tg)(?!\s*Ab)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "TFT",
    },
    "Calcitonin": {
        "patterns": [r"(?:Calcitonin)" + SEP + r"([\d.]+)"],
        "unit": "pg/mL", "panel": "TFT",
    },

    # ========================================================================
    # VIT_D — Vitamin D
    # ========================================================================
    "Vitamin_D_25OH": {
        "patterns": [
            r"(?:Vitamin\s*D[\s\-]*25[\s\-]*OH|25[\s\-]*OH[\s\-]*Vitamin\s*D|25\s*Hydroxy\s*Vitamin\s*D|25\s*\(OH\)\s*D|VIT\.?\s*D)" + SEP + r"([\d.]+)",
            r"(?:Calcidiol)" + SEP + r"([\d.]+)",
        ],
        "unit": "ng/mL", "panel": "VIT_D",
    },
    "Vitamin_D3": {
        "patterns": [r"(?:Vitamin\s*D3|VitD3|Cholecalciferol\s*D3)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "VIT_D",
    },
    "Vitamin_D2": {
        "patterns": [r"(?:Vitamin\s*D2|VitD2|Ergocalciferol)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "VIT_D",
    },
    "PTH": {
        "patterns": [r"(?:PTH|Parathyroid\s*Hormone|Intact\s*PTH|iPTH)" + SEP + r"([\d.]+)"],
        "unit": "pg/mL", "panel": "VIT_D",
    },

    # ========================================================================
    # VIT_B12 — Vitamin B12 / Folate
    # ========================================================================
    "Vitamin_B12": {
        "patterns": [
            r"(?:Vitamin\s*B[\s\-]?12|Vit\.?\s*B12|Cyanocobalamin|Cobalamin)" + SEP + r"([\d.]+)",
        ],
        "unit": "pg/mL", "panel": "VIT_B12",
    },
    "Serum_Folate": {
        "patterns": [
            r"(?:Folate|Folic\s*Acid|Serum\s*Folate|Serum\s*Folic\s*Acid|Vitamin\s*B[\s\-]?9)" + SEP + r"([\d.]+)",
        ],
        "unit": "ng/mL", "panel": "VIT_B12",
    },
    "RBC_Folate": {
        "patterns": [r"(?:RBC\s*Folate|Red\s*Cell\s*Folate)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "VIT_B12",
    },
    "Homocysteine": {
        "patterns": [r"(?:Homocysteine|Hcy|Total\s*Homocysteine)" + SEP + r"([\d.]+)"],
        "unit": "µmol/L", "panel": "VIT_B12",
    },
    "MMA": {
        "patterns": [r"(?:MMA|Methylmalonic\s*Acid)" + SEP + r"([\d.]+)"],
        "unit": "nmol/mL", "panel": "VIT_B12",
    },

    # ========================================================================
    # URINE_RM — Urine Routine & Microscopy
    # ========================================================================
    "Urine_Color": {
        "patterns": [r"(?:Colour|Color|Urine\s*Colou?r)" + SEP + r"([A-Za-z]+)"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Appearance": {
        "patterns": [r"(?:Appearance|Clarity|Turbidity)" + SEP + r"([A-Za-z]+)"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_pH": {
        "patterns": [r"(?:pH|Urine\s*pH|Reaction)" + SEP + r"([\d.]+)"],
        "unit": "", "panel": "URINE_RM",
    },
    "Urine_Specific_Gravity": {
        "patterns": [r"(?:Specific\s*Gravity|SpGr|Sp\.?\s*Gr\.?)" + SEP + r"(1\.0[\d]{2,3})"],
        "unit": "", "panel": "URINE_RM",
    },
    "Urine_Protein": {
        "patterns": [
            r"(?:Protein(?:\s*\(albumin\))?)" + SEP + QUAL,
        ],
        "unit": "mg/dL", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Glucose": {
        "patterns": [
            r"(?:Glucose(?:\s*\(reducing\s*substance\))?|Reducing\s*Substance)" + SEP + QUAL,
        ],
        "unit": "mg/dL", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Ketones": {
        "patterns": [r"(?:Ketones?(?:\s*Bodies?)?)" + SEP + QUAL],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Blood": {
        "patterns": [r"(?:Blood|Occult\s*Blood|H(?:a?e)moglobin\s*\(urine\))" + SEP + QUAL],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Nitrite": {
        "patterns": [r"(?:Nitrites?)" + SEP + r"(Negative|Positive|\+{1,4})"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Leukocyte_Esterase": {
        "patterns": [r"(?:Leukocyte\s*Esterase|WBC\s*Esterase)" + SEP + QUAL],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Bilirubin": {
        "patterns": [r"(?:Bilirubin\s*\(urine\)|Urine\s*Bilirubin)" + SEP + r"(Nil|Negative|Positive|\+{1,4})"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Urobilinogen": {
        "patterns": [r"(?:Urobilinogen)" + SEP + r"(Normal|Negative|Positive|\+{1,4}|[\d.]+)"],
        "unit": "EU/dL", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Pus_Cells": {
        "patterns": [
            r"(?:Pus\s*Cells?|WBC\s*\(urine\))\s*[:\-]?\s*(\d+[\-–]?\d*)\s*/\s*(?:hpf|HPF)",
            r"(?:Pus\s*Cells?|WBC\s*\(urine\))" + SEP + r"([\d.]+)",
        ],
        "unit": "/HPF", "panel": "URINE_RM",
    },
    "Urine_RBC": {
        "patterns": [
            r"(?:RBC\s*\(urine\)|Red\s*Blood\s*Cells?\s*\(urine\))\s*[:\-]?\s*(\d+[\-–]?\d*)\s*/\s*(?:hpf|HPF)",
            r"(?:RBC\s*\(urine\)|Red\s*Blood\s*Cells?\s*\(urine\))" + SEP + r"([\d.]+)",
        ],
        "unit": "/HPF", "panel": "URINE_RM",
    },
    "Urine_Epithelial_Cells": {
        "patterns": [r"(?:Epithelial\s*Cells?)" + SEP + r"(\d+[\-–]?\d*)"],
        "unit": "/HPF", "panel": "URINE_RM",
    },
    "Urine_Casts": {
        "patterns": [r"(?:Casts?)\s*[:\-]?\s*(Nil|Absent|Present|[\w\s]+Casts?)"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Crystals": {
        "patterns": [r"(?:Crystals?)\s*[:\-]?\s*(Nil|Absent|Present|[\w\s]+Crystals?)"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },
    "Urine_Bacteria": {
        "patterns": [r"(?:Bacteria(?:l)?|Bacteriuria)\s*[:\-]?\s*(Nil|Absent|Present|Few|Moderate|Many)"],
        "unit": "", "panel": "URINE_RM", "text_value": True,
    },

    # ========================================================================
    # RHEUMA — Rheumatology Markers
    # ========================================================================
    "RA_Factor": {
        "patterns": [r"(?:RA\s*Factor|Rheumatoid\s*(?:Arthritis\s*)?Factor|\bRF\b)" + SEP + r"([\d.]+)"],
        "unit": "IU/mL", "panel": "RHEUMA",
    },
    "Anti_CCP": {
        "patterns": [r"(?:Anti[\s\-]*CCP|Anti[\s\-]*Cyclic\s*Citrullinated\s*Peptide|ACPA)" + SEP + r"([\d.]+)"],
        "unit": "U/mL", "panel": "RHEUMA",
    },
    "CRP": {
        "patterns": [r"(?:CRP|C[\s\-]*Reactive\s*Protein)(?!\s*hs)" + SEP + r"([\d.]+)"],
        "unit": "mg/L", "panel": "RHEUMA",
    },
    "hs_CRP": {
        "patterns": [r"(?:hs[\s\-]*CRP|High\s*Sensitivity\s*CRP|hsCRP)" + SEP + r"([\d.]+)"],
        "unit": "mg/L", "panel": "RHEUMA",
    },
    "ANA": {
        "patterns": [r"(?:ANA|Anti[\s\-]*Nuclear\s*Antibody|Antinuclear\s*Antibody)" + SEP + r"([\d.]+|Positive|Negative|Reactive)"],
        "unit": "titre", "panel": "RHEUMA", "text_value": True,
    },
    "Anti_dsDNA": {
        "patterns": [r"(?:Anti[\s\-]*dsDNA|Anti[\s\-]*Double\s*Stranded\s*DNA|Anti\s*ds\s*DNA)" + SEP + r"([\d.]+)"],
        "unit": "IU/mL", "panel": "RHEUMA",
    },
    "C3_Complement": {
        "patterns": [r"(?:C3\s*Complement|Complement\s*C3|\bC3\b)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "RHEUMA",
    },
    "C4_Complement": {
        "patterns": [r"(?:C4\s*Complement|Complement\s*C4|\bC4\b)" + SEP + r"([\d.]+)"],
        "unit": "mg/dL", "panel": "RHEUMA",
    },
    "ASO_Titre": {
        "patterns": [r"(?:ASO(?:\s*Titre)?|Anti[\s\-]*Streptolysin\s*O)" + SEP + r"([\d.]+)"],
        "unit": "IU/mL", "panel": "RHEUMA",
    },
    "Ferritin": {
        "patterns": [r"(?:Ferritin|Serum\s*Ferritin|S\.?\s*Ferritin)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "RHEUMA",
    },
    "Serum_Iron": {
        "patterns": [r"(?:Serum\s*Iron|S\.?\s*Iron|Iron(?!\s*Binding))(?!\s*Sat)" + SEP + r"([\d.]+)"],
        "unit": "µg/dL", "panel": "RHEUMA",
    },
    "TIBC": {
        "patterns": [r"(?:TIBC|Total\s*Iron[\s\-]*Binding\s*Capacity)" + SEP + r"([\d.]+)"],
        "unit": "µg/dL", "panel": "RHEUMA",
    },
    "Transferrin_Saturation": {
        "patterns": [r"(?:Transferrin\s*Saturation|Iron\s*Saturation|TSAT)" + SEP + r"([\d.]+)"],
        "unit": "%", "panel": "RHEUMA",
    },
    "ANCA_p": {
        "patterns": [r"(?:p[\s\-]*ANCA|MPO[\s\-]*ANCA|Perinuclear\s*ANCA)" + SEP + r"([\d.]+|Positive|Negative)"],
        "unit": "IU/mL", "panel": "RHEUMA", "text_value": True,
    },
    "ANCA_c": {
        "patterns": [r"(?:c[\s\-]*ANCA|PR3[\s\-]*ANCA|Cytoplasmic\s*ANCA)" + SEP + r"([\d.]+|Positive|Negative)"],
        "unit": "IU/mL", "panel": "RHEUMA", "text_value": True,
    },
    "Anti_Ro_SSA": {
        "patterns": [r"(?:Anti[\s\-]*Ro|Anti[\s\-]*SS[\s\-]*A|SSA)" + SEP + r"([\d.]+|Positive|Negative)"],
        "unit": "U/mL", "panel": "RHEUMA", "text_value": True,
    },
    "Anti_La_SSB": {
        "patterns": [r"(?:Anti[\s\-]*La|Anti[\s\-]*SS[\s\-]*B|SSB)" + SEP + r"([\d.]+|Positive|Negative)"],
        "unit": "U/mL", "panel": "RHEUMA", "text_value": True,
    },

    # ========================================================================
    # ONCOLOGY — Tumour Markers
    # ========================================================================
    "PSA_Total": {
        "patterns": [
            r"(?:Total\s*PSA|PSA[\s\-]*Total|Prostate\s*Specific\s*Antigen(?:\s*[\-\s]*Total)?)" + SEP + r"([\d.]+)",
            r"(?:PSA)(?!\s*Free)" + SEP + r"([\d.]+)",
        ],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "PSA_Free": {
        "patterns": [r"(?:Free\s*PSA|PSA[\s\-]*Free|f[\s\-]*PSA)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "PSA_Free_Total_Ratio": {
        "patterns": [r"(?:Free[\s/]*Total\s*PSA\s*Ratio|f[\s/]*t\s*PSA)" + SEP + r"([\d.]+)"],
        "unit": "%", "panel": "ONCOLOGY",
    },
    "CEA": {
        "patterns": [r"(?:CEA|Carcinoembryonic\s*Antigen)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "CA_125": {
        "patterns": [r"(?:CA[\s\-]?125|Cancer\s*Antigen\s*125)" + SEP + r"([\d.]+)"],
        "unit": "U/mL", "panel": "ONCOLOGY",
    },
    "CA_19_9": {
        "patterns": [r"(?:CA[\s\-]?19[\s\-]?9|Cancer\s*Antigen\s*19[\s\-]?9)" + SEP + r"([\d.]+)"],
        "unit": "U/mL", "panel": "ONCOLOGY",
    },
    "CA_15_3": {
        "patterns": [r"(?:CA[\s\-]?15[\s\-]?3|Cancer\s*Antigen\s*15[\s\-]?3)" + SEP + r"([\d.]+)"],
        "unit": "U/mL", "panel": "ONCOLOGY",
    },
    "CA_72_4": {
        "patterns": [r"(?:CA[\s\-]?72[\s\-]?4|TAG[\s\-]?72)" + SEP + r"([\d.]+)"],
        "unit": "U/mL", "panel": "ONCOLOGY",
    },
    "AFP": {
        "patterns": [r"(?:AFP|Alpha[\s\-]*Feto[\s\-]*Protein|Alpha[\s\-]*Fetoprotein)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "Beta_HCG": {
        "patterns": [
            r"(?:(?:Beta|β)[\s\-]*HCG|(?:Beta|β)[\s\-]*Human\s*Chorionic\s*Gonadotropin|Total\s*HCG)" + SEP + r"([\d.]+)",
        ],
        "unit": "mIU/mL", "panel": "ONCOLOGY",
    },
    "NSE": {
        "patterns": [r"(?:NSE|Neuron[\s\-]*Specific\s*Enolase)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "CYFRA_21_1": {
        "patterns": [r"(?:CYFRA[\s\-]?21[\s\-]?1|Cytokeratin\s*Fragment\s*21[\s\-]?1)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "SCC_Antigen": {
        "patterns": [r"(?:SCC|Squamous\s*Cell\s*Carcinoma\s*Antigen)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "ProGRP": {
        "patterns": [r"(?:ProGRP|Pro[\s\-]*Gastrin[\s\-]*Releasing\s*Peptide)" + SEP + r"([\d.]+)"],
        "unit": "pg/mL", "panel": "ONCOLOGY",
    },
    "HE4": {
        "patterns": [r"(?:HE4|Human\s*Epididymis\s*Protein\s*4)" + SEP + r"([\d.]+)"],
        "unit": "pmol/L", "panel": "ONCOLOGY",
    },
    "Chromogranin_A": {
        "patterns": [r"(?:Chromogranin[\s\-]?A|CgA)" + SEP + r"([\d.]+)"],
        "unit": "ng/mL", "panel": "ONCOLOGY",
    },
    "S100_Protein": {
        "patterns": [r"(?:S[\-\s]?100[\s\-]*(?:Protein|B)?)" + SEP + r"([\d.]+)"],
        "unit": "µg/L", "panel": "ONCOLOGY",
    },
}


# ============================================================================
# DERIVED CALCULATIONS
# ============================================================================
def compute_derived(results: Dict[str, Any]) -> Dict[str, Any]:
    """Auto-calculate parameters derivable from already-parsed values."""

    def _add(key: str, panel: str, unit: str, label: str, val_fn):
        if key not in results:
            try:
                val = val_fn()
                if val is not None:
                    results[key] = {
                        "value": round(val, 3), "unit": unit,
                        "panel": panel, "raw_match": f"Calculated: {label}",
                    }
            except Exception:
                pass

    def _v(k):
        entry = results.get(k)
        if entry is None:
            return None
        return entry.get("value") if isinstance(entry, dict) else entry

    # LFT
    _add("Indirect_Bilirubin", "LFT", "mg/dL", "Total − Direct Bilirubin",
         lambda: _v("Total_Bilirubin") - _v("Direct_Bilirubin")
         if _v("Total_Bilirubin") is not None and _v("Direct_Bilirubin") is not None else None)
    _add("Globulin", "LFT", "g/dL", "Total Protein − Albumin",
         lambda: _v("Total_Protein") - _v("Albumin")
         if _v("Total_Protein") is not None and _v("Albumin") is not None else None)
    if _v("Albumin") and _v("Globulin") and _v("Globulin") > 0:
        _add("AG_Ratio", "LFT", "ratio", "Albumin / Globulin",
             lambda: _v("Albumin") / _v("Globulin"))

    # KFT
    if _v("BUN") and _v("Serum_Creatinine") and _v("Serum_Creatinine") > 0:
        _add("BUN_Creatinine_Ratio", "KFT", "ratio", "BUN / Creatinine",
             lambda: _v("BUN") / _v("Serum_Creatinine"))

    # Lipid
    _add("VLDL_Cholesterol", "LIPID", "mg/dL", "Triglycerides / 5",
         lambda: _v("Triglycerides") / 5 if _v("Triglycerides") is not None else None)

    def _ldl():
        tc = _v("Total_Cholesterol")
        hdl = _v("HDL_Cholesterol")
        vldl = _v("VLDL_Cholesterol")
        tg = _v("Triglycerides")
        if tc is None or hdl is None:
            return None
        vldl_val = vldl if vldl is not None else (tg / 5 if tg is not None else None)
        return tc - hdl - vldl_val if vldl_val is not None else None

    _add("LDL_Cholesterol", "LIPID", "mg/dL", "Friedewald: TC − HDL − VLDL", _ldl)
    _add("Non_HDL_Cholesterol", "LIPID", "mg/dL", "Total Cholesterol − HDL",
         lambda: _v("Total_Cholesterol") - _v("HDL_Cholesterol")
         if _v("Total_Cholesterol") is not None and _v("HDL_Cholesterol") is not None else None)
    if _v("Total_Cholesterol") and _v("HDL_Cholesterol") and _v("HDL_Cholesterol") > 0:
        _add("TC_HDL_Ratio", "LIPID", "ratio", "TC / HDL",
             lambda: _v("Total_Cholesterol") / _v("HDL_Cholesterol"))
    if _v("LDL_Cholesterol") and _v("HDL_Cholesterol") and _v("HDL_Cholesterol") > 0:
        _add("LDL_HDL_Ratio", "LIPID", "ratio", "LDL / HDL",
             lambda: _v("LDL_Cholesterol") / _v("HDL_Cholesterol"))

    # Diabetes
    if _v("Fasting_Blood_Glucose") and _v("Fasting_Insulin"):
        _add("HOMA_IR", "DIABETES", "", "FBG × Insulin / 405",
             lambda: (_v("Fasting_Blood_Glucose") * _v("Fasting_Insulin")) / 405.0)

    # Oncology
    if _v("PSA_Free") and _v("PSA_Total") and _v("PSA_Total") > 0:
        _add("PSA_Free_Total_Ratio", "ONCOLOGY", "%", "(Free / Total PSA) × 100",
             lambda: (_v("PSA_Free") / _v("PSA_Total")) * 100)

    # Rheumatology
    if _v("Serum_Iron") and _v("TIBC") and _v("TIBC") > 0:
        _add("Transferrin_Saturation", "RHEUMA", "%", "(Iron / TIBC) × 100",
             lambda: (_v("Serum_Iron") / _v("TIBC")) * 100)

    return results


# ============================================================================
# PANEL → PARAM KEY MAP (built at import time)
# ============================================================================
PANEL_PARAMETER_KEYS: Dict[str, list] = {}
for _k, _cfg in PARAMETER_PATTERNS.items():
    _p = _cfg.get("panel", "Other")
    PANEL_PARAMETER_KEYS.setdefault(_p, []).append(_k)


# ============================================================================
# TEXT PREPROCESSING
# ============================================================================
def preprocess_text(text: str) -> str:
    """Normalise OCR/PDF text for reliable regex matching."""
    text = text.replace("\t", " ")
    text = re.sub(r"[\u2013\u2014\u2212]", "-", text)   # unicode dashes → hyphen
    text = re.sub(r"[ ]{2,}", " ", text)                  # collapse spaces
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text


# ============================================================================
# OCR / PDF EXTRACTION
# ============================================================================
def extract_text_from_image(image: Image.Image) -> str:
    if pytesseract is None:
        return "Error: pytesseract not installed."
    try:
        image = image.convert("L")
        text = pytesseract.image_to_string(image, config="--psm 6 --oem 3")
        return preprocess_text(text)
    except Exception as e:
        return f"OCR Error: {e}"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    all_text = ""
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        all_text += t + "\n"
                    for table in page.extract_tables():
                        for row in table:
                            if row:
                                all_text += " ".join(str(c) if c else "" for c in row) + "\n"
        except Exception:
            pass

    if len(all_text.strip()) < 50:
        try:
            from pdf2image import convert_from_bytes
            for img in convert_from_bytes(pdf_bytes, dpi=300):
                all_text += extract_text_from_image(img) + "\n"
        except Exception as e:
            all_text += f"\nOCR fallback error: {e}"

    return preprocess_text(all_text)


# ============================================================================
# CORE PARSING
# ============================================================================
def parse_parameters(text: str) -> Dict[str, Any]:
    """
    Parse ALL registered parameters from OCR / pasted text.

    Returns
    -------
    {param_key: {"value": float|str, "unit": str, "panel": str, "raw_match": str}}
    """
    results: Dict[str, Any] = {}
    for key, cfg in PARAMETER_PATTERNS.items():
        is_text = cfg.get("text_value", False)
        for pattern in cfg["patterns"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    raw = m.group(1).strip()
                    value = raw if is_text else float(raw)
                    results[key] = {
                        "value": value,
                        "unit": cfg["unit"],
                        "panel": cfg.get("panel", "Other"),
                        "raw_match": m.group(0).strip(),
                    }
                    break
                except (ValueError, IndexError):
                    continue

    results = compute_derived(results)
    return results


def parse_panel(panel_key: str, text: str) -> Dict[str, Any]:
    """Parse only parameters belonging to a specific panel."""
    keys = PANEL_PARAMETER_KEYS.get(panel_key, [])
    all_parsed = parse_parameters(text)
    return {k: v for k, v in all_parsed.items() if k in keys}


def group_parameters(parsed: Dict[str, Any]) -> Dict[str, Dict]:
    """Group a flat parsed dict into {panel_key: {param: data}} sub-dicts."""
    groups: Dict[str, Dict] = {p: {} for p in PANEL_LABELS}
    for key, data in parsed.items():
        panel = data.get("panel", "Other") if isinstance(data, dict) else "Other"
        groups.setdefault(panel, {})[key] = data
    return {k: v for k, v in groups.items() if v}


# ============================================================================
# PATIENT INFO EXTRACTION
# ============================================================================
def extract_patient_info(text: str) -> Dict[str, str]:
    """Extract patient demographic information from text."""
    info: Dict[str, str] = {}
    patterns = {
        "name":             r"(?:Patient\s*Name|Name|Patient)\s*[:\-]?\s*([A-Za-z\s.]+?)(?:\n|$|Age|Sex|Gender)",
        "age":              r"(?:Age)\s*[:\-]?\s*(\d+)\s*(?:years?|yrs?|Y)?",
        "sex":              r"(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)\b",
        "date":             r"(?:Date|Collection\s*Date|Report\s*Date|Sample\s*Date)\s*[:\-]?\s*([\d/\-\.]+)",
        "lab_ref":          r"(?:Lab\s*No|Lab\s*ID|Sample\s*(?:No|ID)|Report\s*(?:No|ID)|Barcode)\s*[:\-]?\s*([\w\-/]+)",
        "referring_doctor": r"(?:Ref(?:erring)?\s*(?:Doctor|Dr)|Dr\.?)\s*[:\-]?\s*([A-Za-z\s.]+?)(?:\n|$)",
    }
    for field, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if field == "sex":
                val = "Male" if val.upper() in ("M", "MALE") else "Female"
            info[field] = val
    return info


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def process_uploaded_file(uploaded_file) -> Tuple[str, Dict, Dict, Dict]:
    """
    Process an uploaded PDF or image lab report.

    Returns
    -------
    extracted_text : str
    parameters     : dict  — flat {param_key: {value, unit, panel, raw_match}}
    grouped        : dict  — {panel_key: {param_key: ...}}
    patient_info   : dict  — {name, age, sex, date, lab_ref, referring_doctor}
    """
    file_type  = uploaded_file.type
    file_bytes = uploaded_file.read()
    extracted_text = ""

    if "pdf" in file_type:
        extracted_text = extract_text_from_pdf(file_bytes)
    elif "image" in file_type or file_type in ("image/jpeg", "image/jpg", "image/png"):
        extracted_text = extract_text_from_image(Image.open(io.BytesIO(file_bytes)))
    else:
        extracted_text = "Unsupported file format."

    parameters   = parse_parameters(extracted_text)
    grouped      = group_parameters(parameters)
    patient_info = extract_patient_info(extracted_text)

    return extracted_text, parameters, grouped, patient_info
