"""
Liver Function Test (LFT) Analysis Engine
Ported from the HTML/JavaScript LFT Analyzer with full Python logic.
"""

from typing import Dict, List, Optional


# ── Reference Ranges ────────────────────────────────────────────────
LFT_REFERENCE_RANGES = {
    'ALT': {
        'male': {'low': 0, 'high': 33, 'unit': 'IU/L'},
        'female': {'low': 0, 'high': 25, 'unit': 'IU/L'},
    },
    'AST': {
        'male': {'low': 0, 'high': 40, 'unit': 'IU/L'},
        'female': {'low': 0, 'high': 32, 'unit': 'IU/L'},
    },
    'ALP': {
        'default': {'low': 30, 'high': 120, 'unit': 'IU/L'},
    },
    'Total_Bilirubin': {
        'default': {'low': 0.3, 'high': 1.0, 'unit': 'mg/dL'},
    },
    'Direct_Bilirubin': {
        'default': {'low': 0.0, 'high': 0.3, 'unit': 'mg/dL'},
    },
    'Albumin': {
        'default': {'low': 3.3, 'high': 5.5, 'unit': 'g/dL'},
    },
    'PT': {
        'default': {'low': 11.0, 'high': 13.0, 'unit': 'seconds'},
    },
    'INR': {
        'default': {'low': 0.8, 'high': 1.1, 'unit': ''},
    },
    'GGT': {
        'male': {'low': 0, 'high': 60, 'unit': 'IU/L'},
        'female': {'low': 0, 'high': 40, 'unit': 'IU/L'},
    },
}

# ── Differential Diagnosis Database ─────────────────────────────────
LFT_DIFFERENTIALS = {
    'hepatocellular': [
        {
            'condition': 'Viral Hepatitis (A, B, C, E)',
            'discussion': 'Most common infectious cause of hepatocellular injury worldwide. ALT is typically higher '
                          'than AST. Acute hepatitis A/E: often self-limited. Hepatitis B/C: can become chronic. '
                          'Order: HBsAg, anti-HBc IgM, anti-HCV, anti-HAV IgM, anti-HEV IgM.'
        },
        {
            'condition': 'Drug-Induced Liver Injury (DILI)',
            'discussion': 'Acetaminophen is the most common cause of acute liver failure. Many drugs and supplements '
                          'can cause hepatocellular injury. Detailed medication and supplement history is essential. '
                          'Causality assessment using RUCAM score. Acetaminophen level if overdose suspected.'
        },
        {
            'condition': 'Alcoholic Liver Disease',
            'discussion': 'AST/ALT ratio >2:1 is characteristic. AST rarely exceeds 300 IU/L in isolated alcoholic '
                          'hepatitis. GGT is usually markedly elevated. Assess for Maddrey discriminant function if '
                          'alcoholic hepatitis suspected.'
        },
        {
            'condition': 'Non-Alcoholic Fatty Liver Disease (NAFLD/NASH)',
            'discussion': 'Most common cause of chronic transaminase elevation in Western countries. Associated with '
                          'metabolic syndrome, obesity, diabetes. ALT usually > AST. Ultrasound may show hepatic steatosis. '
                          'FIB-4 or NAFLD Fibrosis Score for risk stratification.'
        },
        {
            'condition': 'Autoimmune Hepatitis',
            'discussion': 'Predominantly affects women. Check ANA, ASMA, anti-LKM1, IgG levels. Can present acutely '
                          'or chronically. Liver biopsy often needed for definitive diagnosis. Responds to immunosuppression.'
        },
        {
            'condition': 'Wilson Disease',
            'discussion': 'Consider in patients <40 years. Low ceruloplasmin, high 24-hour urine copper, '
                          'Kayser-Fleischer rings on slit lamp exam. AST/ALT ratio may be >2:1 with ALP/bilirubin '
                          'ratio <4 in acute Wilson disease.'
        },
        {
            'condition': 'Hemochromatosis',
            'discussion': 'Hereditary iron overload. Elevated ferritin and transferrin saturation (>45%). '
                          'HFE gene testing (C282Y, H63D). Liver biopsy or MRI for iron quantification.'
        },
        {
            'condition': 'Ischemic Hepatitis (Shock Liver)',
            'discussion': 'Massive transaminase elevation (often >1000 IU/L) following hypotension or cardiac failure. '
                          'LDH is markedly elevated. ALT/LDH ratio <1.5. Rapid improvement with hemodynamic support.'
        }
    ],
    'cholestatic': [
        {
            'condition': 'Choledocholithiasis (Common Bile Duct Stones)',
            'discussion': 'Most common cause of extrahepatic cholestasis. RUQ ultrasound is first-line imaging. '
                          'Dilated bile ducts on ultrasound → MRCP or ERCP. May present with Charcot triad '
                          '(fever, jaundice, RUQ pain) or Reynold pentad (+ hypotension, altered mental status).'
        },
        {
            'condition': 'Primary Biliary Cholangitis (PBC)',
            'discussion': 'Autoimmune destruction of intrahepatic bile ducts. Anti-mitochondrial antibody (AMA) is '
                          'diagnostic (>95% specific). Predominantly affects middle-aged women. IgM elevated. '
                          'Treatment: ursodeoxycholic acid (UDCA).'
        },
        {
            'condition': 'Primary Sclerosing Cholangitis (PSC)',
            'discussion': 'Chronic cholestatic disease with strictures and dilatation of bile ducts. MRCP shows '
                          '"beading" pattern. Strong association with IBD (especially ulcerative colitis). p-ANCA may '
                          'be positive. Increased risk of cholangiocarcinoma.'
        },
        {
            'condition': 'Pancreatic Head Mass / Cholangiocarcinoma',
            'discussion': 'Painless jaundice in older adults should raise concern for malignancy. CT abdomen with contrast '
                          'or MRCP for evaluation. CA 19-9 may be elevated. ERCP for tissue diagnosis and stenting.'
        },
        {
            'condition': 'Drug-Induced Cholestasis',
            'discussion': 'Many drugs can cause cholestatic injury: amoxicillin-clavulanate, oral contraceptives, '
                          'anabolic steroids, erythromycin, chlorpromazine. Usually resolves after drug withdrawal.'
        },
        {
            'condition': 'Intrahepatic Cholestasis of Pregnancy',
            'discussion': 'Pruritus and elevated bile acids in the third trimester. Risk of fetal complications. '
                          'Treatment: UDCA. Delivery typically recommended at 36-37 weeks.'
        }
    ],
    'mixed': [
        {
            'condition': 'Drug-Induced Liver Injury (Mixed Pattern)',
            'discussion': 'Many drugs produce a mixed hepatocellular-cholestatic pattern. Phenytoin, sulfonamides, '
                          'and amoxicillin-clavulanate are common culprits. Assess with RUCAM score.'
        },
        {
            'condition': 'Granulomatous Hepatitis',
            'discussion': 'Causes include sarcoidosis, tuberculosis, fungal infections, drug reactions. '
                          'Mixed pattern on LFTs. Liver biopsy shows granulomas.'
        },
        {
            'condition': 'Autoimmune Hepatitis with Cholestatic Features',
            'discussion': 'Overlap syndromes (AIH-PBC, AIH-PSC) can present with mixed pattern. Check ANA, ASMA, AMA. '
                          'Liver biopsy often necessary for classification.'
        },
        {
            'condition': 'Infiltrative Liver Disease',
            'discussion': 'Lymphoma, amyloidosis, sarcoidosis can infiltrate the liver causing mixed injury pattern. '
                          'Imaging and liver biopsy for diagnosis.'
        }
    ],
    'isolated_hyperbilirubinemia': [
        {
            'condition': 'Gilbert Syndrome',
            'discussion': 'Most common hereditary hyperbilirubinemia (affects ~5-10% of population). Unconjugated '
                          '(indirect) hyperbilirubinemia with normal liver enzymes and CBC. Bilirubin typically <3 mg/dL. '
                          'Worsens with fasting, stress, illness. Benign condition requiring no treatment.'
        },
        {
            'condition': 'Hemolytic Anemia',
            'discussion': 'Unconjugated hyperbilirubinemia from increased RBC destruction. Check: reticulocyte count, '
                          'LDH (elevated), haptoglobin (low), peripheral smear, direct Coombs test. '
                          'Many causes: autoimmune, microangiopathic, hereditary (spherocytosis, G6PD, sickle cell).'
        },
        {
            'condition': 'Crigler-Najjar Syndrome',
            'discussion': 'Type I: severe unconjugated hyperbilirubinemia (>20 mg/dL), absent UGT1A1 activity. '
                          'Type II: moderate elevation (6-20 mg/dL), responds to phenobarbital. Rare genetic disorder.'
        },
        {
            'condition': 'Dubin-Johnson / Rotor Syndrome',
            'discussion': 'Conjugated (direct) hyperbilirubinemia with normal enzymes. Benign hereditary conditions. '
                          'Dubin-Johnson: black pigmented liver. Rotor: no liver pigmentation. No treatment needed.'
        },
        {
            'condition': 'Ineffective Erythropoiesis',
            'discussion': 'Conditions like megaloblastic anemia, thalassemia, or myelodysplastic syndrome can cause '
                          'unconjugated hyperbilirubinemia from destruction of RBC precursors in the marrow.'
        }
    ]
}


def calculate_r_value(alt: float, alp: float, sex: str = 'male') -> Dict:
    """Calculate the R value for LFT pattern classification."""
    alt_uln = 33 if sex == 'male' else 25
    alp_uln = 120

    if alp_uln == 0 or alp == 0:
        return {'r_value': 0, 'alt_ratio': 0, 'alp_ratio': 0, 'alt_uln': alt_uln, 'alp_uln': alp_uln}

    alt_ratio = alt / alt_uln
    alp_ratio = alp / alp_uln

    if alp_ratio == 0:
        r_value = 0
    else:
        r_value = alt_ratio / alp_ratio

    return {
        'r_value': round(r_value, 2),
        'alt_ratio': round(alt_ratio, 2),
        'alp_ratio': round(alp_ratio, 2),
        'alt_uln': alt_uln,
        'alp_uln': alp_uln,
        'alt': alt,
        'alp': alp
    }


def determine_lft_pattern(r_value: float, alt: float, ast: float, alp: float,
                           total_bili: float, direct_bili: float) -> str:
    """Determine the LFT injury pattern."""
    alt_uln = 40  # generic
    ast_uln = 40
    alp_uln = 120

    # Isolated hyperbilirubinemia: normal enzymes, elevated bilirubin
    if alt <= alt_uln and ast <= ast_uln and alp <= alp_uln and total_bili > 1.0:
        return 'isolated_hyperbilirubinemia'

    if r_value >= 5:
        return 'hepatocellular'
    elif r_value <= 2:
        return 'cholestatic'
    else:
        return 'mixed'


def determine_severity(labs: Dict, sex: str = 'male') -> Dict:
    """Determine the severity of liver injury."""
    alt_uln = 33 if sex == 'male' else 25
    ast_uln = 40 if sex == 'male' else 32
    alp_uln = 120

    elevations = []
    if labs.get('alt', 0) > alt_uln:
        elevations.append(labs['alt'] / alt_uln)
    if labs.get('ast', 0) > ast_uln:
        elevations.append(labs['ast'] / ast_uln)
    if labs.get('alp', 0) > alp_uln:
        elevations.append(labs['alp'] / alp_uln)

    max_elevation = max(elevations) if elevations else 1.0

    if max_elevation < 3:
        return {'grade': 'mild', 'description': '<3x ULN — Often monitored, evaluate for causes', 'max_fold': round(max_elevation, 1)}
    elif max_elevation < 10:
        return {'grade': 'moderate', 'description': '3-10x ULN — Requires systematic workup', 'max_fold': round(max_elevation, 1)}
    else:
        return {'grade': 'severe', 'description': '>10x ULN — Urgent evaluation needed', 'max_fold': round(max_elevation, 1)}


def determine_pathway(clinical: Dict, pattern: str, labs: Dict) -> Dict:
    """Determine the diagnostic pathway based on clinical and lab data."""
    shock = clinical.get('shock', 'no')
    acute_injury = clinical.get('acute_injury', 'no')
    hemolysis_flag = clinical.get('hemolysis', 'no')

    if shock == 'yes' or acute_injury == 'yes':
        return {
            'pathway': 'emergency',
            'emergency': True,
            'content': (
                '<h4>Critical Care Pathway</h4>'
                '<ul>'
                '<li>Provide immediate hemodynamic support (ABC protocol, IV access, fluids)</li>'
                '<li>Obtain blood cultures before antibiotics</li>'
                '<li>Start empiric antibiotics if sepsis suspected</li>'
                '<li>Urgent RUQ imaging (bedside ultrasound if available)</li>'
                '<li>Consider ICU admission</li>'
                '<li>Check acetaminophen level — consider N-acetylcysteine</li>'
                '<li>Hepatology/GI emergent consultation</li>'
                '</ul>'
            )
        }

    if hemolysis_flag == 'yes':
        return {
            'pathway': 'hemolysis',
            'emergency': False,
            'content': (
                '<h4>Hemolysis Evaluation Pathway</h4>'
                '<ul>'
                '<li>CBC with differential and reticulocyte count</li>'
                '<li>Peripheral blood smear review</li>'
                '<li>LDH, haptoglobin, indirect bilirubin levels</li>'
                '<li>Direct Coombs test (DAT)</li>'
                '<li>Consider hematology consultation</li>'
                '</ul>'
            )
        }

    if pattern == 'isolated_hyperbilirubinemia':
        indirect_bili = labs.get('total_bili', 0) - labs.get('direct_bili', 0)
        return {
            'pathway': 'isolated_bilirubin',
            'emergency': False,
            'content': (
                f'<h4>Isolated Hyperbilirubinemia Pathway</h4>'
                f'<p><strong>Key Question:</strong> Is this unconjugated or conjugated?</p>'
                f'<p>Indirect (unconjugated) bilirubin: ~{indirect_bili:.1f} mg/dL</p>'
                f'<ul>'
                f'<li>If predominantly indirect: Consider Gilbert syndrome (most common), hemolysis</li>'
                f'<li>If predominantly direct: Consider Dubin-Johnson syndrome, Rotor syndrome</li>'
                f'<li>Review medication history</li>'
                f'<li>Check CBC with reticulocyte count if hemolysis suspected</li>'
                f'</ul>'
            )
        }

    if pattern == 'cholestatic':
        return {
            'pathway': 'cholestatic',
            'emergency': False,
            'content': (
                '<h4>Cholestatic Injury Pathway (R ≤ 2)</h4>'
                '<p><strong>First step:</strong> RUQ Ultrasound</p>'
                '<ul>'
                '<li>If dilated ducts → Extrahepatic obstruction → MRCP/ERCP</li>'
                '<li>If normal ducts → Intrahepatic cholestasis</li>'
                '<li>&nbsp;&nbsp;→ Check AMA (for PBC), p-ANCA (for PSC)</li>'
                '<li>&nbsp;&nbsp;→ Review medications</li>'
                '<li>&nbsp;&nbsp;→ Consider MRCP if PSC suspected</li>'
                '<li>Check GGT to confirm hepatic origin of elevated ALP</li>'
                '</ul>'
            )
        }

    if pattern == 'hepatocellular':
        return {
            'pathway': 'hepatocellular',
            'emergency': False,
            'content': (
                '<h4>Hepatocellular Injury Pathway (R ≥ 5)</h4>'
                '<ul>'
                '<li>Viral hepatitis serologies: HBsAg, anti-HBc IgM, anti-HCV, anti-HAV IgM</li>'
                '<li>Acetaminophen level (if acute, ALT >1000)</li>'
                '<li>Alcohol history and AST/ALT ratio assessment</li>'
                '<li>Autoimmune markers: ANA, ASMA, IgG</li>'
                '<li>Iron studies: ferritin, transferrin saturation</li>'
                '<li>Ceruloplasmin (if age <40)</li>'
                '<li>RUQ ultrasound for hepatic steatosis, masses</li>'
                '<li>Medication and supplement review</li>'
                '</ul>'
            )
        }

    if pattern == 'mixed':
        return {
            'pathway': 'mixed',
            'emergency': False,
            'content': (
                '<h4>Mixed Pattern Pathway (R 2-5)</h4>'
                '<ul>'
                '<li>Complete viral hepatitis panel (A, B, C, E)</li>'
                '<li>Imaging: RUQ ultrasound, consider MRCP</li>'
                '<li>Autoimmune markers: ANA, ASMA, AMA, IgG, IgM</li>'
                '<li>Drug-induced liver injury assessment (RUCAM)</li>'
                '<li>Consider overlap syndromes (AIH-PBC, AIH-PSC)</li>'
                '<li>Liver biopsy may be needed for definitive diagnosis</li>'
                '</ul>'
            )
        }

    return {
        'pathway': 'further_evaluation',
        'emergency': False,
        'content': (
            '<h4>Further Evaluation Pathway</h4>'
            '<ul>'
            '<li>Repeat LFTs in 1-4 weeks if mild elevation and asymptomatic</li>'
            '<li>Review lifestyle factors: alcohol, weight, medications</li>'
            '<li>Consider non-invasive fibrosis assessment if persistent</li>'
            '<li>Hepatology referral if unexplained persistent abnormalities</li>'
            '</ul>'
        )
    }


def get_abnormalities(labs: Dict, sex: str = 'male') -> Dict:
    """Determine which LFT parameters are abnormal."""
    alt_uln = 33 if sex == 'male' else 25
    ast_uln = 40 if sex == 'male' else 32

    return {
        'alt': labs.get('alt', 0) > alt_uln,
        'ast': labs.get('ast', 0) > ast_uln,
        'alp': labs.get('alp', 0) > 120,
        'total_bili': labs.get('total_bili', 0) > 1.0,
        'direct_bili': labs.get('direct_bili', 0) > 0.3,
        'albumin': 0 < labs.get('albumin', 0) < 3.3,
        'pt': labs.get('pt', 0) > 13 and labs.get('pt', 0) > 0,
        'inr': labs.get('inr', 0) > 1.1 and labs.get('inr', 0) > 0,
    }


def build_severity_table(labs: Dict, abnormalities: Dict, sex: str = 'male') -> List[Dict]:
    """Build severity assessment table rows."""
    alt_uln = 33 if sex == 'male' else 25
    ast_uln = 40 if sex == 'male' else 32

    rows = []
    params = [
        ('ALT', labs.get('alt', 0), alt_uln, abnormalities.get('alt', False)),
        ('AST', labs.get('ast', 0), ast_uln, abnormalities.get('ast', False)),
        ('ALP', labs.get('alp', 0), 120, abnormalities.get('alp', False)),
        ('Total Bilirubin', labs.get('total_bili', 0), 1.0, abnormalities.get('total_bili', False)),
        ('Direct Bilirubin', labs.get('direct_bili', 0), 0.3, abnormalities.get('direct_bili', False)),
    ]

    for name, value, uln, is_abnormal in params:
        fold = round(value / uln, 1) if uln > 0 and value > 0 else 0
        rows.append({
            'Parameter': name,
            'Value': value,
            'Status': '↑ ELEVATED' if is_abnormal else 'Normal',
            'Fold ULN': f'{fold}x' if is_abnormal else '-'
        })

    return rows


def assess_synthetic_function(labs: Dict) -> Dict:
    """Assess liver synthetic function."""
    result = {}
    impaired = False

    albumin = labs.get('albumin', 0)
    pt = labs.get('pt', 0)
    inr = labs.get('inr', 0)

    if albumin > 0:
        if albumin < 3.3:
            result['Albumin'] = f'{albumin} g/dL — LOW (suggests chronic disease or significant hepatic impairment)'
            impaired = True
        else:
            result['Albumin'] = f'{albumin} g/dL — Normal'
    else:
        result['Albumin'] = 'Not provided'

    if pt > 0:
        if pt > 13:
            result['PT'] = f'{pt} sec — PROLONGED'
            impaired = True
        else:
            result['PT'] = f'{pt} sec — Normal'
    else:
        result['PT'] = 'Not provided'

    if inr > 0:
        if inr > 1.1:
            result['INR'] = f'{inr} — ELEVATED (impaired synthesis)'
            impaired = True
        else:
            result['INR'] = f'{inr} — Normal'
    else:
        result['INR'] = 'Not provided'

    return result, impaired


def get_ast_alt_interpretation(ratio: float) -> str:
    """Interpret the AST/ALT ratio."""
    if ratio > 2:
        return f'{ratio:.2f}:1 — Suggestive of alcoholic liver disease (AST/ALT >2:1 is characteristic)'
    elif ratio > 1:
        return f'{ratio:.2f}:1 — Possible alcoholic component or cirrhosis (AST > ALT can occur in advanced fibrosis)'
    else:
        return f'{ratio:.2f}:1 — Typical of viral hepatitis, NAFLD, or other non-alcoholic hepatocellular injury'


def get_lft_differential_diagnosis(pattern: str) -> List[Dict]:
    """Get differential diagnosis list for a given LFT pattern."""
    return LFT_DIFFERENTIALS.get(pattern, [])


def generate_lft_recommendations(pathway_info: Dict, labs: Dict, clinical: Dict, pattern: str) -> List[Dict]:
    """Generate clinical recommendations based on the analysis."""
    recs = []
    is_chronic = clinical.get('reason', '') in ('known_disease', 'routine')

    if pathway_info.get('emergency'):
        recs.append({
            'title': 'Immediate Stabilization',
            'description': 'ABC protocol, IV access, fluid resuscitation. Do NOT delay treatment for diagnostics.'
        })
        recs.append({
            'title': 'Urgent Diagnostics',
            'description': 'Blood cultures, CBC, CMP, coagulation profile, type & screen, acetaminophen level, '
                           'toxicology screen. Bedside RUQ ultrasound.'
        })
        recs.append({
            'title': 'Empiric Therapy',
            'description': 'Broad-spectrum antibiotics if sepsis suspected. N-acetylcysteine if acetaminophen '
                           'toxicity possible (consider even if level unknown).'
        })
        recs.append({
            'title': 'Specialist Consultation',
            'description': 'Urgent hepatology/GI consultation. Consider transfer to transplant center if acute liver failure.'
        })
    else:
        recs.append({
            'title': 'Confirm Abnormalities',
            'description': 'Repeat LFTs in 1-2 weeks to confirm persistence if new finding and patient is asymptomatic.'
        })

        if pattern == 'hepatocellular':
            recs.append({
                'title': 'Hepatocellular Workup',
                'description': 'HBsAg, anti-HBc IgM, anti-HCV, anti-HAV IgM. ANA, ASMA, IgG (autoimmune). '
                               'Ferritin, TIBC (hemochromatosis). Ceruloplasmin if age <40 (Wilson). '
                               'Acetaminophen level if acute and ALT >1000.'
            })
            recs.append({
                'title': 'Lifestyle Assessment',
                'description': 'Detailed alcohol history (AUDIT questionnaire). Medication and supplement review. '
                               'BMI, waist circumference, metabolic syndrome evaluation. Consider FIB-4 score.'
            })
        elif pattern == 'cholestatic':
            recs.append({
                'title': 'Imaging Priority',
                'description': 'RUQ ultrasound with Doppler as first-line. If ducts dilated → MRCP or ERCP. '
                               'If normal ducts → AMA for PBC, p-ANCA for PSC, consider MRCP.'
            })
            recs.append({
                'title': 'Confirm Hepatic Origin',
                'description': 'GGT or 5\'-nucleotidase to confirm elevated ALP is of hepatic origin '
                               '(vs. bone, placental, intestinal).'
            })
        elif pattern == 'mixed':
            recs.append({
                'title': 'Comprehensive Evaluation',
                'description': 'Full viral panel (HAV, HBV, HCV, HEV). Autoimmune markers (ANA, ASMA, AMA, IgG, IgM). '
                               'Iron studies, copper studies. Imaging (US + consider MRCP). RUCAM for drug assessment.'
            })
        elif pattern == 'isolated_hyperbilirubinemia':
            recs.append({
                'title': 'Fractionate Bilirubin',
                'description': 'Distinguish conjugated vs. unconjugated. If predominantly unconjugated and <3 mg/dL '
                               'with normal CBC, likely Gilbert syndrome (no treatment needed).'
            })
            recs.append({
                'title': 'Hemolysis Workup (if indicated)',
                'description': 'CBC, reticulocyte count, peripheral smear, LDH, haptoglobin, direct Coombs test.'
            })

        inr = labs.get('inr', 0)
        albumin = labs.get('albumin', 0)
        if (inr > 1.5) or (0 < albumin < 2.5):
            recs.append({
                'title': 'Synthetic Function Concern',
                'description': 'Impaired hepatic synthesis suggests advanced disease. Urgent hepatology referral. '
                               'Evaluate for encephalopathy (asterixis, confusion). Consider MELD score calculation.'
            })

        recs.append({
            'title': 'Follow-up Plan',
            'description': (
                'Continue current management. Monitor every 3-6 months. Consider non-invasive fibrosis '
                'assessment (FibroScan, FIB-4).' if is_chronic else
                'Re-evaluate in 4-6 weeks. If persistent, proceed with full workup per pathway. '
                'If resolved, likely transient insult (viral, drug, etc.).'
            )
        })

    return recs


def generate_lft_educational_content(results: Dict, clinical: Dict) -> str:
    """Generate educational teaching points for LFT analysis."""
    pattern = results.get('pattern', '')
    r_value = results.get('r_value', 0)

    content = []

    # Teaching point 1: Pattern Recognition
    content.append(
        "### 💡 Teaching Point 1: Pattern Recognition\n\n"
        f"The **R value** (ratio of ALT fold-elevation to ALP fold-elevation) helps categorize liver injury:\n"
        f"- **R ≥ 5**: Hepatocellular\n"
        f"- **R 2-5**: Mixed\n"
        f"- **R ≤ 2**: Cholestatic\n\n"
        f"This patient's R value of **{r_value}** indicates a **{pattern.replace('_', ' ')}** pattern.\n"
    )

    # Teaching point 2: Clinical Context
    emergency_status = clinical.get('shock', 'no') == 'yes' or clinical.get('acute_injury', 'no') == 'yes'
    hemolysis_status = clinical.get('hemolysis', 'no') == 'yes'

    if emergency_status:
        context_text = ("This patient has hemodynamic instability or acute liver failure features, making "
                        "this a medical emergency regardless of lab values. Stabilize first, test second.")
    elif hemolysis_status:
        context_text = ("Suspected hemolysis directs us toward a hematologic rather than hepatic evaluation. "
                        "The elevated bilirubin is likely from RBC destruction, not liver disease.")
    else:
        context_text = ("The absence of red flags allows for a systematic outpatient evaluation. "
                        "Follow the pattern-based diagnostic algorithm.")

    content.append(
        "### 💡 Teaching Point 2: Clinical Context Matters\n\n"
        f"{context_text}\n"
    )

    # Teaching point 3: Synthetic vs Biochemical
    content.append(
        "### 💡 Teaching Point 3: Biochemical vs. Functional Tests\n\n"
        "**Biochemical markers** (ALT, AST, ALP, GGT) indicate **injury** — they tell us cells are being damaged.\n\n"
        "**Functional markers** (albumin, PT/INR, bilirubin) indicate **capacity** — they tell us if the liver "
        "can still do its job.\n\n"
        "A patient can have markedly elevated ALT (severe injury) but normal albumin/INR (preserved function), "
        "as in acute viral hepatitis. Conversely, a patient with cirrhosis may have near-normal ALT but severely "
        "impaired synthetic function.\n"
    )

    # Teaching point 4: AST/ALT Ratio
    content.append(
        "### 💡 Teaching Point 4: AST/ALT Ratio (De Ritis Ratio)\n\n"
        "- **AST/ALT > 2:1**: Strongly suggests alcoholic liver disease\n"
        "- **AST/ALT > 1:1**: May indicate cirrhosis of any etiology\n"
        "- **AST/ALT < 1:1**: Typical of NAFLD, viral hepatitis\n\n"
        "This ratio works because ALT has a longer half-life and is more liver-specific, while AST is found "
        "in multiple tissues. In alcoholic hepatitis, mitochondrial damage preferentially releases AST.\n"
    )

    return "\n".join(content)


def analyze_lft(labs: Dict, clinical: Dict) -> Dict:
    """Perform comprehensive LFT analysis. Main entry point."""
    sex = clinical.get('sex', 'male')
    alt = labs.get('alt', 0)
    ast = labs.get('ast', 0)
    alp = labs.get('alp', 0)
    total_bili = labs.get('total_bili', 0)
    direct_bili = labs.get('direct_bili', 0)

    # R value calculation
    r_calc = calculate_r_value(alt, alp, sex)
    r_value = r_calc['r_value']

    # Pattern
    pattern = determine_lft_pattern(r_value, alt, ast, alp, total_bili, direct_bili)

    # Abnormalities
    abnormalities = get_abnormalities(labs, sex)

    # Severity
    severity = determine_severity(labs, sex)

    # Severity table
    severity_table = build_severity_table(labs, abnormalities, sex)

    # Pathway
    pathway_info = determine_pathway(clinical, pattern, labs)

    # Synthetic function
    synthetic, synthetic_impaired = assess_synthetic_function(labs)

    # AST/ALT ratio
    ast_alt_ratio = round(ast / alt, 2) if alt > 0 else 0
    ast_alt_interpretation = get_ast_alt_interpretation(ast_alt_ratio)

    # Differentials
    differentials = get_lft_differential_diagnosis(pattern)

    # Recommendations
    recommendations = generate_lft_recommendations(pathway_info, labs, clinical, pattern)

    # Build results
    results = {
        'r_value': r_value,
        'r_calculation': r_calc,
        'pattern': pattern,
        'abnormalities': abnormalities,
        'severity': severity,
        'severity_table': severity_table,
        'pathway': pathway_info.get('pathway', ''),
        'pathway_content': pathway_info.get('content', ''),
        'emergency': pathway_info.get('emergency', False),
        'synthetic_function': synthetic,
        'synthetic_impaired': synthetic_impaired,
        'ast_alt_ratio': ast_alt_ratio,
        'ast_alt_interpretation': ast_alt_interpretation,
        'differentials': differentials,
        'recommendations': recommendations,
        'labs': labs,
        'clinical': clinical,
    }

    # Educational content
    results['educational_content'] = generate_lft_educational_content(results, clinical)

    return results