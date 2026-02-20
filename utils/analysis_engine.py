"""
Hematology Analysis Engine
Provides comprehensive analysis of CBC parameters with differential diagnoses.
"""

from typing import Dict, List, Optional, Tuple


# Reference ranges for adults
REFERENCE_RANGES = {
    'RBC': {
        'Male': {'low': 4.5, 'high': 5.5, 'unit': 'x10^12/L', 'critical_low': 2.0, 'critical_high': 8.0},
        'Female': {'low': 4.0, 'high': 5.0, 'unit': 'x10^12/L', 'critical_low': 2.0, 'critical_high': 8.0},
        'Default': {'low': 4.0, 'high': 5.5, 'unit': 'x10^12/L', 'critical_low': 2.0, 'critical_high': 8.0}
    },
    'Hemoglobin': {
        'Male': {'low': 13.5, 'high': 17.5, 'unit': 'g/dL', 'critical_low': 7.0, 'critical_high': 20.0},
        'Female': {'low': 12.0, 'high': 16.0, 'unit': 'g/dL', 'critical_low': 7.0, 'critical_high': 20.0},
        'Default': {'low': 12.0, 'high': 17.5, 'unit': 'g/dL', 'critical_low': 7.0, 'critical_high': 20.0}
    },
    'Hematocrit': {
        'Male': {'low': 38.3, 'high': 48.6, 'unit': '%', 'critical_low': 20.0, 'critical_high': 60.0},
        'Female': {'low': 35.5, 'high': 44.9, 'unit': '%', 'critical_low': 20.0, 'critical_high': 60.0},
        'Default': {'low': 35.5, 'high': 48.6, 'unit': '%', 'critical_low': 20.0, 'critical_high': 60.0}
    },
    'MCV': {
        'Default': {'low': 80.0, 'high': 100.0, 'unit': 'fL', 'critical_low': 50.0, 'critical_high': 130.0}
    },
    'MCH': {
        'Default': {'low': 27.0, 'high': 33.0, 'unit': 'pg', 'critical_low': 15.0, 'critical_high': 45.0}
    },
    'MCHC': {
        'Default': {'low': 32.0, 'high': 36.0, 'unit': 'g/dL', 'critical_low': 25.0, 'critical_high': 40.0}
    },
    'RDW': {
        'Default': {'low': 11.5, 'high': 14.5, 'unit': '%', 'critical_low': 8.0, 'critical_high': 30.0}
    },
    'RDW_SD': {
        'Default': {'low': 35.0, 'high': 56.0, 'unit': 'fL', 'critical_low': 25.0, 'critical_high': 80.0}
    },
    'WBC': {
        'Default': {'low': 4.0, 'high': 11.0, 'unit': 'x10^9/L', 'critical_low': 1.0, 'critical_high': 30.0}
    },
    'Neutrophils': {
        'Default': {'low': 40.0, 'high': 70.0, 'unit': '%', 'critical_low': 5.0, 'critical_high': 95.0}
    },
    'Lymphocytes': {
        'Default': {'low': 20.0, 'high': 40.0, 'unit': '%', 'critical_low': 3.0, 'critical_high': 80.0}
    },
    'Monocytes': {
        'Default': {'low': 2.0, 'high': 8.0, 'unit': '%', 'critical_low': 0.0, 'critical_high': 25.0}
    },
    'Eosinophils': {
        'Default': {'low': 1.0, 'high': 4.0, 'unit': '%', 'critical_low': 0.0, 'critical_high': 30.0}
    },
    'Basophils': {
        'Default': {'low': 0.0, 'high': 1.0, 'unit': '%', 'critical_low': 0.0, 'critical_high': 10.0}
    },
    'Platelets': {
        'Default': {'low': 150.0, 'high': 400.0, 'unit': 'x10^9/L', 'critical_low': 20.0, 'critical_high': 1000.0}
    },
    'MPV': {
        'Default': {'low': 7.5, 'high': 12.5, 'unit': 'fL', 'critical_low': 5.0, 'critical_high': 15.0}
    },
    'PDW': {
        'Default': {'low': 9.0, 'high': 17.0, 'unit': 'fL', 'critical_low': 5.0, 'critical_high': 25.0}
    },
    'Reticulocytes': {
        'Default': {'low': 0.5, 'high': 2.5, 'unit': '%', 'critical_low': 0.0, 'critical_high': 15.0}
    },
    'ESR': {
        'Male': {'low': 0.0, 'high': 15.0, 'unit': 'mm/hr', 'critical_low': 0.0, 'critical_high': 100.0},
        'Female': {'low': 0.0, 'high': 20.0, 'unit': 'mm/hr', 'critical_low': 0.0, 'critical_high': 100.0},
        'Default': {'low': 0.0, 'high': 20.0, 'unit': 'mm/hr', 'critical_low': 0.0, 'critical_high': 100.0}
    },
    'ANC': {
        'Default': {'low': 1.5, 'high': 8.0, 'unit': 'x10^9/L', 'critical_low': 0.5, 'critical_high': 20.0}
    },
    'ALC': {
        'Default': {'low': 1.0, 'high': 4.0, 'unit': 'x10^9/L', 'critical_low': 0.2, 'critical_high': 15.0}
    },
}

# =============================================
# DIFFERENTIAL DIAGNOSIS DATABASE
# =============================================
DIFFERENTIAL_DIAGNOSES = {
    'RBC': {
        'low': {
            'title': 'Decreased RBC Count (Anemia)',
            'differentials': [
                {'condition': 'Iron Deficiency Anemia',
                 'discussion': 'Most common cause worldwide. Microcytic, hypochromic RBCs. Low MCV, MCH, MCHC, elevated RDW. Check ferritin and iron studies.'},
                {'condition': 'Vitamin B12/Folate Deficiency',
                 'discussion': 'Megaloblastic anemia with high MCV. Hypersegmented neutrophils. Check B12, folate, methylmalonic acid.'},
                {'condition': 'Anemia of Chronic Disease (ACD/AI)',
                 'discussion': 'Second most common. Usually normocytic. Ferritin normal/elevated. Low serum iron, low TIBC.'},
                {'condition': 'Hemolytic Anemia',
                 'discussion': 'Premature RBC destruction. Elevated reticulocytes, LDH, indirect bilirubin. Low haptoglobin.'},
                {'condition': 'Aplastic Anemia',
                 'discussion': 'Bone marrow failure with pancytopenia. Low reticulocyte count. Requires bone marrow biopsy.'},
                {'condition': 'Thalassemia',
                 'discussion': 'Inherited globin synthesis disorder. Microcytic with relatively high RBC count. Hemoglobin electrophoresis diagnostic.'},
                {'condition': 'Chronic Kidney Disease',
                 'discussion': 'Decreased erythropoietin production. Usually normocytic. Check renal function.'},
                {'condition': 'Myelodysplastic Syndrome (MDS)',
                 'discussion': 'Clonal disorder with ineffective hematopoiesis. Often macrocytic. Bone marrow biopsy required.'}
            ]
        },
        'high': {
            'title': 'Elevated RBC Count (Erythrocytosis/Polycythemia)',
            'differentials': [
                {'condition': 'Polycythemia Vera',
                 'discussion': 'Myeloproliferative neoplasm. JAK2 V617F mutation in ~95%. Risk of thrombosis.'},
                {'condition': 'Secondary Polycythemia',
                 'discussion': 'Reactive from chronic hypoxia (COPD, sleep apnea, high altitude), EPO-secreting tumors.'},
                {'condition': 'Dehydration',
                 'discussion': 'Decreased plasma volume causes apparent increase. Resolves with hydration.'},
                {'condition': 'Thalassemia Trait',
                 'discussion': 'Elevated RBC with low MCV and low-normal Hb. Mentzer index (MCV/RBC) <13.'}
            ]
        }
    },
    'Hemoglobin': {
        'low': {
            'title': 'Low Hemoglobin (Anemia)',
            'differentials': [
                {'condition': 'Iron Deficiency Anemia',
                 'discussion': 'Most common cause globally. Fatigue, pallor, dyspnea. Check ferritin, iron studies.'},
                {'condition': 'Hemorrhage (Acute or Chronic)',
                 'discussion': 'Acute blood loss dilutional effect takes 24-48 hrs. Chronic loss causes iron deficiency.'},
                {'condition': 'Hemoglobinopathies',
                 'discussion': 'Sickle cell, thalassemias. Hemoglobin electrophoresis or HPLC diagnostic.'},
                {'condition': 'Bone Marrow Infiltration',
                 'discussion': 'Leukemia, lymphoma, metastatic cancer. Leukoerythroblastic picture on smear.'}
            ]
        },
        'high': {
            'title': 'Elevated Hemoglobin',
            'differentials': [
                {'condition': 'Polycythemia Vera',
                 'discussion': 'Hb >16.5 g/dL (men) or >16.0 g/dL (women) is major criterion.'},
                {'condition': 'Chronic Hypoxia',
                 'discussion': 'Compensatory from COPD, heart disease, sleep apnea, high altitude.'},
                {'condition': 'Dehydration',
                 'discussion': 'Hemoconcentration from volume depletion. Corrects with hydration.'},
                {'condition': 'Spurious (Lipemia/High WBC)',
                 'discussion': 'Very high WBC, lipemia, or monoclonal proteins cause turbidity artifact.'}
            ]
        }
    },
    'MCV': {
        'low': {
            'title': 'Microcytosis (Low MCV)',
            'differentials': [
                {'condition': 'Iron Deficiency Anemia',
                 'discussion': 'Most common cause. Low MCV with elevated RDW.'},
                {'condition': 'Thalassemia Trait',
                 'discussion': 'Low MCV with normal/slightly elevated RDW. RBC count often normal/elevated. Mentzer index <13.'},
                {'condition': 'Anemia of Chronic Disease',
                 'discussion': 'Usually normocytic but can be microcytic in ~30%. Ferritin normal/elevated.'},
                {'condition': 'Sideroblastic Anemia',
                 'discussion': 'Congenital or acquired. Ring sideroblasts on bone marrow iron stain.'},
                {'condition': 'Lead Poisoning',
                 'discussion': 'Inhibits heme synthesis. Basophilic stippling. Check blood lead level.'}
            ]
        },
        'high': {
            'title': 'Macrocytosis (High MCV)',
            'differentials': [
                {'condition': 'Vitamin B12 Deficiency',
                 'discussion': 'Megaloblastic anemia, MCV often >110 fL. Hypersegmented neutrophils.'},
                {'condition': 'Folate Deficiency',
                 'discussion': 'Similar to B12 without neurological features. Alcoholism, poor diet, medications.'},
                {'condition': 'Myelodysplastic Syndrome',
                 'discussion': 'Clonal disorder with dysplastic morphology. Common cause in elderly.'},
                {'condition': 'Alcoholism/Liver Disease',
                 'discussion': 'Direct toxic effect or folate deficiency or altered lipid metabolism.'},
                {'condition': 'Hypothyroidism',
                 'discussion': 'Mild macrocytosis. Check TSH and free T4.'},
                {'condition': 'Reticulocytosis',
                 'discussion': 'Reticulocytes are larger than mature RBCs. Check reticulocyte count.'},
                {'condition': 'Medications',
                 'discussion': 'Hydroxyurea, methotrexate, azathioprine, zidovudine.'}
            ]
        }
    },
    'MCHC': {
        'low': {
            'title': 'Low MCHC (Hypochromia)',
            'differentials': [
                {'condition': 'Iron Deficiency Anemia', 'discussion': 'Most common cause. Decreased hemoglobin synthesis.'},
                {'condition': 'Thalassemia', 'discussion': 'Decreased globin chain synthesis.'},
                {'condition': 'Sideroblastic Anemia', 'discussion': 'Impaired heme synthesis.'}
            ]
        },
        'high': {
            'title': 'High MCHC',
            'differentials': [
                {'condition': 'Hereditary Spherocytosis',
                 'discussion': 'RBC membrane defect. MCHC truly elevated >36 g/dL. EMA binding test diagnostic.'},
                {'condition': 'Cold Agglutinin Disease',
                 'discussion': 'Spurious from RBC agglutination. Warming sample to 37C resolves.'},
                {'condition': 'Severe Lipemia',
                 'discussion': 'Turbidity falsely elevates hemoglobin measurement.'},
                {'condition': 'Hemoglobin C Disease',
                 'discussion': 'RBC dehydration from Hb C crystals. Target cells on smear.'}
            ]
        }
    },
    'RDW': {
        'high': {
            'title': 'Elevated RDW (Anisocytosis)',
            'differentials': [
                {'condition': 'Iron Deficiency Anemia', 'discussion': 'Early finding. Mixed normocytic and microcytic cells.'},
                {'condition': 'B12/Folate Deficiency', 'discussion': 'Mixed population of macrocytes and normocytes.'},
                {'condition': 'Myelodysplastic Syndrome', 'discussion': 'Dysplastic erythropoiesis with variable cell sizes.'},
                {'condition': 'Post-Transfusion', 'discussion': 'Transfused RBCs differ in size from patient cells.'},
                {'condition': 'Mixed Nutritional Deficiency', 'discussion': 'Combined iron and B12/folate deficiency.'},
                {'condition': 'Hemoglobinopathies', 'discussion': 'Variable RBC shapes and sizes.'}
            ]
        }
    },
    'WBC': {
        'low': {
            'title': 'Leukopenia (Low WBC)',
            'differentials': [
                {'condition': 'Neutropenia', 'discussion': 'Most common cause. Viral infections, drugs, autoimmune, marrow failure.'},
                {'condition': 'Viral Infections', 'discussion': 'HIV, hepatitis, EBV, CMV, influenza cause transient leukopenia.'},
                {'condition': 'Aplastic Anemia', 'discussion': 'Pancytopenia with hypocellular bone marrow.'},
                {'condition': 'Drug-Induced', 'discussion': 'Chemotherapy, clozapine, carbamazepine, methimazole, sulfonamides.'},
                {'condition': 'Autoimmune', 'discussion': 'SLE, rheumatoid arthritis can cause neutropenia or lymphopenia.'},
                {'condition': 'Hypersplenism', 'discussion': 'Splenomegaly sequesters WBCs.'}
            ]
        },
        'high': {
            'title': 'Leukocytosis (High WBC)',
            'differentials': [
                {'condition': 'Bacterial Infection', 'discussion': 'Most common cause. Left shift, toxic granulation, Dohle bodies.'},
                {'condition': 'Stress/Physiologic', 'discussion': 'Catecholamine demargination of neutrophils.'},
                {'condition': 'Corticosteroid Use', 'discussion': 'Demargination and decreased migration to tissues.'},
                {'condition': 'Chronic Myeloid Leukemia (CML)', 'discussion': 'Full myeloid maturation spectrum. Basophilia. BCR-ABL1.'},
                {'condition': 'Acute Leukemia', 'discussion': 'Can present with very high WBC with circulating blasts.'},
                {'condition': 'Smoking', 'discussion': 'Chronic mild neutrophilic leukocytosis.'}
            ]
        }
    },
    'Platelets': {
        'low': {
            'title': 'Thrombocytopenia (Low Platelets)',
            'differentials': [
                {'condition': 'Immune Thrombocytopenia (ITP)', 'discussion': 'Autoimmune destruction. Diagnosis of exclusion. Large platelets on smear.'},
                {'condition': 'Pseudothrombocytopenia', 'discussion': 'EDTA-induced clumping. Check smear. Repeat with citrate tube.'},
                {'condition': 'DIC', 'discussion': 'Consumptive coagulopathy. Elevated PT/PTT, low fibrinogen, schistocytes.'},
                {'condition': 'TTP/HUS', 'discussion': 'Microangiopathic hemolytic anemia. Schistocytes. ADAMTS13 for TTP.'},
                {'condition': 'Bone Marrow Failure', 'discussion': 'Aplastic anemia, MDS, leukemia. Usually with other cytopenias.'},
                {'condition': 'Drug-Induced', 'discussion': 'HIT, valproic acid, quinine, chemotherapy.'},
                {'condition': 'Liver Disease/Hypersplenism', 'discussion': 'Portal hypertension with platelet sequestration.'}
            ]
        },
        'high': {
            'title': 'Thrombocytosis (High Platelets)',
            'differentials': [
                {'condition': 'Reactive Thrombocytosis', 'discussion': 'Most common (>80%). Infection, inflammation, iron deficiency, surgery.'},
                {'condition': 'Essential Thrombocythemia', 'discussion': 'Myeloproliferative neoplasm. JAK2, CALR, or MPL mutations.'},
                {'condition': 'Iron Deficiency', 'discussion': 'Reactive thrombocytosis. Normalizes with iron replacement.'},
                {'condition': 'Post-Splenectomy', 'discussion': 'Loss of splenic sequestration.'}
            ]
        }
    },
    'MPV': {
        'low': {
            'title': 'Low MPV (Small Platelets)',
            'differentials': [
                {'condition': 'Bone Marrow Suppression', 'discussion': 'Decreased megakaryopoiesis produces small platelets.'},
                {'condition': 'Wiskott-Aldrich Syndrome', 'discussion': 'X-linked. Characteristically small platelets with thrombocytopenia.'},
                {'condition': 'Hypersplenism', 'discussion': 'Spleen sequesters larger platelets.'}
            ]
        },
        'high': {
            'title': 'High MPV (Large Platelets)',
            'differentials': [
                {'condition': 'Immune Thrombocytopenia (ITP)', 'discussion': 'Compensatory large, young platelets.'},
                {'condition': 'Inherited Platelet Disorders', 'discussion': 'Bernard-Soulier, Gray platelet syndrome, MYH9-related disease.'},
                {'condition': 'EDTA Artifact', 'discussion': 'Prolonged EDTA exposure causes platelet swelling.'}
            ]
        }
    },
    'Neutrophils': {
        'low': {
            'title': 'Neutropenia',
            'differentials': [
                {'condition': 'Drug-Induced', 'discussion': 'Chemotherapy, clozapine, carbamazepine, methimazole.'},
                {'condition': 'Viral Infections', 'discussion': 'HIV, hepatitis, EBV, CMV, parvovirus B19.'},
                {'condition': 'Autoimmune Neutropenia', 'discussion': 'Primary or secondary (SLE, Felty syndrome).'},
                {'condition': 'Benign Ethnic Neutropenia', 'discussion': 'Common in African descent. ANC 1.0-1.5 without increased risk.'}
            ]
        },
        'high': {
            'title': 'Neutrophilia',
            'differentials': [
                {'condition': 'Bacterial Infection', 'discussion': 'Most common. Left shift, toxic granulation.'},
                {'condition': 'Corticosteroid Effect', 'discussion': 'Demargination from vessel walls.'},
                {'condition': 'Myeloproliferative Neoplasms', 'discussion': 'CML with persistent neutrophilia and basophilia.'}
            ]
        }
    },
    'Lymphocytes': {
        'low': {
            'title': 'Lymphopenia',
            'differentials': [
                {'condition': 'HIV/AIDS', 'discussion': 'CD4+ T cell depletion.'},
                {'condition': 'Corticosteroid Use', 'discussion': 'Lymphocyte redistribution and apoptosis.'},
                {'condition': 'Severe Infection/Sepsis', 'discussion': 'Lymphocyte apoptosis. Poor prognostic sign.'}
            ]
        },
        'high': {
            'title': 'Lymphocytosis',
            'differentials': [
                {'condition': 'Viral Infections', 'discussion': 'EBV, CMV, hepatitis. Reactive lymphocytes on smear.'},
                {'condition': 'Chronic Lymphocytic Leukemia (CLL)', 'discussion': 'Mature lymphocytes >5 x10^9/L. Smudge cells.'},
                {'condition': 'Pertussis', 'discussion': 'Marked lymphocytosis especially in children.'}
            ]
        }
    },
    'Eosinophils': {
        'high': {
            'title': 'Eosinophilia',
            'differentials': [
                {'condition': 'Allergic Conditions', 'discussion': 'Asthma, allergic rhinitis, eczema. Most common cause.'},
                {'condition': 'Parasitic Infections', 'discussion': 'Tissue-invasive helminths.'},
                {'condition': 'Hypereosinophilic Syndrome', 'discussion': 'Persistent >1.5 x10^9/L with organ damage.'}
            ]
        }
    },
    'Basophils': {
        'high': {
            'title': 'Basophilia',
            'differentials': [
                {'condition': 'Chronic Myeloid Leukemia', 'discussion': 'Characteristic finding in CML.'},
                {'condition': 'Other Myeloproliferative Neoplasms', 'discussion': 'PV, myelofibrosis.'},
                {'condition': 'Allergic/Hypersensitivity', 'discussion': 'Immediate hypersensitivity reactions.'}
            ]
        }
    },
    'Monocytes': {
        'high': {
            'title': 'Monocytosis',
            'differentials': [
                {'condition': 'Chronic Infections', 'discussion': 'TB, endocarditis, brucellosis, fungal infections.'},
                {'condition': 'CMML', 'discussion': 'Persistent monocytosis >1 x10^9/L for >3 months.'},
                {'condition': 'Recovery from Neutropenia', 'discussion': 'Monocytes recover before neutrophils.'}
            ]
        }
    },
    'Reticulocytes': {
        'low': {
            'title': 'Low Reticulocyte Count',
            'differentials': [
                {'condition': 'Aplastic Anemia', 'discussion': 'Bone marrow failure. Low reticulocytes despite anemia.'},
                {'condition': 'Pure Red Cell Aplasia', 'discussion': 'Selective absence of erythroid precursors.'},
                {'condition': 'Nutritional Deficiency (Untreated)', 'discussion': 'Iron, B12, folate before treatment.'}
            ]
        },
        'high': {
            'title': 'Elevated Reticulocyte Count',
            'differentials': [
                {'condition': 'Hemolytic Anemia', 'discussion': 'Compensatory production. Check LDH, haptoglobin, DAT.'},
                {'condition': 'Acute Hemorrhage', 'discussion': 'Marrow response peaks at 7-10 days.'},
                {'condition': 'Response to Treatment', 'discussion': 'Reticulocyte crisis 5-7 days after starting replacement.'}
            ]
        }
    },
    'Hematocrit': {
        'low': {
            'title': 'Low Hematocrit',
            'differentials': [
                {'condition': 'Anemia (Various)', 'discussion': 'Decreased RBC mass from any cause.'},
                {'condition': 'Fluid Overload', 'discussion': 'Hemodilution from IV fluids.'},
                {'condition': 'Pregnancy', 'discussion': 'Physiologic hemodilution.'}
            ]
        },
        'high': {
            'title': 'Elevated Hematocrit',
            'differentials': [
                {'condition': 'Polycythemia Vera', 'discussion': 'HCT >49% men or >48% women. JAK2 testing.'},
                {'condition': 'Dehydration', 'discussion': 'Relative polycythemia. Corrects with hydration.'},
                {'condition': 'Chronic Hypoxia', 'discussion': 'COPD, high altitude, sleep apnea.'}
            ]
        }
    },
    'MCH': {
        'low': {
            'title': 'Low MCH',
            'differentials': [
                {'condition': 'Iron Deficiency', 'discussion': 'Decreased hemoglobin per cell.'},
                {'condition': 'Thalassemia', 'discussion': 'Reduced globin synthesis.'}
            ]
        },
        'high': {
            'title': 'High MCH',
            'differentials': [
                {'condition': 'Macrocytic Anemia', 'discussion': 'Larger cells contain more hemoglobin.'},
                {'condition': 'Spurious', 'discussion': 'Cold agglutinins or lipemia.'}
            ]
        }
    },
    'ESR': {
        'high': {
            'title': 'Elevated ESR',
            'differentials': [
                {'condition': 'Infection', 'discussion': 'Acute and chronic infections.'},
                {'condition': 'Autoimmune/Inflammatory', 'discussion': 'SLE, RA, PMR, GCA. ESR >100 suggests malignancy/vasculitis.'},
                {'condition': 'Malignancy', 'discussion': 'Multiple myeloma classically causes very high ESR.'},
                {'condition': 'Anemia', 'discussion': 'Low hematocrit accelerates sedimentation.'}
            ]
        }
    },
    'PDW': {
        'high': {
            'title': 'Elevated PDW',
            'differentials': [
                {'condition': 'Reactive Thrombocytosis', 'discussion': 'Variable platelet sizes.'},
                {'condition': 'Myeloproliferative Disorders', 'discussion': 'Dysplastic megakaryopoiesis.'}
            ]
        }
    }
}


# =============================================
# CORE FUNCTIONS
# =============================================

def get_reference_range(param: str, sex: str = 'Default') -> Dict:
    """Get reference range for a parameter based on sex."""
    if param in REFERENCE_RANGES:
        ranges = REFERENCE_RANGES[param]
        if sex in ranges:
            return ranges[sex]
        return ranges.get('Default', {})
    return {}


def classify_value(param: str, value: float, sex: str = 'Default') -> Dict:
    """Classify a parameter value as normal, low, high, or critical."""
    ref = get_reference_range(param, sex)
    if not ref:
        return {'status': 'unknown', 'message': 'No reference range available', 'color': 'gray', 'value': value}

    result = {
        'value': value,
        'unit': ref.get('unit', ''),
        'low': ref.get('low'),
        'high': ref.get('high'),
        'critical_low': ref.get('critical_low'),
        'critical_high': ref.get('critical_high'),
    }

    if value < ref.get('critical_low', float('-inf')):
        result['status'] = 'critical_low'
        result['message'] = f'CRITICAL LOW: {value} {ref["unit"]} (Ref: {ref["low"]}-{ref["high"]})'
        result['color'] = 'red'
    elif value > ref.get('critical_high', float('inf')):
        result['status'] = 'critical_high'
        result['message'] = f'CRITICAL HIGH: {value} {ref["unit"]} (Ref: {ref["low"]}-{ref["high"]})'
        result['color'] = 'red'
    elif value < ref.get('low', 0):
        result['status'] = 'low'
        result['message'] = f'LOW: {value} {ref["unit"]} (Ref: {ref["low"]}-{ref["high"]})'
        result['color'] = 'orange'
    elif value > ref.get('high', float('inf')):
        result['status'] = 'high'
        result['message'] = f'HIGH: {value} {ref["unit"]} (Ref: {ref["low"]}-{ref["high"]})'
        result['color'] = 'orange'
    else:
        result['status'] = 'normal'
        result['message'] = f'NORMAL: {value} {ref["unit"]} (Ref: {ref["low"]}-{ref["high"]})'
        result['color'] = 'green'

    return result


def get_differential_diagnosis(param: str, status: str) -> Optional[Dict]:
    """Get differential diagnosis for an abnormal parameter."""
    if param in DIFFERENTIAL_DIAGNOSES:
        direction = status.replace('critical_', '')
        if direction in DIFFERENTIAL_DIAGNOSES[param]:
            return DIFFERENTIAL_DIAGNOSES[param][direction]
    return None


def check_sample_quality(parameters: Dict) -> List[Dict]:
    """Check sample quality using various rules and consistency checks."""
    issues = []

    rbc = parameters.get('RBC', {}).get('value')
    hb = parameters.get('Hemoglobin', {}).get('value')
    hct = parameters.get('Hematocrit', {}).get('value')

    if rbc and hb and hct:
        expected_hb = rbc * 3
        hb_diff = abs(hb - expected_hb)
        if hb_diff > 1.5:
            issues.append({
                'rule': 'Rule of Threes (RBC x 3 = Hb)',
                'expected': f'{expected_hb:.1f} g/dL',
                'actual': f'{hb:.1f} g/dL',
                'deviation': f'{hb_diff:.1f} g/dL',
                'severity': 'warning' if hb_diff < 3.0 else 'error',
                'interpretation': 'RBC x 3 should equal Hb. Deviation suggests spurious results, thalassemia, or iron deficiency.'
            })

        expected_hct = hb * 3
        hct_diff = abs(hct - expected_hct)
        if hct_diff > 3.0:
            issues.append({
                'rule': 'Rule of Threes (Hb x 3 = HCT)',
                'expected': f'{expected_hct:.1f}%',
                'actual': f'{hct:.1f}%',
                'deviation': f'{hct_diff:.1f}%',
                'severity': 'warning' if hct_diff < 6.0 else 'error',
                'interpretation': 'Hb x 3 should equal HCT. Deviation may indicate sample issues or abnormal hemoglobin.'
            })

    mcv = parameters.get('MCV', {}).get('value')
    if rbc and hct and mcv:
        calculated_mcv = (hct * 10) / rbc
        mcv_diff = abs(mcv - calculated_mcv)
        if mcv_diff > 5:
            issues.append({
                'rule': 'MCV Consistency (HCT x 10 / RBC)',
                'expected': f'{calculated_mcv:.1f} fL',
                'actual': f'{mcv:.1f} fL',
                'deviation': f'{mcv_diff:.1f} fL',
                'severity': 'warning',
                'interpretation': 'Measured MCV differs from calculated. May indicate instrument issues or RBC agglutination.'
            })

    mchc = parameters.get('MCHC', {}).get('value')
    if mchc and mchc > 36.5:
        issues.append({
            'rule': 'MCHC Upper Limit Check',
            'expected': '32.0-36.0 g/dL',
            'actual': f'{mchc:.1f} g/dL',
            'deviation': f'{mchc - 36.0:.1f} g/dL above',
            'severity': 'warning',
            'interpretation': 'MCHC >36 may indicate spherocytosis, cold agglutinins, or lipemia artifact.'
        })

    diff_params = ['Neutrophils', 'Lymphocytes', 'Monocytes', 'Eosinophils', 'Basophils']
    diff_values = [parameters.get(p, {}).get('value') for p in diff_params]
    diff_values = [v for v in diff_values if v is not None]

    if len(diff_values) >= 3:
        diff_sum = sum(diff_values)
        if abs(diff_sum - 100) > 5:
            issues.append({
                'rule': 'WBC Differential Sum',
                'expected': '100%',
                'actual': f'{diff_sum:.1f}%',
                'deviation': f'{abs(diff_sum - 100):.1f}%',
                'severity': 'warning' if abs(diff_sum - 100) < 10 else 'error',
                'interpretation': 'WBC differential should sum to ~100%. Deviation may indicate extraction errors.'
            })

    plt_val = parameters.get('Platelets', {}).get('value')
    mpv_val = parameters.get('MPV', {}).get('value')
    if plt_val and mpv_val:
        if plt_val > 400 and mpv_val > 11:
            issues.append({
                'rule': 'Platelet-MPV Inverse Relationship',
                'expected': 'High platelets with Low-normal MPV',
                'actual': f'Plt: {plt_val:.0f}, MPV: {mpv_val:.1f}',
                'deviation': 'Both elevated',
                'severity': 'info',
                'interpretation': 'Both elevated may suggest myeloproliferative neoplasm.'
            })
        elif plt_val < 150 and mpv_val < 8:
            issues.append({
                'rule': 'Platelet-MPV Inverse Relationship',
                'expected': 'Low platelets with High MPV',
                'actual': f'Plt: {plt_val:.0f}, MPV: {mpv_val:.1f}',
                'deviation': 'Both decreased',
                'severity': 'info',
                'interpretation': 'Both low suggests bone marrow suppression rather than peripheral destruction.'
            })

    if not issues:
        issues.append({
            'rule': 'Overall Quality Assessment',
            'expected': 'All checks passed',
            'actual': 'All checks passed',
            'deviation': 'None',
            'severity': 'pass',
            'interpretation': 'No quality issues detected. Results appear internally consistent.'
        })

    return issues


# =============================================
# ADDITIONAL CALCULATED INDICES
# =============================================

def get_anc_interpretation(anc: float) -> str:
    if anc < 0.2:
        return f'{anc:.2f} x10^9/L - Very severe neutropenia (high infection risk)'
    elif anc < 0.5:
        return f'{anc:.2f} x10^9/L - Severe neutropenia'
    elif anc < 1.0:
        return f'{anc:.2f} x10^9/L - Moderate neutropenia'
    elif anc < 1.5:
        return f'{anc:.2f} x10^9/L - Mild neutropenia'
    elif anc <= 8.0:
        return f'{anc:.2f} x10^9/L - Normal'
    else:
        return f'{anc:.2f} x10^9/L - Neutrophilia'


def get_nlr_interpretation(nlr: float) -> str:
    if nlr < 1:
        return f'{nlr:.2f} - Low (consider viral infection or neutropenia)'
    elif nlr <= 3:
        return f'{nlr:.2f} - Normal'
    elif nlr <= 9:
        return f'{nlr:.2f} - Mildly elevated (mild stress/infection)'
    else:
        return f'{nlr:.2f} - Significantly elevated (severe infection/inflammation)'


def calculate_additional_indices(parameters: Dict) -> Dict:
    """Calculate additional hematological indices."""
    indices = {}

    rbc = parameters.get('RBC', {}).get('value')
    mcv = parameters.get('MCV', {}).get('value')
    hb = parameters.get('Hemoglobin', {}).get('value')
    hct = parameters.get('Hematocrit', {}).get('value')
    wbc = parameters.get('WBC', {}).get('value')
    neut_pct = parameters.get('Neutrophils', {}).get('value')
    lymph_pct = parameters.get('Lymphocytes', {}).get('value')

    if mcv and rbc and rbc > 0:
        mentzer = mcv / rbc
        indices['Mentzer Index'] = {
            'value': round(mentzer, 1),
            'interpretation': 'Suggests thalassemia trait' if mentzer < 13 else 'Suggests iron deficiency',
            'formula': 'MCV / RBC',
            'note': '<13 = thalassemia trait; >13 = iron deficiency'
        }

    if hb and hct and hct > 0:
        calc_mchc = (hb / hct) * 100
        indices['Calculated MCHC'] = {
            'value': round(calc_mchc, 1),
            'interpretation': f'{calc_mchc:.1f} g/dL',
            'formula': '(Hb / HCT) x 100',
            'note': 'Should match reported MCHC'
        }

    if hb and rbc and rbc > 0:
        calc_mch = (hb / rbc) * 10
        indices['Calculated MCH'] = {
            'value': round(calc_mch, 1),
            'interpretation': f'{calc_mch:.1f} pg',
            'formula': '(Hb / RBC) x 10',
            'note': 'Should match reported MCH'
        }

    if wbc and neut_pct:
        anc = wbc * (neut_pct / 100)
        indices['Calculated ANC'] = {
            'value': round(anc, 2),
            'interpretation': get_anc_interpretation(anc),
            'formula': 'WBC x (Neutrophils% / 100)',
            'note': '<1.5 = neutropenia; <0.5 = severe'
        }

    if wbc and lymph_pct:
        alc = wbc * (lymph_pct / 100)
        indices['Calculated ALC'] = {
            'value': round(alc, 2),
            'interpretation': f'{alc:.2f} x10^9/L',
            'formula': 'WBC x (Lymphocytes% / 100)',
            'note': 'Normal: 1.0-4.0 x10^9/L'
        }

    if neut_pct and lymph_pct and lymph_pct > 0:
        nlr = neut_pct / lymph_pct
        indices['NLR'] = {
            'value': round(nlr, 2),
            'interpretation': get_nlr_interpretation(nlr),
            'formula': 'Neutrophils% / Lymphocytes%',
            'note': 'Normal: 1-3; Elevated in infection/inflammation'
        }

    return indices


# =============================================
# MAIN ANALYSIS FUNCTION
# =============================================

def analyze_all_parameters(parameters: Dict, sex: str = 'Default') -> Dict:
    """Perform comprehensive analysis of all parameters."""
    results = {}
    abnormalities = []
    critical_values = []

    for param_name, param_data in parameters.items():
        value = param_data.get('value')
        if value is None:
            continue

        classification = classify_value(param_name, value, sex)
        differential = None

        if classification['status'] not in ['normal', 'unknown']:
            differential = get_differential_diagnosis(param_name, classification['status'])
            abnormalities.append({
                'parameter': param_name,
                'classification': classification,
                'differential': differential
            })
            if 'critical' in classification['status']:
                critical_values.append({
                    'parameter': param_name,
                    'value': value,
                    'status': classification['status'],
                    'message': classification['message']
                })

        results[param_name] = {
            'value': value,
            'unit': param_data.get('unit', classification.get('unit', '')),
            'classification': classification,
            'differential': differential
        }

    quality_checks = check_sample_quality(parameters)
    calculated_indices = calculate_additional_indices(parameters)

    return {
        'parameters': results,
        'abnormalities': abnormalities,
        'critical_values': critical_values,
        'quality_checks': quality_checks,
        'calculated_indices': calculated_indices,
        'total_parameters': len(results),
        'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values)
    }


# =============================================
# TEXT SUMMARY GENERATOR
# =============================================

def generate_summary_text(analysis: Dict, patient_info: Dict) -> str:
    """Generate a text summary of the analysis."""
    lines = []
    lines.append("=" * 60)
    lines.append("HEMATOLOGY BLOOD INVESTIGATION ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")

    if patient_info:
        lines.append("PATIENT INFORMATION")
        lines.append("-" * 40)
        for key, value in patient_info.items():
            if value:
                lines.append(f"  {key.capitalize()}: {value}")
        lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Parameters Analyzed: {analysis.get('total_parameters', 0)}")
    lines.append(f"  Abnormal Values: {analysis.get('abnormal_count', 0)}")
    lines.append(f"  Critical Values: {analysis.get('critical_count', 0)}")
    lines.append("")

    if analysis.get('critical_values'):
        lines.append("!!! CRITICAL VALUES ALERT !!!")
        lines.append("-" * 40)
        for cv in analysis['critical_values']:
            lines.append(f"  {cv['parameter']}: {cv['message']}")
        lines.append("")

    lines.append("SAMPLE QUALITY ASSESSMENT")
    lines.append("-" * 40)
    for check in analysis.get('quality_checks', []):
        severity_label = check.get('severity', 'info').upper()
        lines.append(f"  [{severity_label}] {check['rule']}")
        lines.append(f"    Expected: {check['expected']} | Actual: {check['actual']}")
        lines.append(f"    {check['interpretation']}")
        lines.append("")

    lines.append("DETAILED PARAMETER ANALYSIS")
    lines.append("-" * 40)
    for param_name, param_data in analysis.get('parameters', {}).items():
        classification = param_data.get('classification', {})
        status_label = classification.get('status', 'unknown').upper()
        lines.append(f"\n  {param_name}: {param_data['value']} {param_data.get('unit', '')}")
        lines.append(f"    Status: {status_label}")
        if classification.get('low') is not None:
            lines.append(f"    Reference: {classification['low']}-{classification['high']} {classification.get('unit', '')}")

        if param_data.get('differential'):
            diff = param_data['differential']
            lines.append(f"\n    Differential Diagnosis: {diff['title']}")
            for i, d in enumerate(diff.get('differentials', []), 1):
                lines.append(f"      {i}. {d['condition']}")
                lines.append(f"         {d['discussion']}")

    if analysis.get('calculated_indices'):
        lines.append("\n" + "=" * 60)
        lines.append("CALCULATED INDICES")
        lines.append("-" * 40)
        for idx_name, idx_data in analysis['calculated_indices'].items():
            lines.append(f"  {idx_name}: {idx_data['value']}")
            lines.append(f"    Formula: {idx_data['formula']}")
            lines.append(f"    Interpretation: {idx_data['interpretation']}")
            lines.append(f"    Note: {idx_data['note']}")
            lines.append("")

    lines.append("\n" + "=" * 60)
    lines.append("DISCLAIMER: This analysis is for educational purposes only.")
    lines.append("Always consult qualified medical professionals for diagnosis.")
    lines.append("=" * 60)

    return "\n".join(lines)
