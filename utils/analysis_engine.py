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
    'Reti
