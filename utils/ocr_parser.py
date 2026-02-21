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
    # Complete Blood Count (CBC)
    'RBC': {
        'patterns': [
            r'(?:RBC|Red\s*Blood\s*Cell(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
            r'(?:Erythrocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10¹²/L',
        'alt_units': ['million/µL', 'M/µL', '10^12/L']
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
        'unit': 'x10⁹/L', 'alt_units': ['K/µL', '10^9/L']
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
        'unit': 'x10⁹/L', 'alt_units': ['K/µL', '10^9/L']
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
        'unit': 'x10⁹/L', 'alt_units': ['cells/µL']
    },
    'ALC': {
        'patterns': [r'(?:ALC|Absolute\s*Lymphocyte\s*Count)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'x10⁹/L', 'alt_units': ['cells/µL']
    },
    
    # Liver Function Tests (LFT)
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
    'Indirect_Bilirubin': {
        'patterns': [r'(?:Indirect\s*Bilirubin|Unconjugated\s*Bilirubin|I[\.\s]*Bili(?:rubin)?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mg/dL']
    },
    'Albumin': {
        'patterns': [r'(?:Albumin|ALB)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'g/dL', 'alt_units': ['g/dL', 'g/L']
    },
    'Total_Protein': {
        'patterns': [r'(?:Total\s*Protein|TP|Protein\s*Total)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'g/dL', 'alt_units': ['g/dL', 'g/L']
    },
    'Globulin': {
        'patterns': [r'(?:Globulin|GLOB)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'g/dL', 'alt_units': ['g/dL']
    },
    'A_G_Ratio': {
        'patterns': [r'(?:A[/:]G\s*Ratio|Albumin[/:]Globulin\s*Ratio)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ratio', 'alt_units': ['ratio']
    },
    'GGT': {
        'patterns': [r'(?:GGT|Gamma[\s\-]*(?:Glutamyl)?[\s\-]*Transferase|γ[\s\-]*GT)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L']
    },
    'LDH': {
        'patterns': [r'(?:LDH|Lactate\s*Dehydrogenase|Lactic\s*Acid\s*Dehydrogenase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L']
    },
    
    # Kidney Function Tests (KFT / Renal Panel)
    'Creatinine': {
        'patterns': [r'(?:Creatinine|Creat|CREA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['µmol/L', 'umol/L']
    },
    'BUN': {
        'patterns': [r'(?:BUN|Blood\s*Urea\s*Nitrogen|Urea\s*Nitrogen)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Urea': {
        'patterns': [r'(?:Urea|Blood\s*Urea)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Uric_Acid': {
        'patterns': [r'(?:Uric\s*Acid|UA|Urate)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['µmol/L', 'umol/L']
    },
    'eGFR': {
        'patterns': [r'(?:eGFR|Estimated\s*GFR|GFR\s*Estimated)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mL/min/1.73m²', 'alt_units': ['mL/min']
    },
    'Cystatin_C': {
        'patterns': [r'(?:Cystatin\s*C)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/L', 'alt_units': ['mg/L']
    },
    
    # Electrolytes (part of KFT)
    'Sodium': {
        'patterns': [r'(?:Sodium|Na[⁺+]?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mEq/L', 'alt_units': ['mmol/L']
    },
    'Potassium': {
        'patterns': [r'(?:Potassium|K[⁺+]?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mEq/L', 'alt_units': ['mmol/L']
    },
    'Chloride': {
        'patterns': [r'(?:Chloride|Cl[⁻-]?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mEq/L', 'alt_units': ['mmol/L']
    },
    'Bicarbonate': {
        'patterns': [r'(?:Bicarbonate|HCO3[⁻-]?|Total\s*CO2|TCO2)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mEq/L', 'alt_units': ['mmol/L']
    },
    'Calcium': {
        'patterns': [r'(?:Calcium|Ca[²+]?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Phosphorus': {
        'patterns': [r'(?:Phosphorus|Phosphate|PO4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Magnesium': {
        'patterns': [r'(?:Magnesium|Mg[²+]?)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    
    # Lipid Profile
    'Total_Cholesterol': {
        'patterns': [r'(?:Total\s*Cholesterol|T[\.\s]*Chol|Cholesterol\s*Total)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'HDL_Cholesterol': {
        'patterns': [r'(?:HDL[\s\-]*Cholesterol|HDL[\s\-]*C|HDL)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'LDL_Cholesterol': {
        'patterns': [r'(?:LDL[\s\-]*Cholesterol|LDL[\s\-]*C|LDL)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'VLDL_Cholesterol': {
        'patterns': [r'(?:VLDL[\s\-]*Cholesterol|VLDL[\s\-]*C|VLDL)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Triglycerides': {
        'patterns': [r'(?:Triglycerides|TG|TGL|TRIG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Non_HDL_Cholesterol': {
        'patterns': [r'(?:Non[\s\-]*HDL[\s\-]*Cholesterol|Non[\s\-]*HDL)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'TC_HDL_Ratio': {
        'patterns': [r'(?:TC[/:]HDL\s*Ratio|Cholesterol[/:]HDL\s*Ratio|Total[/:]HDL)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ratio', 'alt_units': ['ratio']
    },
    'LDL_HDL_Ratio': {
        'patterns': [r'(?:LDL[/:]HDL\s*Ratio)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ratio', 'alt_units': ['ratio']
    },
    'ApoA1': {
        'patterns': [r'(?:Apo[\s\-]*A[\s\-]*I|Apolipoprotein\s*A[\s\-]*I)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['g/L']
    },
    'ApoB': {
        'patterns': [r'(?:Apo[\s\-]*B|Apolipoprotein\s*B)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['g/L']
    },
    'Lp_a': {
        'patterns': [r'(?:Lipoprotein[\s\(]*a[\s\)]*|Lp[\s\(]*a[\s\)]*|LPA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['nmol/L']
    },
    
    # Blood Sugar / Glucose
    'Fasting_Glucose': {
        'patterns': [r'(?:Fasting\s*Glucose|Fasting\s*Blood\s*Sugar|FBS|FBG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Random_Glucose': {
        'patterns': [r'(?:Random\s*Glucose|Random\s*Blood\s*Sugar|RBS|RBG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Post_Prandial_Glucose': {
        'patterns': [r'(?:Post[\s\-]*Prandial\s*Glucose|PP[\s\-]*Glucose|PPBS|PPBG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'HbA1c': {
        'patterns': [r'(?:HbA1c|HbA1C|Glycated\s*Hemoglobin|Glycosylated\s*Hemoglobin|A1C)\s*[:\-]?\s*([\d.]+)'],
        'unit': '%', 'alt_units': ['%', 'mmol/mol']
    },
    'Estimated_Average_Glucose': {
        'patterns': [r'(?:eAG|Estimated\s*Average\s*Glucose)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Insulin': {
        'patterns': [r'(?:Insulin|Fasting\s*Insulin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'µIU/mL', 'alt_units': ['mIU/L', 'pmol/L']
    },
    'C_Peptide': {
        'patterns': [r'(?:C[\s\-]*Peptide|Cpeptide)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['nmol/L']
    },
    'HOMA_IR': {
        'patterns': [r'(?:HOMA[\s\-]*IR|HOMA\s*Index)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'index', 'alt_units': ['index']
    },
    
    # Urine Routine & Microscopy (URINE R/M)
    'Urine_Color': {
        'patterns': [r'(?:Color|Colour)\s*[:\-]?\s*([A-Za-z\s]+?)(?:\n|$|Appearance)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Appearance': {
        'patterns': [r'(?:Appearance)\s*[:\-]?\s*([A-Za-z\s]+?)(?:\n|$|pH)'],
        'unit': '', 'alt_units': []
    },
    'Urine_pH': {
        'patterns': [r'(?:pH|Reaction)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pH', 'alt_units': []
    },
    'Urine_Specific_Gravity': {
        'patterns': [r'(?:Specific\s*Gravity|Sp[\.\s]*Gr|SG)\s*[:\-]?\s*([\d.]+)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Protein': {
        'patterns': [r'(?:Protein|Albumin)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Glucose)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Glucose': {
        'patterns': [r'(?:Glucose|Sugar)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Ketone)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Ketones': {
        'patterns': [r'(?:Ketone(?:s)?)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Bilirubin)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Bilirubin': {
        'patterns': [r'(?:Bilirubin)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Urobilinogen)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Urobilinogen': {
        'patterns': [r'(?:Urobilinogen)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Blood)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Blood': {
        'patterns': [r'(?:Blood|RBC\s*in\s*urine)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Nitrite)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Nitrite': {
        'patterns': [r'(?:Nitrite(?:s)?)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Leukocyte)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Leukocyte_Esterase': {
        'patterns': [r'(?:Leukocyte[\s\-]*Esterase|WBC\s*in\s*urine|Pus\s*Cells)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$)'],
        'unit': '', 'alt_units': []
    },
    'Urine_RBC': {
        'patterns': [r'(?:RBC|Red\s*Blood\s*Cells)\s*[:\-]?\s*([\d\s-]+)(?:\s*/hpf|\s*cells)'],
        'unit': '/hpf', 'alt_units': ['cells/HPF']
    },
    'Urine_WBC': {
        'patterns': [r'(?:WBC|Pus\s*Cells|White\s*Blood\s*Cells)\s*[:\-]?\s*([\d\s-]+)(?:\s*/hpf|\s*cells)'],
        'unit': '/hpf', 'alt_units': ['cells/HPF']
    },
    'Urine_Epithelial_Cells': {
        'patterns': [r'(?:Epithelial\s*Cells)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Casts)'],
        'unit': '/hpf', 'alt_units': ['cells/HPF']
    },
    'Urine_Casts': {
        'patterns': [r'(?:Casts)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Crystals)'],
        'unit': '/lpf', 'alt_units': []
    },
    'Urine_Crystals': {
        'patterns': [r'(?:Crystals)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Bacteria)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Bacteria': {
        'patterns': [r'(?:Bacteria)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$|Yeast)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Yeast_Cells': {
        'patterns': [r'(?:Yeast(?:\s*Cells)?)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$)'],
        'unit': '', 'alt_units': []
    },
    'Urine_Protein_Creatinine_Ratio': {
        'patterns': [r'(?:Protein[/:]Creatinine\s*Ratio|PCR|UPCR)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/g', 'alt_units': ['mg/mmol']
    },
    'Urine_Albumin_Creatinine_Ratio': {
        'patterns': [r'(?:Albumin[/:]Creatinine\s*Ratio|ACR|UACR)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/g', 'alt_units': ['mg/mmol', 'µg/mg']
    },
    'Microalbumin': {
        'patterns': [r'(?:Microalbumin|Urinary\s*Albumin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/L', 'alt_units': ['mg/24h']
    },
    
    # Thyroid Function Tests (TFT)
    'TSH': {
        'patterns': [r'(?:TSH|Thyroid\s*Stimulating\s*Hormone|Thyrotropin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'µIU/mL', 'alt_units': ['mIU/L', 'mU/L']
    },
    'T3': {
        'patterns': [r'(?:T3|Triiodothyronine|Total\s*T3|TT3)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/dL', 'alt_units': ['nmol/L', 'pg/mL']
    },
    'T4': {
        'patterns': [r'(?:T4|Thyroxine|Total\s*T4|TT4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'µg/dL', 'alt_units': ['nmol/L']
    },
    'Free_T3': {
        'patterns': [r'(?:Free\s*T3|FT3)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pg/mL', 'alt_units': ['pmol/L']
    },
    'Free_T4': {
        'patterns': [r'(?:Free\s*T4|FT4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/dL', 'alt_units': ['pmol/L']
    },
    'Reverse_T3': {
        'patterns': [r'(?:Reverse\s*T3|rT3)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/dL', 'alt_units': ['nmol/L']
    },
    'T3_Uptake': {
        'patterns': [r'(?:T3\s*Uptake|T3U)\s*[:\-]?\s*([\d.]+)'],
        'unit': '%', 'alt_units': ['%']
    },
    'Thyroglobulin': {
        'patterns': [r'(?:Thyroglobulin|Tg)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'Anti_TPO': {
        'patterns': [r'(?:Anti[\s\-]*TPO|TPO[\s\-]*Ab|Thyroid\s*Peroxidase\s*Antibod(?:y|ies))\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/mL', 'alt_units': ['U/mL']
    },
    'Anti_Thyroglobulin': {
        'patterns': [r'(?:Anti[\s\-]*Thyroglobulin|TG[\s\-]*Ab|Anti[\s\-]*Tg)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/mL', 'alt_units': ['U/mL']
    },
    'TSH_Receptor_Antibody': {
        'patterns': [r'(?:TRAb|TSH\s*Receptor\s*Antibod(?:y|ies)|TSI|Thyroid\s*Stimulating\s*Immunoglobulin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L']
    },
    
    # Rheumatology / Autoimmune Markers
    'RF': {
        'patterns': [r'(?:RF|Rheumatoid\s*Factor)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/mL', 'alt_units': ['U/mL']
    },
    'Anti_CCP': {
        'patterns': [r'(?:Anti[\s\-]*CCP|CCP\s*Antibod(?:y|ies)|Cyclic\s*Citrullinated\s*Peptide)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['IU/mL']
    },
    'ANA': {
        'patterns': [r'(?:ANA|Antinuclear\s*Antibod(?:y|ies))\s*[:\-]?\s*([A-Za-z\s\d:]+?)(?:\n|$|Pattern)'],
        'unit': 'titer', 'alt_units': []
    },
    'ANA_Pattern': {
        'patterns': [r'(?:ANA\s*Pattern|Pattern)\s*[:\-]?\s*([A-Za-z\s,]+?)(?:\n|$)'],
        'unit': '', 'alt_units': []
    },
    'Anti_dS_DNA': {
        'patterns': [r'(?:Anti[\s\-]*dsDNA|dsDNA\s*Antibod(?:y|ies)|Double[\s\-]*Stranded\s*DNA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/mL', 'alt_units': ['U/mL']
    },
    'Anti_Smith': {
        'patterns': [r'(?:Anti[\s\-]*Smith|Sm\s*Antibod(?:y|ies)|Smith\s*Antibod(?:y|ies))\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['AU/mL']
    },
    'Anti_Phospholipid_IgG': {
        'patterns': [r'(?:Anti[\s\-]*Phospholipid[\s\-]*IgG|aPL[\s\-]*IgG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'GPL', 'alt_units': ['U/mL']
    },
    'Anti_Phospholipid_IgM': {
        'patterns': [r'(?:Anti[\s\-]*Phospholipid[\s\-]*IgM|aPL[\s\-]*IgM)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'MPL', 'alt_units': ['U/mL']
    },
    'Anti_Cardiolipin_IgG': {
        'patterns': [r'(?:Anti[\s\-]*Cardiolipin[\s\-]*IgG|aCL[\s\-]*IgG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'GPL', 'alt_units': ['U/mL']
    },
    'Anti_Cardiolipin_IgM': {
        'patterns': [r'(?:Anti[\s\-]*Cardiolipin[\s\-]*IgM|aCL[\s\-]*IgM)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'MPL', 'alt_units': ['U/mL']
    },
    'Lupus_Anticoagulant': {
        'patterns': [r'(?:Lupus\s*Anticoagulant|LA)\s*[:\-]?\s*([A-Za-z\s]+?)(?:\n|$)'],
        'unit': '', 'alt_units': []
    },
    'Beta_2_Glycoprotein_IgG': {
        'patterns': [r'(?:Beta[\s\-]*2[\s\-]*Glycoprotein[\s\-]*IgG|β2[\s\-]*GPI[\s\-]*IgG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['AU/mL']
    },
    'Beta_2_Glycoprotein_IgM': {
        'patterns': [r'(?:Beta[\s\-]*2[\s\-]*Glycoprotein[\s\-]*IgM|β2[\s\-]*GPI[\s\-]*IgM)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['AU/mL']
    },
    'ESR_Rheumatology': {
        'patterns': [r'(?:ESR|Erythrocyte\s*Sedimentation\s*Rate)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mm/hr', 'alt_units': ['mm/hr']
    },
    'CRP': {
        'patterns': [r'(?:CRP|C[\s\-]*Reactive\s*Protein)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/L', 'alt_units': ['mg/dL']
    },
    'hs_CRP': {
        'patterns': [r'(?:hs[\s\-]*CRP|High\s*Sensitivity\s*CRP)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/L', 'alt_units': ['mg/dL']
    },
    'Complement_C3': {
        'patterns': [r'(?:C3|Complement\s*C3)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['g/L']
    },
    'Complement_C4': {
        'patterns': [r'(?:C4|Complement\s*C4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['g/L']
    },
    'ASO': {
        'patterns': [r'(?:ASO|ASLO|Anti[\s\-]*Streptolysin[\s\-]*O)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/mL', 'alt_units': ['U/mL', 'Todd units']
    },
    'HLA_B27': {
        'patterns': [r'(?:HLA[\s\-]*B27|B27)\s*[:\-]?\s*([A-Za-z\s\+-]+?)(?:\n|$)'],
        'unit': '', 'alt_units': []
    },
    
    # Oncology / Tumor Markers
    'AFP': {
        'patterns': [r'(?:AFP|Alpha[\s\-]*Fetoprotein|α[\s\-]*Fetoprotein)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L', 'IU/mL']
    },
    'CEA': {
        'patterns': [r'(?:CEA|Carcinoembryonic\s*Antigen)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'CA_125': {
        'patterns': [r'(?:CA[\s\-]*125|Cancer\s*Antigen[\s\-]*125)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['kU/L']
    },
    'CA_19_9': {
        'patterns': [r'(?:CA[\s\-]*19[\s\-]*9|CA[\s\-]*19-9|Cancer\s*Antigen[\s\-]*19-9)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['kU/L']
    },
    'CA_15_3': {
        'patterns': [r'(?:CA[\s\-]*15[\s\-]*3|CA[\s\-]*15-3|Cancer\s*Antigen[\s\-]*15-3)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['kU/L']
    },
    'CA_72_4': {
        'patterns': [r'(?:CA[\s\-]*72[\s\-]*4|CA[\s\-]*72-4|Cancer\s*Antigen[\s\-]*72-4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['kU/L']
    },
    'CA_27_29': {
        'patterns': [r'(?:CA[\s\-]*27[\s\-]*29|CA[\s\-]*27-29)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'U/mL', 'alt_units': ['kU/L']
    },
    'PSA': {
        'patterns': [r'(?:PSA|Prostate[\s\-]*Specific\s*Antigen|Total\s*PSA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'Free_PSA': {
        'patterns': [r'(?:Free\s*PSA|fPSA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'PSA_Ratio': {
        'patterns': [r'(?:Free[/:]Total\s*PSA\s*Ratio|PSA\s*Ratio|F[/:]T\s*PSA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ratio', 'alt_units': ['%']
    },
    'Beta_HCG': {
        'patterns': [r'(?:Beta[\s\-]*hCG|β[\s\-]*hCG|hCG\s*Beta)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mIU/mL', 'alt_units': ['IU/L']
    },
    'LDH_Oncology': {
        'patterns': [r'(?:LDH|Lactate\s*Dehydrogenase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L']
    },
    'NSE': {
        'patterns': [r'(?:NSE|Neuron[\s\-]*Specific\s*Enolase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'CYFRA_21_1': {
        'patterns': [r'(?:CYFRA[\s\-]*21-1|Cytokeratin[\s\-]*19\s*Fragment)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'SCC': {
        'patterns': [r'(?:SCC|Squamous\s*Cell\s*Carcinoma\s*Antigen)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'HE4': {
        'patterns': [r'(?:HE4|Human\s*Epididymis\s*Protein\s*4)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pmol/L', 'alt_units': ['ng/mL']
    },
    'ROMA_Index': {
        'patterns': [r'(?:ROMA|ROMA\s*Index|Risk\s*of\s*Ovarian\s*Malignancy\s*Algorithm)\s*[:\-]?\s*([\d.]+)'],
        'unit': '%', 'alt_units': ['%']
    },
    'Calcitonin': {
        'patterns': [r'(?:Calcitonin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pg/mL', 'alt_units': ['ng/L']
    },
    'Chromogranin_A': {
        'patterns': [r'(?:Chromogranin[\s\-]*A|CgA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'ProGRP': {
        'patterns': [r'(?:ProGRP|Pro[\s\-]*Gastrin[\s\-]*releasing\s*Peptide)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'pg/mL', 'alt_units': ['ng/L']
    },
    'Thyroglobulin_Oncology': {
        'patterns': [r'(?:Thyroglobulin|Tg)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'ng/mL', 'alt_units': ['µg/L']
    },
    'B2_Microglobulin': {
        'patterns': [r'(?:Beta[\s\-]*2[\s\-]*Microglobulin|β2[\s\-]*Microglobulin|B2M)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/L', 'alt_units': ['µg/mL']
    },
    'Ki_67': {
        'patterns': [r'(?:Ki[\s\-]*67|Ki67|MKI67)\s*[:\-]?\s*([\d.]+)'],
        'unit': '%', 'alt_units': ['%']
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
