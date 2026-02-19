"""
Hematology Analysis Engine
Provides comprehensive analysis of CBC parameters with differential diagnoses.
"""

from typing import Dict, List, Optional, Tuple


# Reference ranges for adults
REFERENCE_RANGES = {
    'RBC': {
        'Male': {'low': 4.5, 'high': 5.5, 'unit': 'x10¹²/L', 'critical_low': 2.0, 'critical_high': 8.0},
        'Female': {'low': 4.0, 'high': 5.0, 'unit': 'x10¹²/L', 'critical_low': 2.0, 'critical_high': 8.0},
        'Default': {'low': 4.0, 'high': 5.5, 'unit': 'x10¹²/L', 'critical_low': 2.0, 'critical_high': 8.0}
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
        'Default': {'low': 4.0, 'high': 11.0, 'unit': 'x10⁹/L', 'critical_low': 1.0, 'critical_high': 30.0}
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
        'Default': {'low': 150.0, 'high': 400.0, 'unit': 'x10⁹/L', 'critical_low': 20.0, 'critical_high': 1000.0}
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
        'Default': {'low': 1.5, 'high': 8.0, 'unit': 'x10⁹/L', 'critical_low': 0.5, 'critical_high': 20.0}
    },
    'ALC': {
        'Default': {'low': 1.0, 'high': 4.0, 'unit': 'x10⁹/L', 'critical_low': 0.2, 'critical_high': 15.0}
    },
}

# Differential diagnosis database
DIFFERENTIAL_DIAGNOSES = {
    'RBC': {
        'low': {
            'title': 'Decreased RBC Count (Anemia)',
            'differentials': [
                {
                    'condition': 'Iron Deficiency Anemia',
                    'discussion': 'Most common cause of anemia worldwide. Results from inadequate iron for hemoglobin synthesis. '
                                 'Typically presents with microcytic, hypochromic RBCs. Low MCV, low MCH, low MCHC, elevated RDW. '
                                 'Serum ferritin is the most useful initial test. Iron studies show low serum iron, high TIBC, low transferrin saturation.'
                },
                {
                    'condition': 'Vitamin B12/Folate Deficiency',
                    'discussion': 'Causes megaloblastic anemia with macrocytic RBCs (high MCV). May see hypersegmented neutrophils on smear. '
                                 'B12 deficiency can cause neurological symptoms. Check serum B12, folate, methylmalonic acid, homocysteine.'
                },
                {
                    'condition': 'Anemia of Chronic Disease/Inflammation (ACD/AI)',
                    'discussion': 'Second most common cause of anemia. Associated with chronic infections, autoimmune diseases, malignancy. '
                                 'Usually normocytic, normochromic but can be microcytic. Ferritin is normal or elevated (acute phase reactant). '
                                 'Low serum iron, low TIBC, low transferrin saturation.'
                },
                {
                    'condition': 'Hemolytic Anemia',
                    'discussion': 'Premature destruction of RBCs. Can be hereditary (spherocytosis, G6PD deficiency, sickle cell) or acquired '
                                 '(autoimmune, microangiopathic). Elevated reticulocyte count, elevated LDH, elevated indirect bilirubin, '
                                 'low haptoglobin. Peripheral smear may show spherocytes, schistocytes, or sickle cells.'
                },
                {
                    'condition': 'Aplastic Anemia',
                    'discussion': 'Bone marrow failure with pancytopenia. Low RBCs, WBCs, and platelets. Reticulocyte count is low. '
                                 'Requires bone marrow biopsy for diagnosis. Can be acquired or inherited (Fanconi anemia).'
                },
                {
                    'condition': 'Thalassemia',
                    'discussion': 'Inherited disorder of globin chain synthesis. Alpha or beta thalassemia. Microcytic anemia with '
                                 'relatively high RBC count. Low MCV, normal or slightly elevated RDW. Hemoglobin electrophoresis is diagnostic.'
                },
                {
                    'condition': 'Chronic Kidney Disease',
                    'discussion': 'Decreased erythropoietin production leads to decreased RBC production. Usually normocytic, normochromic. '
                                 'Check renal function (BUN, creatinine, GFR). May require erythropoiesis-stimulating agents.'
                },
                {
                    'condition': 'Myelodysplastic Syndrome (MDS)',
                    'discussion': 'Clonal hematopoietic disorder with ineffective hematopoiesis. May present with macrocytic anemia. '
                                 'Peripheral smear may show dysplastic features. Bone marrow biopsy is required for diagnosis.'
                }
            ]
        },
        'high': {
            'title': 'Elevated RBC Count (Erythrocytosis/Polycythemia)',
            'differentials': [
                {
                    'condition': 'Polycythemia Vera',
                    'discussion': 'Myeloproliferative neoplasm with JAK2 V617F mutation in ~95% of cases. Elevated RBC mass, often with '
                                 'elevated WBC and platelets. Risk of thrombosis. Requires JAK2 mutation testing, EPO level, bone marrow biopsy.'
                },
                {
                    'condition': 'Secondary Polycythemia',
                    'discussion': 'Reactive erythrocytosis due to increased EPO production. Causes include chronic hypoxia (COPD, sleep apnea, '
                                 'high altitude), EPO-secreting tumors (renal cell carcinoma, hepatocellular carcinoma), smoking.'
                },
                {
                    'condition': 'Dehydration (Relative Polycythemia)',
                    'discussion': 'Decreased plasma volume leads to apparent increase in RBC concentration. All cell counts may appear elevated. '
                                 'Resolves with adequate hydration.'
                },
                {
                    'condition': 'Thalassemia Trait',
                    'discussion': 'Heterozygous thalassemia can present with elevated RBC count but low MCV and low-normal hemoglobin. '
                                 'Mentzer index (MCV/RBC) <13 suggests thalassemia trait.'
                }
            ]
        }
    },
    'Hemoglobin': {
        'low': {
            'title': 'Low Hemoglobin (Anemia)',
            'differentials': [
                {
                    'condition': 'Iron Deficiency Anemia',
                    'discussion': 'Decreased hemoglobin synthesis due to iron deficiency. Most common cause of anemia globally. '
                                 'Symptoms include fatigue, pallor, dyspnea on exertion, pica, koilonychia. Check ferritin, iron studies.'
                },
                {
                    'condition': 'Hemorrhage (Acute or Chronic)',
                    'discussion': 'Acute blood loss may not immediately show decreased hemoglobin (dilutional effect takes 24-48 hours). '
                                 'Chronic blood loss (GI bleeding, menorrhagia) leads to iron deficiency over time.'
                },
                {
                    'condition': 'Hemoglobinopathies',
                    'discussion': 'Sickle cell disease, thalassemias, and other hemoglobin variants can cause chronic anemia. '
                                 'Hemoglobin electrophoresis or HPLC is diagnostic.'
                },
                {
                    'condition': 'Bone Marrow Infiltration',
                    'discussion': 'Leukemia, lymphoma, metastatic cancer, or myelofibrosis can replace normal marrow. '
                                 'Leukoerythroblastic picture on peripheral smear (nucleated RBCs, tear-drop cells, immature WBCs).'
                }
            ]
        },
        'high': {
            'title': 'Elevated Hemoglobin',
            'differentials': [
                {
                    'condition': 'Polycythemia Vera',
                    'discussion': 'Primary myeloproliferative neoplasm. Hemoglobin >16.5 g/dL in men or >16.0 g/dL in women is a major criterion.'
                },
                {
                    'condition': 'Chronic Hypoxia',
                    'discussion': 'Compensatory erythrocytosis from COPD, congenital heart disease, obstructive sleep apnea, high altitude residence.'
                },
                {
                    'condition': 'Dehydration',
                    'discussion': 'Hemoconcentration from volume depletion. Will correct with hydration.'
                },
                {
                    'condition': 'Spurious (Lipemia/High WBC)',
                    'discussion': 'Very high WBC count (>100 x10⁹/L), lipemia, or monoclonal proteins can cause spuriously elevated hemoglobin '
                                 'due to turbidity in the colorimetric measurement method.'
                }
            ]
        }
    },
    'MCV': {
        'low': {
            'title': 'Microcytosis (Low MCV)',
            'differentials': [
                {
                    'condition': 'Iron Deficiency Anemia',
                    'discussion': 'Most common cause of microcytic anemia. Low MCV with elevated RDW. '
                                 'Progressive iron depletion: depleted stores then iron deficient erythropoiesis then iron deficiency anemia.'
                },
                {
                    'condition': 'Thalassemia Trait',
                    'discussion': 'Alpha or beta thalassemia trait shows low MCV with normal to slightly elevated RDW. '
                                 'RBC count is often elevated or normal. Mentzer index (MCV/RBC) <13 suggests thalassemia.'
                },
                {
                    'condition': 'Anemia of Chronic Disease',
                    'discussion': 'Usually normocytic but can be microcytic in about 30 percent of cases. Ferritin is normal or elevated.'
                },
                {
                    'condition': 'Sideroblastic Anemia',
                    'discussion': 'Can be congenital (X-linked) or acquired (MDS, drugs, lead poisoning). '
                                 'Ring sideroblasts on iron stain of bone marrow aspirate. Dimorphic RBC population may be seen.'
                },
                {
                    'condition': 'Lead Poisoning',
                    'discussion': 'Inhibits heme synthesis enzymes. Basophilic stippling on peripheral smear. '
                                 'Check blood lead level, free erythrocyte protoporphyrin.'
                }
            ]
        },
        'high': {
            'title': 'Macrocytosis (High MCV)',
            'differentials': [
                {
                    'condition': 'Vitamin B12 Deficiency',
                    'discussion': 'Megaloblastic anemia with MCV often >110 fL. Hypersegmented neutrophils on smear. '
                                 'Causes: pernicious anemia, malabsorption, strict vegan diet, nitrous oxide exposure.'
                },
                {
                    'condition': 'Folate Deficiency',
                    'discussion': 'Megaloblastic anemia similar to B12 deficiency but without neurological features. '
                                 'Causes: poor dietary intake, alcoholism, pregnancy, medications (methotrexate, trimethoprim).'
                },
                {
                    'condition': 'Myelodysplastic Syndrome',
                    'discussion': 'Clonal stem cell disorder with dysplastic morphology. Macrocytic anemia is common. '
                                 'May see pseudo-Pelger-Huet cells, hypogranular neutrophils, dysplastic megakaryocytes.'
                },
                {
                    'condition': 'Alcoholism/Liver Disease',
                    'discussion': 'Common cause of macrocytosis. May be due to direct toxic effect on erythropoiesis, '
                                 'folate deficiency, or altered lipid metabolism affecting RBC membrane.'
                },
                {
                    'condition': 'Hypothyroidism',
                    'discussion': 'Mild macrocytosis may occur. Check TSH and free T4.'
                },
                {
                    'condition': 'Reticulocytosis',
                    'discussion': 'Reticulocytes are larger than mature RBCs. High reticulocyte count (hemolysis, hemorrhage, recovery) '
                                 'can raise the MCV. Check reticulocyte count.'
                },
                {
                    'condition': 'Medications',
                    'discussion': 'Hydroxyurea, methotrexate, azathioprine, zidovudine, and other drugs can cause macrocytosis.'
                }
            ]
        }
    },
    'MCHC': {
        'low': {
            'title': 'Low MCHC (Hypochromia)',
            'differentials': [
                {
                    'condition': 'Iron Deficiency Anemia',
                    'discussion': 'Most common cause of low MCHC. Decreased hemoglobin synthesis leads to hypochromic cells.'
                },
                {
                    'condition': 'Thalassemia',
                    'discussion': 'Decreased globin chain synthesis leads to reduced hemoglobin content.'
                },
                {
                    'condition': 'Sideroblastic Anemia',
                    'discussion': 'Impaired heme synthesis with iron loading of mitochondria.'
                }
            ]
        },
        'high': {
            'title': 'High MCHC',
            'differentials': [
                {
                    'condition': 'Hereditary Spherocytosis',
                    'discussion': 'RBC membrane defect causing spherical RBCs with reduced surface area. MCHC is truly elevated (>36 g/dL). '
                                 'Osmotic fragility test, eosin-5-maleimide (EMA) binding test for diagnosis.'
                },
                {
                    'condition': 'Cold Agglutinin Disease',
                    'discussion': 'Spurious elevation due to RBC agglutination. Multiple RBCs counted as single large cell. '
                                 'Warming the sample to 37C resolves the artifact.'
                },
                {
                    'condition': 'Severe Lipemia',
                    'discussion': 'Turbidity from lipemia falsely elevates hemoglobin measurement, leading to spuriously high MCHC.'
                },
                {
                    'condition': 'Hemoglobin C Disease',
                    'discussion': 'Hemoglobin C crystals cause RBC dehydration. Target cells and crystal-containing cells on smear.'
                }
            ]
        }
    },
    'RDW': {
        'high': {
            'title': 'Elevated RDW (Anisocytosis)',
            'differentials': [
                {
                    'condition': 'Iron Deficiency Anemia',
                    'discussion': 'Elevated RDW is an early finding in iron deficiency. Mixed population of normocytic and microcytic cells.'
                },
                {
                    'condition': 'B12/Folate Deficiency',
                    'discussion': 'Mixed population of macrocytes and normocytes causes elevated RDW.'
                },
                {
                    'condition': 'Myelodysplastic Syndrome',
                    'discussion': 'Dysplastic erythropoiesis produces RBCs of variable size.'
                },
                {
                    'condition': 'Post-Transfusion',
                    'discussion': 'Transfused RBCs may differ in size from patient own cells, widening the distribution.'
                },
                {
                    'condition': 'Mixed Nutritional Deficiency',
                    'discussion': 'Combined iron and B12/folate deficiency produces both micro and macrocytes.'
                },
                {
                    'condition': 'Hemoglobinopathies',
                    'discussion': 'Sickle cell disease and other hemoglobinopathies can produce elevated RDW.'
                }
            ]
        }
    },
    'WBC': {
        'low': {
            'title': 'Leukopenia (Low WBC)',
            'differentials': [
                {
                    'condition': 'Neutropenia',
                    'discussion': 'Most common cause of leukopenia. Can be due to infections (viral), drugs, autoimmune conditions, bone marrow failure.'
                },
                {
                    'condition': 'Viral Infections',
                    'discussion': 'Many viral infections (HIV, hepatitis, EBV, CMV, influenza) cause transient leukopenia.'
                },
                {
                    'condition': 'Aplastic Anemia',
                    'discussion': 'Pancytopenia with hypocellular bone marrow.'
                },
                {
                    'condition': 'Drug-Induced',
                    'discussion': 'Chemotherapy, clozapine, carbamazepine, methimazole, sulfonamides, and many others.'
                },
                {
                    'condition': 'Autoimmune',
                    'discussion': 'SLE, rheumatoid arthritis can cause neutropenia or lymphopenia.'
                },
                {
                    'condition': 'Hypersplenism',
                    'discussion': 'Splenomegaly from any cause can sequester WBCs.'
                }
            ]
 
