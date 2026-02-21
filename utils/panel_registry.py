"""
Panel Registry - Central registration of all test panels and their parameter keys.
Used for OCR routing and cross-panel analysis.
"""

PANEL_REGISTRY = {
    'CBC': [
        'RBC', 'Hemoglobin', 'Hematocrit', 'MCV', 'MCH', 'MCHC', 'RDW', 'RDW_SD',
        'Reticulocytes', 'WBC', 'Neutrophils', 'Lymphocytes', 'Monocytes',
        'Eosinophils', 'Basophils', 'Platelets', 'MPV', 'PDW', 'ESR', 'ANC', 'ALC'
    ],
    'LFT': [
        'ALT', 'AST', 'ALP', 'GGT', 'Total_Bilirubin', 'Direct_Bilirubin',
        'Indirect_Bilirubin', 'Total_Protein', 'Albumin', 'Globulin',
        'AG_Ratio', 'LDH', 'PT', 'INR'
    ],
    'KFT': [
        'Creatinine', 'BUN', 'Urea', 'Uric_Acid', 'eGFR', 'Cystatin_C',
        'Sodium', 'Potassium', 'Chloride', 'Bicarbonate', 'Calcium',
        'Phosphorus', 'Magnesium'
    ],
    'Lipid': [
        'Total_Cholesterol', 'HDL', 'LDL', 'VLDL', 'Triglycerides',
        'Non_HDL', 'TC_HDL_Ratio', 'LDL_HDL_Ratio', 'ApoA1', 'ApoB', 'Lp_a'
    ],
    'Sugar': [
        'Fasting_Glucose', 'Random_Glucose', 'PP_Glucose', 'HbA1c',
        'eAG', 'Insulin', 'C_Peptide', 'HOMA_IR'
    ],
    'Urine': [
        'Urine_Color', 'Urine_Appearance', 'Urine_pH', 'Specific_Gravity',
        'Urine_Protein', 'Urine_Glucose', 'Urine_Ketones', 'Urine_Bilirubin',
        'Urine_Urobilinogen', 'Urine_Blood', 'Urine_Nitrite',
        'Urine_Leukocyte_Esterase', 'Urine_RBC', 'Urine_WBC',
        'Urine_Epithelial', 'Urine_Casts', 'Urine_Crystals',
        'Urine_Bacteria', 'Urine_Yeast', 'Protein_Creatinine_Ratio',
        'Albumin_Creatinine_Ratio', 'Microalbumin'
    ],
    'TFT': [
        'TSH', 'T3', 'T4', 'FT3', 'FT4', 'Reverse_T3', 'T3_Uptake',
        'Anti_TPO', 'Anti_Thyroglobulin', 'TSH_Receptor_Ab', 'Thyroglobulin'
    ],
    'Rheumatology': [
        'RF', 'Anti_CCP', 'ANA', 'ANA_Pattern', 'Anti_dsDNA', 'Anti_Smith',
        'Complement_C3', 'Complement_C4', 'Anti_Phospholipid_IgG',
        'Anti_Phospholipid_IgM', 'Anti_Cardiolipin_IgG', 'Anti_Cardiolipin_IgM',
        'Lupus_Anticoagulant', 'Beta2_Glycoprotein', 'CRP', 'hs_CRP', 'ASO', 'HLA_B27'
    ],
    'Oncology': [
        'AFP', 'CEA', 'Onco_LDH', 'Beta2_Microglobulin', 'CA_19_9', 'CA_72_4',
        'CA_15_3', 'CA_27_29', 'CA_125', 'HE4', 'ROMA_Index',
        'Total_PSA', 'Free_PSA', 'PSA_Ratio', 'Beta_hCG', 'NSE',
        'CYFRA_21_1', 'SCC', 'ProGRP', 'Calcitonin', 'Onco_Thyroglobulin',
        'Chromogranin_A', 'Ki_67'
    ]
}


def get_all_panels():
    return list(PANEL_REGISTRY.keys())


def get_panel_parameters(panel: str):
    return PANEL_REGISTRY.get(panel, [])


def find_panel_for_parameter(param_key: str) -> str:
    for panel, keys in PANEL_REGISTRY.items():
        if param_key in keys:
            return panel
    return 'CBC'
