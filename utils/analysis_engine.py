"""
analysis_engine.py — Comprehensive Clinical Analysis Engine
============================================================
Provides multi-panel clinical analysis with:

  • Reference range validation & clinical classification
  • Differential diagnosis suggestions
  • Sample quality assessment (Rule of Threes, consistency checks)
  • Calculated indices (Mentzer, NLR, ratios, etc.)
  • Panel-specific insights (CBC, LFT, KFT, LIPID, etc.)
  • Critical value alerts
  • Clinical recommendations
  • Severity assessment & flagging system

Public API
----------
  analyze_all_parameters(params, patient_info)      → comprehensive analysis
  get_reference_range(param, sex)                   → ref_low, ref_high, unit
  classify_value(param, value, sex)                 → {status, message, color, ...}
  check_sample_quality(params)                      → [quality_issues]
  calculate_indices(params)                         → {calculated_field: result}
  get_differential_diagnosis(param, status)         → [differential_conditions]
  get_clinical_recommendations(analysis)            → [recommendations]
  generate_summary_report(analysis, patient_info)   → formatted_text
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json

# ============================================================================
# COMPREHENSIVE REFERENCE RANGES BY PARAMETER & SEX
# ============================================================================

REFERENCE_RANGES = {
# Add these constants to utils/analysis_engine.py

PANEL_LABELS = {
    "CBC": "Complete Blood Count",
    "LFT": "Liver Function Tests",
    "KFT": "Kidney Function Tests",
    "LIPID": "Lipid Profile",
    "DIABETES": "Diabetes Markers",
    "TFT": "Thyroid Function Tests",
    "VIT_D": "Vitamin D",
    "VIT_B12": "Vitamin B12 / Folate",
    "URINE_RM": "Urine Routine & Microscopy",
    "RHEUMA": "Rheumatology Markers",
    "ONCOLOGY": "Oncology / Tumour Markers",
}

PANEL_ICONS = {
    "CBC": "🩸",
    "LFT": "🏥",
    "KFT": "🫘",
    "LIPID": "🧬",
    "DIABETES": "🩺",
    "TFT": "🦋",
    "VIT_D": "☀️",
    "VIT_B12": "💊",
    "URINE_RM": "🧪",
    "RHEUMA": "🦴",
    "ONCOLOGY": "🔬",
}

# Map each panel to its parameters
PANEL_PARAMETER_MAP = {
    "CBC": ["RBC", "Hemoglobin", "Hematocrit", "MCV", "MCH", "MCHC", "RDW", "RDW_SD", "WBC", "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils", "Platelets", "MPV", "PDW", "PCT"],
    "LFT": ["ALT", "AST", "ALP", "GGT", "Bilirubin_Total", "Bilirubin_Direct", "Bilirubin_Indirect", "Albumin", "Total_Protein", "Globulin", "Albumin_Globulin_Ratio", "PT", "INR"],
    "KFT": ["Creatinine", "BUN", "Urea", "Uric_Acid", "eGFR", "Cystatin_C", "Sodium", "Potassium", "Chloride", "Bicarbonate", "Calcium", "Phosphate", "Magnesium"],
    "LIPID": ["Total_Cholesterol", "HDL", "LDL", "VLDL", "Triglycerides", "Non_HDL", "TC_HDL_Ratio", "LDL_HDL_Ratio", "ApoA1", "ApoB", "Lp_a"],
    "DIABETES": ["Fasting_Glucose", "Random_Glucose", "PP_Glucose", "HbA1c", "eAG", "Insulin", "C_Peptide", "HOMA_IR"],
    "TFT": ["TSH", "T3", "T4", "FT3", "FT4", "Reverse_T3", "T3_Uptake", "Anti_TPO", "Anti_Thyroglobulin", "TSH_Receptor_Ab", "Thyroglobulin"],
    "VIT_D": ["Vitamin_D_25OH"],
    "VIT_B12": ["Vitamin_B12", "Folate"],
    "URINE_RM": ["Color", "Appearance", "pH", "Specific_Gravity", "Protein", "Glucose", "Ketones", "Nitrites", "Leukocyte_Esterase", "RBC", "WBC", "Bacteria", "Crystals", "Casts", "Epithelial_Cells"],
    "RHEUMA": ["RA_Factor", "Anti_CCP", "ANA", "Anti_dsDNA", "Anti_Smith", "Anti_Sm", "Complement_C3", "Complement_C4", "ESR", "CRP"],
    "ONCOLOGY": ["AFP", "CEA", "CA_19_9", "CA_125", "PSA", "Beta_hCG"],
}
  # ────────────────────────────────────────────────────────────────────
    # CBC Parameters
    # ────────────────────────────────────────────────────────────────────
    "RBC": {
        "Male":    {"low": 4.5, "high": 5.9, "unit": "×10¹²/L", "critical_low": 2.0, "critical_high": 8.0},
        "Female":  {"low": 4.1, "high": 5.1, "unit": "×10¹²/L", "critical_low": 2.0, "critical_high": 8.0},
        "Default": {"low": 4.1, "high": 5.9, "unit": "×10¹²/L", "critical_low": 2.0, "critical_high": 8.0},
    },
    "Hemoglobin": {
        "Male":    {"low": 13.5, "high": 17.5, "unit": "g/dL", "critical_low": 5.0, "critical_high": 20.0},
        "Female":  {"low": 12.0, "high": 15.5, "unit": "g/dL", "critical_low": 5.0, "critical_high": 20.0},
        "Default": {"low": 12.0, "high": 17.5, "unit": "g/dL", "critical_low": 5.0, "critical_high": 20.0},
    },
    "Hematocrit": {
        "Male":    {"low": 38.8, "high": 50.0, "unit": "%", "critical_low": 15.0, "critical_high": 60.0},
        "Female":  {"low": 34.9, "high": 44.5, "unit": "%", "critical_low": 15.0, "critical_high": 60.0},
        "Default": {"low": 34.9, "high": 50.0, "unit": "%", "critical_low": 15.0, "critical_high": 60.0},
    },
    "MCV": {
        "Default": {"low": 80, "high": 100, "unit": "fL", "critical_low": 40, "critical_high": 150},
    },
    "MCH": {
        "Default": {"low": 27, "high": 33, "unit": "pg", "critical_low": 10, "critical_high": 50},
    },
    "MCHC": {
        "Default": {"low": 32, "high": 36, "unit": "g/dL", "critical_low": 20, "critical_high": 50},
    },
    "RDW_CV": {
        "Default": {"low": 11.5, "high": 14.5, "unit": "%", "critical_low": 5, "critical_high": 30},
    },
    "WBC": {
        "Default": {"low": 4.5, "high": 11.0, "unit": "×10⁹/L", "critical_low": 0.5, "critical_high": 100},
    },
    "Neutrophils": {
        "Default": {"low": 45, "high": 74, "unit": "%", "critical_low": 0, "critical_high": 100},
    },
    "Lymphocytes": {
        "Default": {"low": 17, "high": 48, "unit": "%", "critical_low": 0, "critical_high": 100},
    },
    "Monocytes": {
        "Default": {"low": 2, "high": 11, "unit": "%", "critical_low": 0, "critical_high": 100},
    },
    "Eosinophils": {
        "Default": {"low": 0, "high": 4, "unit": "%", "critical_low": 0, "critical_high": 100},
    },
    "Basophils": {
        "Default": {"low": 0, "high": 2, "unit": "%", "critical_low": 0, "critical_high": 100},
    },
    "ANC": {
        "Default": {"low": 2.0, "high": 7.5, "unit": "×10⁹/L", "critical_low": 0.5, "critical_high": 100},
    },
    "ALC": {
        "Default": {"low": 1.0, "high": 4.8, "unit": "×10⁹/L", "critical_low": 0.2, "critical_high": 50},
    },
    "Platelets": {
        "Default": {"low": 150, "high": 400, "unit": "×10⁹/L", "critical_low": 20, "critical_high": 1000},
    },
    "MPV": {
        "Default": {"low": 7.4, "high": 10.4, "unit": "fL", "critical_low": 3, "critical_high": 20},
    },
    "ESR": {
        "Male":    {"low": 0, "high": 15, "unit": "mm/hr", "critical_low": 0, "critical_high": 100},
        "Female":  {"low": 0, "high": 20, "unit": "mm/hr", "critical_low": 0, "critical_high": 100},
        "Default": {"low": 0, "high": 20, "unit": "mm/hr", "critical_low": 0, "critical_high": 100},
    },

    # ────────────────────────────────────────────────────────────────────
    # LFT Parameters
    # ────────────────────────────────────────────────────────────────────
    "ALT": {
        "Male":    {"low": 7, "high": 56, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
        "Female":  {"low": 7, "high": 45, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
        "Default": {"low": 7, "high": 56, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
    },
    "AST": {
        "Male":    {"low": 10, "high": 40, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
        "Female":  {"low": 7, "high": 35, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
        "Default": {"low": 7, "high": 40, "unit": "IU/L", "critical_low": 0, "critical_high": 10000},
    },
    "ALP": {
        "Default": {"low": 30, "high": 120, "unit": "IU/L", "critical_low": 0, "critical_high": 1000},
    },
    "GGT": {
        "Male":    {"low": 0, "high": 65, "unit": "IU/L", "critical_low": 0, "critical_high": 1000},
        "Female":  {"low": 0, "high": 36, "unit": "IU/L", "critical_low": 0, "critical_high": 1000},
        "Default": {"low": 0, "high": 65, "unit": "IU/L", "critical_low": 0, "critical_high": 1000},
    },
    "Total_Bilirubin": {
        "Default": {"low": 0.2, "high": 1.3, "unit": "mg/dL", "critical_low": 0, "critical_high": 50},
    },
    "Direct_Bilirubin": {
        "Default": {"low": 0.0, "high": 0.3, "unit": "mg/dL", "critical_low": 0, "critical_high": 30},
    },
    "Total_Protein": {
        "Default": {"low": 6.0, "high": 8.3, "unit": "g/dL", "critical_low": 2.0, "critical_high": 15.0},
    },
    "Albumin": {
        "Default": {"low": 3.5, "high": 5.0, "unit": "g/dL", "critical_low": 1.0, "critical_high": 10.0},
    },

    # ────────────────────────────────────────────────────────────────────
    # KFT Parameters
    # ────────────────────────────────────────────────────────────────────
    "Serum_Creatinine": {
        "Male":    {"low": 0.7, "high": 1.3, "unit": "mg/dL", "critical_low": 0.1, "critical_high": 30.0},
        "Female":  {"low": 0.6, "high": 1.1, "unit": "mg/dL", "critical_low": 0.1, "critical_high": 30.0},
        "Default": {"low": 0.6, "high": 1.3, "unit": "mg/dL", "critical_low": 0.1, "critical_high": 30.0},
    },
    "BUN": {
        "Default": {"low": 7, "high": 20, "unit": "mg/dL", "critical_low": 0, "critical_high": 200},
    },
    "Serum_Urea": {
        "Default": {"low": 15, "high": 45, "unit": "mg/dL", "critical_low": 0, "critical_high": 500},
    },
    "Serum_Sodium": {
        "Default": {"low": 136, "high": 145, "unit": "mEq/L", "critical_low": 110, "critical_high": 170},
    },
    "Serum_Potassium": {
        "Default": {"low": 3.5, "high": 5.0, "unit": "mEq/L", "critical_low": 2.5, "critical_high": 7.0},
    },
    "Serum_Chloride": {
        "Default": {"low": 98, "high": 107, "unit": "mEq/L", "critical_low": 80, "critical_high": 120},
    },
    "Serum_Calcium": {
        "Default": {"low": 8.5, "high": 10.2, "unit": "mg/dL", "critical_low": 6.0, "critical_high": 14.0},
    },
    "Serum_Phosphorus": {
        "Default": {"low": 2.5, "high": 4.5, "unit": "mg/dL", "critical_low": 1.0, "critical_high": 15.0},
    },
    "eGFR": {
        "Default": {"low": 60, "high": 999, "unit": "mL/min/1.73m²", "critical_low": 0, "critical_high": 200},
    },

    # ────────────────────────────────────────────────────────────────────
    # Lipid Profile
    # ────────────────────────────────────────────────────────────────────
    "Total_Cholesterol": {
        "Default": {"low": 0, "high": 200, "unit": "mg/dL", "optimal": 200, "borderline": 240, "critical_high": 500},
    },
    "HDL_Cholesterol": {
        "Default": {"low": 40, "high": 999, "unit": "mg/dL", "optimal": 60, "critical_low": 20},
    },
    "LDL_Cholesterol": {
        "Default": {"low": 0, "high": 100, "unit": "mg/dL", "optimal": 100, "critical_high": 500},
    },
    "Triglycerides": {
        "Default": {"low": 0, "high": 150, "unit": "mg/dL", "critical_high": 1000},
    },

    # ────────────────────────────────────────────────────────────────────
    # Diabetes Parameters
    # ────────────────────────────────────────────────────────────────────
    "Fasting_Blood_Glucose": {
        "Default": {"low": 70, "high": 100, "unit": "mg/dL", "critical_low": 40, "critical_high": 600},
    },
    "HbA1c": {
        "Default": {"low": 0, "high": 5.7, "unit": "%", "critical_high": 15},
    },
    "Random_Blood_Glucose": {
        "Default": {"low": 70, "high": 140, "unit": "mg/dL", "critical_low": 40, "critical_high": 600},
    },

    # ────────────────────────────────────────────────────────────────────
    # Thyroid Function
    # ────────────────────────────────────────────────────────────────────
    "TSH": {
        "Default": {"low": 0.4, "high": 4.0, "unit": "µIU/mL", "critical_low": 0, "critical_high": 100},
    },
    "Free_T4": {
        "Default": {"low": 0.8, "high": 1.8, "unit": "ng/dL", "critical_low": 0, "critical_high": 5},
    },
    "Total_T3": {
        "Default": {"low": 80, "high": 200, "unit": "ng/dL", "critical_low": 20, "critical_high": 500},
    },

    # ────────────────────────────────────────────────────────────────────
    # Vitamin & Mineral Parameters
    # ────────────────────────────────────────────────────────────────────
    "Vitamin_D_25OH": {
        "Default": {"low": 30, "high": 100, "unit": "ng/mL", "deficient": 20, "insufficient": 29},
    },
    "Vitamin_B12": {
        "Default": {"low": 200, "high": 900, "unit": "pg/mL", "critical_low": 100},
    },
    "Serum_Folate": {
        "Default": {"low": 5.4, "high": 16, "unit": "ng/mL", "critical_low": 2},
    },

    # ────────────────────────────────────────────────────────────────────
    # Rheumatology & Inflammation
    # ────────────────────────────────────────────────────────────────────
    "CRP": {
        "Default": {"low": 0, "high": 3.0, "unit": "mg/L", "critical_high": 100},
    },
    "hs_CRP": {
        "Default": {"low": 0, "high": 1.0, "unit": "mg/L", "critical_high": 50},
    },
    "RA_Factor": {
        "Default": {"low": 0, "high": 14, "unit": "IU/mL", "critical_high": 500},
    },

    # ───────────────────────────────────────────────────────��────────────
    # Oncology Markers
    # ────────────────────────────────────────────────────────────────────
    "PSA_Total": {
        "Default": {"low": 0, "high": 4.0, "unit": "ng/mL", "borderline": 4.0, "critical_high": 100},
    },
    "CEA": {
        "Default": {"low": 0, "high": 2.5, "unit": "ng/mL", "critical_high": 50},
    },
    "CA_125": {
        "Default": {"low": 0, "high": 35, "unit": "U/mL", "critical_high": 1000},
    },
    "AFP": {
        "Default": {"low": 0, "high": 10, "unit": "ng/mL", "critical_high": 10000},
    },
}


# ============================================================================
# DIFFERENTIAL DIAGNOSES BY PARAMETER
# ============================================================================

DIFFERENTIAL_DIAGNOSES = {
    "Hemoglobin": {
        "low": {
            "title": "Anemia (Low Hemoglobin)",
            "conditions": [
                {"name": "Iron Deficiency Anemia", "prevalence": "Most common", "note": "Check ferritin, iron saturation, TIBC. Low MCV, low MCH typical."},
                {"name": "Vitamin B12 Deficiency", "prevalence": "Common in vegans/elderly", "note": "Check B12, folate, homocysteine. Macrocytic anemia."},
                {"name": "Folate Deficiency", "prevalence": "Common in alcoholics", "note": "Check serum/RBC folate. Macrocytic anemia."},
                {"name": "Chronic Kidney Disease", "prevalence": "Common in advanced CKD", "note": "Erythropoietin deficiency. Check creatinine, eGFR."},
                {"name": "Hemolytic Anemia", "prevalence": "Various causes", "note": "Check bilirubin, LDH, reticulocyte count, direct Coombs."},
                {"name": "Bone Marrow Disorders", "prevalence": "Serious", "note": "Leukemia, aplastic anemia, myelodysplasia. Check WBC, platelets."},
                {"name": "Acute Hemorrhage", "prevalence": "Clinical context", "note": "Recent bleeding event. Watch for clinical signs."},
            ],
        },
        "high": {
            "title": "Elevated Hemoglobin (Polycythemia)",
            "conditions": [
                {"name": "Polycythemia Vera", "prevalence": "Hematologic malignancy", "note": "JAK2 V617F mutation. Check WBC, platelets for myeloproliferation."},
                {"name": "Chronic Hypoxia", "prevalence": "Chronic lung/heart disease", "note": "Physiologic compensation for low O2. Check clinical history."},
                {"name": "Erythropoietin-Secreting Tumors", "prevalence": "Renal cancer, hemangioma", "note": "Paraneoplastic syndrome. Check kidney imaging."},
                {"name": "Dehydration", "prevalence": "Hemoconcentration", "note": "Apparent increase in Hb. Check BUN/Cr ratio, clinical state."},
                {"name": "High Altitude", "prevalence": "Normal adaptive response", "note": "Chronic hypoxia stimulates EPO. Expected at elevation."},
            ],
        },
    },
    "WBC": {
        "low": {
            "title": "Leukopenia (Low WBC)",
            "conditions": [
                {"name": "Bone Marrow Suppression", "prevalence": "Common", "note": "Medications, chemotherapy, radiation. Check medications list."},
                {"name": "Infection/Sepsis", "prevalence": "Critical", "note": "Overwhelming bacterial infection depletes WBC. Clinical signs of infection?"},
                {"name": "Aplastic Anemia", "prevalence": "Serious", "note": "Pancytopenia (low RBC, WBC, platelets). Bone marrow biopsy definitive."},
                {"name": "SLE or Other Autoimmune", "prevalence": "Immune-mediated", "note": "Check ANA, anti-dsDNA, complement levels."},
                {"name": "HIV/AIDS", "prevalence": "Immunosuppression", "note": "CD4 count typically low. Check HIV status."},
                {"name": "Medication-Induced", "prevalence": "Common", "note": "NSAIDs, antibiotics, immunosuppressants, chemotherapy."},
            ],
        },
        "high": {
            "title": "Leukocytosis (High WBC)",
            "conditions": [
                {"name": "Infection/Pneumonia", "prevalence": "Most common", "note": "Bacterial, viral, or fungal. Check neutrophil %, clinical signs."},
                {"name": "Leukemia", "prevalence": "Hematologic malignancy", "note": "Acute or chronic. High WBC + blasts. Check smear, LDH."},
                {"name": "Leukemoid Reaction", "prevalence": "Reactive", "note": "Extreme elevation (>50K) in response to severe infection/inflammation."},
                {"name": "Chronic Myeloproliferative", "prevalence": "Hematologic", "note": "CML, polycythemia vera, myelofibrosis. JAK2 mutation studies."},
                {"name": "Medications", "prevalence": "Steroids, catecholamines", "note": "Epinephrine, corticosteroids cause release from marginal pool."},
                {"name": "Smoking", "prevalence": "Common habit effect", "note": "Chronic smokers have persistently elevated WBC. Reversible with cessation."},
                {"name": "Malignancy", "prevalence": "Paraneoplastic", "note": "Lung, kidney cancers can elevate WBC. Check imaging."},
            ],
        },
    },
    "Platelets": {
        "low": {
            "title": "Thrombocytopenia (Low Platelets)",
            "conditions": [
                {"name": "Immune Thrombocytopenia (ITP)", "prevalence": "Most common acquired", "note": "Autoimmune destruction. Often 10-50K range. Check for splenomegaly."},
                {"name": "Drug-Induced", "prevalence": "Common", "note": "NSAIDs, sulfonamides, statins, anticonvulsants. Discontinue if possible."},
                {"name": "Bone Marrow Disorders", "prevalence": "Serious", "note": "Aplastic anemia, MDS, leukemia. Pancytopenia pattern."},
                {"name": "TTP/HUS", "prevalence": "Thrombotic microangiopathy", "note": "Microangiopathic hemolytic anemia. High LDH, high creatinine."},
                {"name": "DIC", "prevalence": "Disseminated Intravascular Coagulation", "note": "Critical. Prolonged PT/INR, low fibrinogen. Severe illness context."},
                {"name": "Splenomegaly", "prevalence": "Sequestration", "note": "Portal hypertension, lymphoma. Physical exam critical."},
                {"name": "Sepsis", "prevalence": "Critical illness", "note": "Severe infection causes consumptive thrombocytopenia."},
            ],
        },
        "high": {
            "title": "Thrombocytosis (High Platelets)",
            "conditions": [
                {"name": "Essential Thrombocythemia", "prevalence": "Primary hematologic", "note": "Myeloproliferative. JAK2 V617F, CALR, MPL mutations. Elevated risk of thrombosis."},
                {"name": "Polycythemia Vera", "prevalence": "Myeloproliferative", "note": "Often elevated Hb, WBC, platelets together. JAK2+."},
                {"name": "Chronic Myeloid Leukemia", "prevalence": "Philadelphia chromosome+", "note": "BCR-ABL fusion. Extreme elevation possible."},
                {"name": "Infection/Inflammation", "prevalence": "Reactive", "note": "Acute phase response. Reversible with treatment of underlying cause."},
                {"name": "Iron Deficiency", "prevalence": "Reactive", "note": "Mild elevation common. Corrects with iron replacement."},
                {"name": "Malignancy", "prevalence": "Paraneoplastic", "note": "Lung, gastric, ovarian cancers. Resolves with cancer treatment."},
                {"name": "Post-Splenectomy", "prevalence": "Permanent elevation", "note": "Normal consequence of absent spleen. Watch for thrombosis risk."},
            ],
        },
    },
    "Total_Cholesterol": {
        "high": {
            "title": "Hypercholesterolemia",
            "conditions": [
                {"name": "Primary Hyperlipidemia", "prevalence": "Genetic", "note": "Familial hypercholesterolemia. Check family history, LDL pattern."},
                {"name": "Secondary to Metabolic Syndrome", "prevalence": "Common", "note": "Obesity, diabetes, sedentary. Elevates TC, TG, LDL; lowers HDL."},
                {"name": "Hypothyroidism", "prevalence": "Treatable", "note": "Check TSH, free T4. Cholesterol improves with thyroid replacement."},
                {"name": "Liver Disease", "prevalence": "Can be increased", "note": "Cirrhosis paradoxically lowers. Cholestasis may elevate."},
                {"name": "Chronic Kidney Disease", "prevalence": "Progressive", "note": "Nephrotic syndrome has severe dyslipidemia. Check albumin, proteinuria."},
            ],
        },
    },
    "Serum_Creatinine": {
        "high": {
            "title": "Elevated Creatinine (Renal Dysfunction)",
            "conditions": [
                {"name": "Chronic Kidney Disease", "prevalence": "Progressive", "note": "Stages 1-5. Check eGFR, urinalysis, kidney imaging if new."},
                {"name": "Acute Kidney Injury", "prevalence": "Acute", "note": "Sudden rise. Distinguish pre-renal, intrinsic, post-renal causes."},
                {"name": "Dehydration", "prevalence": "Pre-renal", "note": "BUN/Cr >20 suggests pre-renal. Improves with hydration."},
                {"name": "Hypertension", "prevalence": "Common cause of CKD", "note": "Chronic poorly controlled HTN damages kidneys. Check BP control."},
                {"name": "Diabetes", "prevalence": "Most common cause globally", "note": "Diabetic nephropathy. Check glucose, HbA1c, proteinuria."},
                {"name": "Glomerulonephritis", "prevalence": "Immune-mediated", "note": "Check urinalysis (RBC, casts), kidney biopsy if needed."},
                {"name": "Muscle Disease", "prevalence": "High muscle mass", "note": "Athletes have higher baseline. Use eGFR/CKD-EPI for more accurate GFR."},
            ],
        },
    },
    "TSH": {
        "high": {
            "title": "Elevated TSH (Primary Hypothyroidism)",
            "conditions": [
                {"name": "Hashimoto's Thyroiditis", "prevalence": "Most common cause", "note": "Autoimmune. Check anti-TPO, anti-thyroglobulin. Fatigue, weight gain."},
                {"name": "Iodine Deficiency", "prevalence": "Worldwide leading cause", "note": "Geographic areas with low iodine. Improvement with supplementation."},
                {"name": "Hypothyroidism on Inadequate Levothyroxine", "prevalence": "Common compliance issue", "note": "Check dose, adherence. Repeat TSH 6-8 weeks after adjustment."},
                {"name": "Central Hypothyroidism", "prevalence": "Secondary/tertiary", "note": "Low TSH + low free T4. Pituitary/hypothalamic disease. Check MRI if suspected."},
            ],
        },
        "low": {
            "title": "Suppressed TSH (Hyperthyroidism or Over-replacement)",
            "conditions": [
                {"name": "Graves' Disease", "prevalence": "Most common hyperthyroidism", "note": "Autoimmune. Check TSI antibodies. Heat intolerance, anxiety, tachycardia."},
                {"name": "Thyroiditis", "prevalence": "Postpartum, viral, medication-induced", "note": "Painful or painless. Transient hyperthyroid phase."},
                {"name": "Toxic Nodule/Multinodular Goiter", "prevalence": "Iodine-replete areas", "note": "Thyroid scan/ultrasound shows autonomously functioning nodule(s)."},
                {"name": "Over-replacement with Levothyroxine", "prevalence": "Iatrogenic", "note": "Patient on thyroid hormone for hypothyroidism or TSH suppression. Adjust dose."},
                {"name": "TSH-Secreting Pituitary Tumor", "prevalence": "Rare", "note": "High TSH with high free T4 (unusual pattern). MRI pituitary."},
            ],
        },
    },
}


# ============================================================================
# CLASSIFICATION LOGIC
# ============================================================================

def get_reference_range(param: str, sex: str = "Default") -> Optional[Dict]:
    """
    Get reference range for a parameter.
    
    Returns
    -------
    {"low": float, "high": float, "unit": str, ...}
    """
    if param not in REFERENCE_RANGES:
        return None
    
    ref_data = REFERENCE_RANGES[param]
    if sex in ref_data:
        return ref_data[sex].copy()
    elif "Default" in ref_data:
        return ref_data["Default"].copy()
    return None


def classify_value(param: str, value: float, sex: str = "Default") -> Dict[str, Any]:
    """
    Classify a value as normal, low, high, or critical.
    
    Returns
    -------
    {
        "status": "normal|low|high|critical_low|critical_high|unknown",
        "message": "Human-readable classification",
        "color": "green|yellow|orange|red|gray",
        "low": float,
        "high": float,
        "unit": str,
    }
    """
    ref = get_reference_range(param, sex)
    if ref is None:
        return {
            "status": "unknown",
            "message": f"No reference range for {param}",
            "color": "gray",
            "low": None,
            "high": None,
            "unit": "unknown",
        }
    
    low = ref.get("low")
    high = ref.get("high")
    critical_low = ref.get("critical_low", low)
    critical_high = ref.get("critical_high", high)
    unit = ref.get("unit", "")
    
    # Determine status
    if critical_low is not None and value < critical_low:
        status = "critical_low"
        message = f"CRITICAL LOW: {value} {unit} (ref: {low}-{high})"
        color = "red"
    elif critical_high is not None and value > critical_high:
        status = "critical_high"
        message = f"CRITICAL HIGH: {value} {unit} (ref: {low}-{high})"
        color = "red"
    elif low is not None and value < low:
        status = "low"
        message = f"Low: {value} {unit} (ref: {low}-{high})"
        color = "orange"
    elif high is not None and value > high:
        status = "high"
        message = f"High: {value} {unit} (ref: {low}-{high})"
        color = "orange"
    else:
        status = "normal"
        message = f"Normal: {value} {unit} (ref: {low}-{high})"
        color = "green"
    
    return {
        "status": status,
        "message": message,
        "color": color,
        "low": low,
        "high": high,
        "unit": unit,
    }


def get_differential_diagnosis(param: str, status: str) -> Optional[List[Dict]]:
    """
    Get differential diagnosis for an abnormal parameter.
    
    Args
    ----
    param : str
        Parameter name (e.g., "Hemoglobin")
    status : str
        "low" or "high"
    
    Returns
    -------
    [{"name": str, "prevalence": str, "note": str}, ...]
    """
    if param not in DIFFERENTIAL_DIAGNOSES:
        return None
    
    dx = DIFFERENTIAL_DIAGNOSES[param]
    if status in dx:
        return dx[status].get("conditions", [])
    
    return None


# ============================================================================
# QUALITY CHECKS
# ============================================================================

def check_sample_quality(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess sample quality using consistency rules.
    
    Returns
    -------
    {
        "issues": [
            {"rule": str, "severity": "warning|error", "details": str},
            ...
        ],
        "quality_score": 0-100,
        "summary": str,
    }
    """
    issues = []
    score = 100
    
    # Extract CBC values
    rbc = parameters.get("RBC", {}).get("value")
    hb = parameters.get("Hemoglobin", {}).get("value")
    hct = parameters.get("Hematocrit", {}).get("value")
    mcv = parameters.get("MCV", {}).get("value")
    wbc = parameters.get("WBC", {}).get("value")
    platelets = parameters.get("Platelets", {}).get("value")
    
    # ────────────────────────────────────────────────────────────────
    # Rule of Threes: RBC × 3 = Hb
    # ────────────────────────────────────────────────────────────────
    if rbc and hb:
        expected_hb = rbc * 3
        diff = abs(hb - expected_hb)
        if diff > 1.5:
            severity = "warning" if diff < 3 else "error"
            issues.append({
                "rule": "Rule of Threes (RBC × 3 = Hb)",
                "severity": severity,
                "details": f"Expected Hb ≈ {expected_hb:.1f} g/dL, got {hb:.1f} g/dL (diff: {diff:.1f})",
                "possible_causes": "Sample clotting, hemolysis, abnormal hemoglobin, thalassemia, iron deficiency",
            })
            score -= 10 if severity == "warning" else 20
    
    # ────────────────────────────────────────────────────────────────
    # Rule of Threes: Hb × 3 = Hct
    # ────────────────────────────────────────────────────────────────
    if hb and hct:
        expected_hct = hb * 3
        diff = abs(hct - expected_hct)
        if diff > 3.0:
            severity = "warning" if diff < 6 else "error"
            issues.append({
                "rule": "Rule of Threes (Hb × 3 = Hct)",
                "severity": severity,
                "details": f"Expected Hct ≈ {expected_hct:.1f}%, got {hct:.1f}% (diff: {diff:.1f}%)",
                "possible_causes": "Sample issues, abnormal hemoglobin, thalassemia",
            })
            score -= 10 if severity == "warning" else 20
    
    # ────────────────────────────────────────────────────────────────
    # Mentzer Index: MCV/RBC < 13 suggests thalassemia; > 13 suggests iron deficiency
    # ────────────────────────────────────────────────────────────────
    if mcv and rbc and rbc > 0:
        mentzer = mcv / rbc
        if mentzer < 10:
            issues.append({
                "rule": "Mentzer Index",
                "severity": "warning",
                "details": f"Mentzer Index = {mentzer:.1f} (<10 suggests thalassemia trait)",
                "note": "Consider hemoglobin electrophoresis; may not need iron supplementation.",
            })
            score -= 5
    
    # ────────────────────────────────────────────────────────────────
    # Physiologic Impossibilities
    # ────────────────────────────────────────────────────────────────
    if hct and (hct < 10 or hct > 65):
        issues.append({
            "rule": "Hematocrit Out of Physiologic Range",
            "severity": "error",
            "details": f"Hct = {hct}% is physiologically implausible",
            "note": "Check for sample issues, data entry error, or genuine critical state.",
        })
        score -= 20
    
    if wbc and (wbc < 0.5 or wbc > 150):
        issues.append({
            "rule": "WBC Out of Physiologic Range",
            "severity": "error",
            "details": f"WBC = {wbc} ×10⁹/L is extremely rare",
            "note": "Verify sample quality and data entry.",
        })
        score -= 20
    
    if platelets and (platelets < 5 or platelets > 2000):
        issues.append({
            "rule": "Platelets Out of Physiologic Range",
            "severity": "error",
            "details": f"Platelets = {platelets} ×10⁹/L is extremely rare",
            "note": "Verify sample quality; clotting artifact likely.",
        })
        score -= 20
    
    score = max(0, min(100, score))
    
    summary = (
        "Excellent sample quality" if score >= 90
        else "Good sample quality with minor issues" if score >= 70
        else "Questionable sample quality; recommend repeat" if score >= 50
        else "Poor sample quality; REPEAT TEST RECOMMENDED"
    )
    
    return {
        "issues": issues,
        "quality_score": score,
        "summary": summary,
    }


# ============================================================================
# CALCULATED INDICES
# ============================================================================

def calculate_indices(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate derived indices from measured parameters.
    
    Returns
    -------
    {
        "Mentzer Index": {...},
        "NLR": {...},
        "BUN/Cr Ratio": {...},
        ...
    }
    """
    indices = {}
    
    # ────────────────────────────────────────────────────────────────
    # CBC Indices
    # ────────────────────────────────────────────────────────────────
    rbc = parameters.get("RBC", {}).get("value")
    mcv = parameters.get("MCV", {}).get("value")
    if rbc and mcv and rbc > 0:
        mentzer = mcv / rbc
        indices["Mentzer_Index"] = {
            "value": round(mentzer, 1),
            "formula": "MCV / RBC",
            "interpretation": "Thalassemia trait" if mentzer < 13 else "Iron deficiency or normal",
            "note": "<13 suggestive of thalassemia; >13 iron deficiency",
        }
    
    hb = parameters.get("Hemoglobin", {}).get("value")
    hct = parameters.get("Hematocrit", {}).get("value")
    if hb and hct and hct > 0:
        calc_mchc = (hb / hct) * 100
        indices["Calculated_MCHC"] = {
            "value": round(calc_mchc, 1),
            "formula": "(Hb / Hct) × 100",
            "interpretation": f"{calc_mchc:.1f} g/dL",
            "note": "Should match reported MCHC",
        }
    
    wbc = parameters.get("WBC", {}).get("value")
    neutrophils = parameters.get("Neutrophils", {}).get("value")
    lymphocytes = parameters.get("Lymphocytes", {}).get("value")
    
    if wbc and neutrophils:
        anc = wbc * (neutrophils / 100)
        indices["Calculated_ANC"] = {
            "value": round(anc, 2),
            "formula": "WBC × (Neutrophils% / 100)",
            "interpretation": f"{anc:.2f} ×10⁹/L",
            "note": "<1.5 neutropenia; <0.5 severe neutropenia",
        }
    
    if wbc and lymphocytes:
        alc = wbc * (lymphocytes / 100)
        indices["Calculated_ALC"] = {
            "value": round(alc, 2),
            "formula": "WBC × (Lymphocytes% / 100)",
            "interpretation": f"{alc:.2f} ×10⁹/L",
            "note": "Normal: 1.0-4.8 ×10⁹/L",
        }
    
    if wbc and neutrophils and lymphocytes:
        nlr = (wbc * neutrophils / 100) / (wbc * lymphocytes / 100) if (wbc * lymphocytes / 100) > 0 else None
        if nlr:
            indices["NLR"] = {
                "value": round(nlr, 2),
                "formula": "ANC / ALC",
                "interpretation": f"{nlr:.2f}",
                "note": "Elevated NLR associated with infection, inflammation, poor prognosis in cancer",
            }
    
    # ────────────────────────────────────────────────────────────────
    # LFT Indices
    # ────────────────────────────────────────────────────────────────
    total_bili = parameters.get("Total_Bilirubin", {}).get("value")
    direct_bili = parameters.get("Direct_Bilirubin", {}).get("value")
    if total_bili and direct_bili:
        indirect_bili = total_bili - direct_bili
        indices["Indirect_Bilirubin"] = {
            "value": round(indirect_bili, 2),
            "formula": "Total Bilirubin - Direct Bilirubin",
            "interpretation": f"{indirect_bili:.2f} mg/dL",
            "note": "Indirect hyperbilirubinemia suggests hemolysis or unconjugated hyperbilirubinemia",
        }
    
    total_protein = parameters.get("Total_Protein", {}).get("value")
    albumin = parameters.get("Albumin", {}).get("value")
    if total_protein and albumin:
        globulin = total_protein - albumin
        indices["Globulin"] = {
            "value": round(globulin, 2),
            "formula": "Total Protein - Albumin",
            "interpretation": f"{globulin:.2f} g/dL",
        }
        if globulin > 0:
            ag_ratio = albumin / globulin
            indices["AG_Ratio"] = {
                "value": round(ag_ratio, 2),
                "formula": "Albumin / Globulin",
                "interpretation": f"{ag_ratio:.2f}",
                "note": "Normally 1:1 to 2:1; inverted ratio suggests cirrhosis or chronic liver disease",
            }
    
    alt = parameters.get("ALT", {}).get("value")
    ast = parameters.get("AST", {}).get("value")
    if alt and ast:
        ast_alt_ratio = ast / alt if alt > 0 else None
        if ast_alt_ratio:
            indices["AST_ALT_Ratio"] = {
                "value": round(ast_alt_ratio, 2),
                "formula": "AST / ALT",
                "interpretation": f"{ast_alt_ratio:.2f}",
                "note": "<1 hepatitis; >2 alcoholic liver disease or cirrhosis",
            }
    
    # ────────────────────────────────────────────────────────────────
    # KFT Indices
    # ────────────────────────────────────────────────────────────────
    bun = parameters.get("BUN", {}).get("value")
    creatinine = parameters.get("Serum_Creatinine", {}).get("value")
    if bun and creatinine and creatinine > 0:
        bun_cr_ratio = bun / creatinine
        indices["BUN_Creatinine_Ratio"] = {
            "value": round(bun_cr_ratio, 1),
            "formula": "BUN / Creatinine",
            "interpretation": f"{bun_cr_ratio:.1f}",
            "note": ">20 pre-renal; 10-20 normal; <10 intrinsic/hepatic",
        }
    
    sodium = parameters.get("Serum_Sodium", {}).get("value")
    chloride = parameters.get("Serum_Chloride", {}).get("value")
    hco3 = parameters.get("Serum_Bicarbonate", {}).get("value")
    if sodium and chloride and hco3:
        anion_gap = sodium - (chloride + hco3)
        indices["Anion_Gap"] = {
            "value": round(anion_gap, 1),
            "formula": "Na - (Cl + HCO3)",
            "interpretation": f"{anion_gap:.1f} mEq/L",
            "note": ">12 metabolic acidosis with high anion gap; <8 low anion gap acidosis",
        }
    
    # ────────────────────────────────────────────────────────────────
    # Lipid Indices
    # ────────────────────────────────────────────────────────��───────
    tc = parameters.get("Total_Cholesterol", {}).get("value")
    hdl = parameters.get("HDL_Cholesterol", {}).get("value")
    triglycerides = parameters.get("Triglycerides", {}).get("value")
    
    if triglycerides:
        vldl = triglycerides / 5
        indices["Calculated_VLDL"] = {
            "value": round(vldl, 1),
            "formula": "Triglycerides / 5",
            "interpretation": f"{vldl:.1f} mg/dL",
            "note": "Estimated VLDL; direct VLDL measurement preferred if available",
        }
    
    if tc and hdl and triglycerides and hdl > 0:
        vldl = triglycerides / 5
        ldl = tc - hdl - vldl
        indices["Calculated_LDL"] = {
            "value": round(ldl, 1),
            "formula": "TC - HDL - (Triglycerides/5)",
            "interpretation": f"{ldl:.1f} mg/dL",
            "note": "Friedewald formula; less accurate if triglycerides >400 or LDL <25",
        }
    
    if tc and hdl:
        non_hdl = tc - hdl
        indices["Non_HDL_Cholesterol"] = {
            "value": round(non_hdl, 1),
            "formula": "TC - HDL",
            "interpretation": f"{non_hdl:.1f} mg/dL",
            "note": "Better predictor of CVD risk than LDL alone; includes all atherogenic particles",
        }
        
        if hdl > 0:
            tc_hdl_ratio = tc / hdl
            indices["TC_HDL_Ratio"] = {
                "value": round(tc_hdl_ratio, 2),
                "formula": "TC / HDL",
                "interpretation": f"{tc_hdl_ratio:.2f}",
                "note": "<5 good; >5 increased CVD risk",
            }
    
    # ────────────────────────────────────────────────────────────────
    # Diabetes Indices
    # ────────────────────────────────────────────────────────────────
    fbg = parameters.get("Fasting_Blood_Glucose", {}).get("value")
    fasting_insulin = parameters.get("Fasting_Insulin", {}).get("value")
    if fbg and fasting_insulin:
        homa_ir = (fbg * fasting_insulin) / 405
        indices["HOMA_IR"] = {
            "value": round(homa_ir, 2),
            "formula": "(FBG × Fasting Insulin) / 405",
            "interpretation": f"{homa_ir:.2f}",
            "note": "<1 normal; 1-2 borderline; >2 insulin resistance",
        }
    
    return indices


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def analyze_all_parameters(
    parameters: Dict[str, Any],
    patient_info: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of all blood test parameters.
    
    Args
    ----
    parameters : dict
        Flat dictionary of {param_key: {value, unit, panel, raw_match}}
    patient_info : dict
        Optional {name, age, sex, date, lab_ref, ...}
    
    Returns
    -------
    {
        "summary": {...},
        "parameters": {param: {value, classification, differential, ...}},
        "quality": {...},
        "indices": {...},
        "critical_values": [...],
        "abnormalities": [...],
        "recommendations": [...],
        "panels": {panel: {...}},
    }
    """
    
    if patient_info is None:
        patient_info = {}
    
    sex = patient_info.get("sex", "Default")
    
    # ────────────────────────────────────────────────────────────────
    # Classify all parameters
    # ────────────────────────────────────────────────────────────────
    classified = {}
    abnormalities = []
    critical_values = []
    
    for param_key, param_data in parameters.items():
        if not isinstance(param_data, dict):
            continue
        
        value = param_data.get("value")
        unit = param_data.get("unit", "")
        panel = param_data.get("panel", "Other")
        
        # Skip if no value or is text (qualitative)
        if value is None or isinstance(value, str):
            classified[param_key] = {
                "value": value,
                "unit": unit,
                "panel": panel,
                "classification": {"status": "text_value", "message": str(value), "color": "blue"},
                "differential": None,
            }
            continue
        
        # Classify numeric values
        classification = classify_value(param_key, value, sex)
        differential = None
        
        if classification["status"] not in ("normal", "unknown"):
            # Get differential for abnormal values
            status_type = classification["status"].replace("critical_", "")
            diff_conditions = get_differential_diagnosis(param_key, status_type)
            if diff_conditions:
                differential = {
                    "status": status_type,
                    "conditions": diff_conditions,
                }
            
            # Track abnormalities
            abnormalities.append({
                "parameter": param_key,
                "value": value,
                "classification": classification,
                "differential": differential,
            })
            
            # Track critical values
            if "critical" in classification["status"]:
                critical_values.append({
                    "parameter": param_key,
                    "value": value,
                    "status": classification["status"],
                    "message": classification["message"],
                })
        
        classified[param_key] = {
            "value": value,
            "unit": unit,
            "panel": panel,
            "classification": classification,
            "differential": differential,
        }
    
    # ────────────────────────────────────────────────────────────────
    # Quality checks
    # ────────────────────────────────────────────────────────────────
    quality = check_sample_quality(parameters)
    
    # ────────────────────────────────────────────────────────────────
    # Calculate indices
    # ────────────────────────────────────────────────────────────────
    indices = calculate_indices(parameters)
    
    # ────────────────────────────────────────────────────────────────
    # Panel grouping
    # ────────────────────────────────────────────────────────────────
    panels = {}
    for param_key, param_data in classified.items():
        panel = param_data.get("panel", "Other")
        if panel not in panels:
            panels[panel] = {}
        panels[panel][param_key] = param_data
    
    # ────────────────────────────────────────────────────────────────
    # Summary statistics
    # ────────────────────────────────────────────────────────────────
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "patient_info": patient_info,
        "total_parameters": len(classified),
        "abnormal_count": len(abnormalities),
        "critical_count": len(critical_values),
        "quality_score": quality["quality_score"],
    }
    
    return {
        "summary": summary,
        "parameters": classified,
        "quality": quality,
        "indices": indices,
        "critical_values": critical_values,
        "abnormalities": abnormalities,
        "panels": panels,
    }


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

def get_clinical_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate clinical recommendations based on analysis.
    
    Returns
    -------
    [
        {"priority": "high|medium|low", "category": str, "recommendation": str},
        ...
    ]
    """
    recommendations = []
    
    # Critical values
    if analysis.get("critical_values"):
        recommendations.append({
            "priority": "high",
            "category": "URGENT",
            "recommendation": "CRITICAL VALUES DETECTED. Notify physician immediately. Consider repeat testing to confirm.",
        })
    
    # Poor sample quality
    if analysis["quality"]["quality_score"] < 50:
        recommendations.append({
            "priority": "high",
            "category": "Sample Quality",
            "recommendation": "Sample quality is questionable. REPEAT TEST RECOMMENDED to rule out pre-analytical error.",
        })
    
    # Abnormalities
    abnormalities = analysis.get("abnormalities", [])
    if abnormalities:
        for abnorm in abnormalities[:5]:  # Top 5
            param = abnorm["parameter"]
            value = abnorm["value"]
            classification = abnorm["classification"]
            
            recommendations.append({
                "priority": "high" if "critical" in classification["status"] else "medium",
                "category": f"Parameter: {param}",
                "recommendation": f"{classification['message']} → Consider evaluation for underlying causes.",
            })
    
    # Lipid profile pattern
    ldl = analysis["parameters"].get("LDL_Cholesterol", {})
    hdl = analysis["parameters"].get("HDL_Cholesterol", {})
    if ldl.get("classification", {}).get("status") == "high" and hdl.get("classification", {}).get("status") == "low":
        recommendations.append({
            "priority": "medium",
            "category": "Lipid Pattern",
            "recommendation": "Atherogenic dyslipidemia (high LDL + low HDL). Intensify lifestyle modifications and consider statin therapy.",
        })
    
    # Anemia workup
    hb = analysis["parameters"].get("Hemoglobin", {})
    if hb.get("classification", {}).get("status") == "low":
        recommendations.append({
            "priority": "medium",
            "category": "Anemia Workup",
            "recommendation": "Low hemoglobin. Recommend: iron studies, ferritin, B12, folate, peripheral smear, reticulocyte count.",
        })
    
    # Renal function
    creatinine = analysis["parameters"].get("Serum_Creatinine", {})
    bun = analysis["parameters"].get("BUN", {})
    if creatinine.get("classification", {}).get("status") in ("high", "critical_high"):
        recommendations.append({
            "priority": "medium",
            "category": "Renal Function",
            "recommendation": "Elevated creatinine. Check eGFR, urinalysis, renal ultrasound if new. Adjust medication doses for renal impairment.",
        })
    
    # Glucose control
    fbs = analysis["parameters"].get("Fasting_Blood_Glucose", {})
    hba1c = analysis["parameters"].get("HbA1c", {})
    if fbs.get("classification", {}).get("status") in ("high", "critical_high") or hba1c.get("classification", {}).get("status") in ("high", "critical_high"):
        recommendations.append({
            "priority": "medium",
            "category": "Diabetes Management",
            "recommendation": "Elevated glucose/HbA1c. Optimize diabetes medications, diet, exercise. Check for DKA if severely elevated.",
        })
    
    # Liver function
    alt = analysis["parameters"].get("ALT", {})
    ast = analysis["parameters"].get("AST", {})
    if alt.get("classification", {}).get("status") in ("high", "critical_high") or ast.get("classification", {}).get("status") in ("high", "critical_high"):
        recommendations.append({
            "priority": "medium",
            "category": "Liver Function",
            "recommendation": "Elevated transaminases. Assess for viral hepatitis, fatty liver, cirrhosis. Check viral serology, ultrasound.",
        })
    
    return recommendations


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_summary_report(analysis: Dict[str, Any], patient_info: Optional[Dict] = None) -> str:
    """
    Generate a formatted text summary report.
    
    Returns
    -------
    Formatted multi-line string
    """
    if patient_info is None:
        patient_info = analysis.get("summary", {}).get("patient_info", {})
    
    lines = []
    lines.append("=" * 70)
    lines.append("BLOOD INVESTIGATION ANALYSIS REPORT".center(70))
    lines.append("=" * 70)
    lines.append("")
    
    # Patient info
    if patient_info:
        lines.append("PATIENT INFORMATION")
        lines.append("-" * 70)
        for key, value in patient_info.items():
            if value:
                lines.append(f"  {key.replace('_', ' ').title():.<30} {value}")
        lines.append("")
    
    # Summary
    summary = analysis.get("summary", {})
    lines.append("ANALYSIS SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  Total Parameters Analyzed    {summary.get('total_parameters', 0)}")
    lines.append(f"  Abnormal Values              {summary.get('abnormal_count', 0)}")
    lines.append(f"  Critical Values              {summary.get('critical_count', 0)}")
    lines.append(f"  Sample Quality Score         {summary.get('quality_score', 0)}%")
    lines.append("")
    
    # Quality
    quality = analysis.get("quality", {})
    lines.append("SAMPLE QUALITY ASSESSMENT")
    lines.append("-" * 70)
    lines.append(f"  Status: {quality.get('summary', 'Unknown')}")
    if quality.get("issues"):
        lines.append("  Issues Found:")
        for issue in quality["issues"][:3]:
            severity_mark = "⚠ " if issue.get("severity") == "warning" else "✗ "
            lines.append(f"    {severity_mark}{issue.get('rule', 'Unknown')}")
            lines.append(f"       {issue.get('details', '')}")
    lines.append("")
    
    # Critical values
    critical = analysis.get("critical_values", [])
    if critical:
        lines.append("!!! CRITICAL VALUES !!!")
        lines.append("-" * 70)
        for cv in critical:
            lines.append(f"  ✗ {cv['parameter']}: {cv['value']} ({cv['status']})")
            lines.append(f"    {cv['message']}")
        lines.append("")
    
    # Abnormalities by panel
    panels = analysis.get("panels", {})
    for panel_name, panel_params in sorted(panels.items()):
        panel_abnorms = [p for p in panel_params.values() if p.get("classification", {}).get("status") not in ("normal", "unknown", "text_value")]
        if not panel_abnorms:
            continue
        
        lines.append(f"{panel_name.replace('_', ' ').upper()}")
        lines.append("-" * 70)
        for param_name, param_data in sorted(panel_params.items()):
            status = param_data.get("classification", {}).get("status")
            if status in ("normal", "unknown", "text_value"):
                continue
            
            value = param_data.get("value")
            unit = param_data.get("unit", "")
            message = param_data.get("classification", {}).get("message", "")
            
            lines.append(f"  {param_name}")
            lines.append(f"    Value:     {value} {unit}")
            lines.append(f"    Status:    {message}")
            
            # Differential
            diff = param_data.get("differential")
            if diff and diff.get("conditions"):
                lines.append(f"    Consider:")
                for cond in diff["conditions"][:3]:
                    lines.append(f"      • {cond.get('name', 'Unknown')} - {cond.get('note', '')}")
            lines.append("")
    
    # Recommendations
    recommendations = get_clinical_recommendations(analysis)
    if recommendations:
        lines.append("CLINICAL RECOMMENDATIONS")
        lines.append("-" * 70)
        for rec in recommendations[:5]:
            priority_mark = "🔴 " if rec["priority"] == "high" else "🟡 " if rec["priority"] == "medium" else "🟢 "
            lines.append(f"  {priority_mark}[{rec['priority'].upper()}] {rec['category']}")
            lines.append(f"     {rec['recommendation']}")
        lines.append("")
    
    # Footer
    lines.append("=" * 70)
    lines.append(f"Report generated: {summary.get('analysis_date', 'Unknown')}")
    lines.append("DISCLAIMER: This is an AI-assisted analysis tool for educational purposes.")
    lines.append("Always consult with a qualified healthcare provider for clinical decisions.")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_json(analysis: Dict[str, Any]) -> str:
    """Export analysis to JSON format."""
    return json.dumps(analysis, indent=2, default=str)


def export_to_csv_flat(analysis: Dict[str, Any]) -> str:
    """Export parameters to CSV flat format."""
    lines = ["Parameter,Value,Unit,Panel,Status,Classification"]
    
    for param_name, param_data in analysis.get("parameters", {}).items():
        value = param_data.get("value", "")
        unit = param_data.get("unit", "")
        panel = param_data.get("panel", "")
        classification = param_data.get("classification", {})
        status = classification.get("status", "")
        message = classification.get("message", "")
        
        lines.append(f'"{param_name}","{value}","{unit}","{panel}","{status}","{message}"')
    
    return "\n".join(lines)
