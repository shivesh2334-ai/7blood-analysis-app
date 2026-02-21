"""Oncology Markers Analysis Engine"""
from typing import Dict

ONCO_REFERENCE_RANGES = {
    'AFP': {'Default': {'low': 0, 'high': 10, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 50000}},
    'CEA': {'Default': {'low': 0, 'high': 3.0, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 1000}},
    'Onco_LDH': {'Default': {'low': 140, 'high': 280, 'unit': 'IU/L', 'critical_low': 50, 'critical_high': 5000}},
    'Beta2_Microglobulin': {'Default': {'low': 0.8, 'high': 2.4, 'unit': 'mg/L', 'critical_low': 0, 'critical_high': 30}},
    'CA_19_9': {'Default': {'low': 0, 'high': 37, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 50000}},
    'CA_72_4': {'Default': {'low': 0, 'high': 6.9, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 500}},
    'CA_15_3': {'Default': {'low': 0, 'high': 30, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 500}},
    'CA_27_29': {'Default': {'low': 0, 'high': 38, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 500}},
    'CA_125': {'Default': {'low': 0, 'high': 35, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 5000}},
    'HE4': {'Default': {'low': 0, 'high': 140, 'unit': 'pmol/L', 'critical_low': 0, 'critical_high': 2000}},
    'ROMA_Index': {'Default': {'low': 0, 'high': 11.4, 'unit': '%', 'critical_low': 0, 'critical_high': 100}},
    'Total_PSA': {
        'Default': {'low': 0, 'high': 4.0, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 500},
    },
    'Free_PSA': {'Default': {'low': 0, 'high': 100, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 100}},
    'PSA_Ratio': {'Default': {'low': 25, 'high': 100, 'unit': '%', 'critical_low': 0, 'critical_high': 100}},
    'Beta_hCG': {
        'Male': {'low': 0, 'high': 2.0, 'unit': 'mIU/mL', 'critical_low': 0, 'critical_high': 500000},
        'Female': {'low': 0, 'high': 5.0, 'unit': 'mIU/mL', 'critical_low': 0, 'critical_high': 500000},
        'Default': {'low': 0, 'high': 5.0, 'unit': 'mIU/mL', 'critical_low': 0, 'critical_high': 500000},
    },
    'NSE': {'Default': {'low': 0, 'high': 16.3, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 200}},
    'CYFRA_21_1': {'Default': {'low': 0, 'high': 3.3, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 200}},
    'SCC': {'Default': {'low': 0, 'high': 1.5, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 100}},
    'ProGRP': {'Default': {'low': 0, 'high': 68, 'unit': 'pg/mL', 'critical_low': 0, 'critical_high': 5000}},
    'Calcitonin': {
        'Male': {'low': 0, 'high': 8.4, 'unit': 'pg/mL', 'critical_low': 0, 'critical_high': 1000},
        'Female': {'low': 0, 'high': 5.0, 'unit': 'pg/mL', 'critical_low': 0, 'critical_high': 1000},
        'Default': {'low': 0, 'high': 8.4, 'unit': 'pg/mL', 'critical_low': 0, 'critical_high': 1000},
    },
    'Onco_Thyroglobulin': {'Default': {'low': 0, 'high': 55, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 500}},
    'Chromogranin_A': {'Default': {'low': 0, 'high': 100, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 1000}},
    'Ki_67': {'Default': {'low': 0, 'high': 10, 'unit': '%', 'critical_low': 0, 'critical_high': 100}},
}

ONCO_DIFFERENTIALS = {
    'AFP': {
        'high': {'title': 'Elevated AFP', 'differentials': [
            {'condition': 'Hepatocellular Carcinoma', 'discussion': 'AFP >400 ng/mL in cirrhotic patient is highly suggestive. Screening: AFP + US every 6 months in cirrhosis. Sensitivity ~60%.'},
            {'condition': 'Germ Cell Tumors', 'discussion': 'Nonseminomatous germ cell tumors (yolk sac tumor). Also elevated in testicular teratoma. Part of tumor marker panel with beta-hCG and LDH.'},
            {'condition': 'Pregnancy', 'discussion': 'AFP rises during normal pregnancy. Abnormal levels in pregnancy may indicate neural tube defects or chromosomal abnormalities.'},
            {'condition': 'Chronic Liver Disease', 'discussion': 'Mild elevation (<100) can be seen in cirrhosis, chronic hepatitis without HCC.'},
        ]}
    },
    'CEA': {
        'high': {'title': 'Elevated CEA', 'differentials': [
            {'condition': 'Colorectal Cancer', 'discussion': 'Primary use: monitoring treatment response and recurrence. Not for screening. Preop level >5 = worse prognosis. Rising CEA post-resection suggests recurrence.'},
            {'condition': 'Other GI Cancers', 'discussion': 'Pancreatic, gastric, esophageal cancers can elevate CEA.'},
            {'condition': 'Lung Cancer', 'discussion': 'Especially adenocarcinoma. Non-specific.'},
            {'condition': 'Smoking', 'discussion': 'Smokers have higher baseline CEA (up to 5-10 ng/mL). Always interpret in context.'},
            {'condition': 'Benign Conditions', 'discussion': 'IBD, pancreatitis, hypothyroidism, liver disease can mildly elevate CEA.'},
        ]}
    },
    'CA_125': {
        'high': {'title': 'Elevated CA 125', 'differentials': [
            {'condition': 'Epithelial Ovarian Cancer', 'discussion': 'Elevated in ~80% of epithelial ovarian cancers. Better for serous type. Use with HE4 (ROMA index) for risk assessment. Poor screening test due to low specificity.'},
            {'condition': 'Endometriosis', 'discussion': 'Commonly elevated, especially during menstruation. Not useful for diagnosis.'},
            {'condition': 'Other Cancers', 'discussion': 'Endometrial, fallopian tube, peritoneal, breast, lung, pancreatic.'},
            {'condition': 'Benign Conditions', 'discussion': 'Pregnancy, PID, cirrhosis, heart failure, pleural/peritoneal effusions. Any peritoneal inflammation.'},
        ]}
    },
    'Total_PSA': {
        'high': {'title': 'Elevated PSA', 'differentials': [
            {'condition': 'Prostate Cancer', 'discussion': 'PSA 4-10: ~25% chance of cancer. >10: ~50% chance. PSA velocity >0.75/year and low free/total ratio (<25%) increase suspicion. MRI fusion biopsy for diagnosis.'},
            {'condition': 'BPH', 'discussion': 'Most common cause of PSA elevation. BPH contributes ~0.3 ng/mL per gram of tissue. Free/total ratio usually >25%.'},
            {'condition': 'Prostatitis', 'discussion': 'Acute prostatitis can dramatically elevate PSA. Wait 6-8 weeks after treatment to recheck.'},
            {'condition': 'Recent Procedures', 'discussion': 'DRE causes minimal rise. Prostate biopsy, TURP, catheterization can significantly elevate PSA. Wait 6 weeks.'},
        ]}
    },
    'Beta_hCG': {
        'high': {'title': 'Elevated Beta-hCG', 'differentials': [
            {'condition': 'Pregnancy', 'discussion': 'Always the first consideration in women of reproductive age. Doubles every 48 hours in early normal pregnancy.'},
            {'condition': 'Germ Cell Tumors', 'discussion': 'Seminoma, choriocarcinoma, embryonal carcinoma. Testicular or extragonadal. Part of GCT staging with AFP and LDH.'},
            {'condition': 'Gestational Trophoblastic Disease', 'discussion': 'Hydatidiform mole, choriocarcinoma. Very high levels (>100,000). US shows snowstorm pattern.'},
        ]}
    },
    'Calcitonin': {
        'high': {'title': 'Elevated Calcitonin', 'differentials': [
            {'condition': 'Medullary Thyroid Cancer (MTC)', 'discussion': 'Calcitonin is the primary tumor marker. >100 pg/mL highly suspicious for MTC. Screen in MEN2 families. Pentagastrin stimulation test for borderline values.'},
            {'condition': 'C-Cell Hyperplasia', 'discussion': 'Precursor to MTC in MEN2. Mildly elevated calcitonin.'},
            {'condition': 'Other Cancers', 'discussion': 'Small cell lung cancer, carcinoid, VIPoma can produce calcitonin.'},
        ]}
    },
    'Ki_67': {
        'high': {'title': 'Elevated Ki-67 Proliferation Index', 'differentials': [
            {'condition': 'Aggressive Malignancy', 'discussion': 'Ki-67 reflects proliferative activity. Breast: <14% low, >30% high. Neuroendocrine tumors: G1 <3%, G2 3-20%, G3 >20%. Lymphoma grading. Higher Ki-67 = more aggressive but often more chemo-responsive.'},
        ]}
    },
    'Chromogranin_A': {
        'high': {'title': 'Elevated Chromogranin A', 'differentials': [
            {'condition': 'Neuroendocrine Tumors', 'discussion': 'Most sensitive marker for NETs. Correlates with tumor burden. Also elevated in carcinoid, pheochromocytoma, medullary thyroid cancer.'},
            {'condition': 'PPI Use', 'discussion': 'Proton pump inhibitors cause gastric ECL cell hyperplasia, raising CgA. MUST stop PPI 2 weeks before testing. Very common false positive.'},
            {'condition': 'Renal Impairment', 'discussion': 'Reduced clearance causes elevated levels. Interpret with caution in CKD.'},
        ]}
    }
}


def _get_ref(p, sex='Default'):
    if p in ONCO_REFERENCE_RANGES:
        refs = ONCO_REFERENCE_RANGES[p]
        return refs.get(sex, refs.get('Default', {}))
    return {}

def _classify(p, v, sex='Default'):
    ref = _get_ref(p, sex)
    if not ref: return {'status': 'unknown', 'message': str(v), 'color': 'gray'}
    r = {'value': v, 'unit': ref.get('unit',''), 'low': ref.get('low'), 'high': ref.get('high'),
         'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if v > ref.get('critical_high', float('inf')): r.update({'status': 'critical_high', 'message': f'CRITICAL: {v}', 'color': 'red'})
    elif v > ref.get('high', float('inf')): r.update({'status': 'high', 'message': f'ELEVATED: {v} (Ref: <{ref["high"]})', 'color': 'orange'})
    elif v < ref.get('low', 0) and ref.get('low', 0) > 0: r.update({'status': 'low', 'message': f'LOW: {v} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    else: r.update({'status': 'normal', 'message': f'NORMAL: {v} (Ref: <{ref["high"]})', 'color': 'green'})
    return r


def analyze_oncology(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values, calc = {}, [], [], {}

    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None or not isinstance(val, (int, float)): continue
        c = _classify(pname, val, sex)
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = c['status'].replace('critical_', '')
            if pname in ONCO_DIFFERENTIALS and d in ONCO_DIFFERENTIALS[pname]:
                diff = ONCO_DIFFERENTIALS[pname][d]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c['status']:
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        results[pname] = {'value': val, 'unit': pdata.get('unit',''), 'classification': c, 'differential': diff}

    # PSA ratio calculation
    total_psa = parameters.get('Total_PSA', {}).get('value')
    free_psa = parameters.get('Free_PSA', {}).get('value')
    if total_psa and free_psa and total_psa > 0:
        ratio = round((free_psa / total_psa) * 100, 1)
        calc['Free/Total PSA Ratio'] = {
            'value': f'{ratio}%', 'formula': '(Free PSA / Total PSA) × 100',
            'interpretation': f'{ratio}% — {"Low ratio (<25%): increased cancer risk" if ratio < 25 else "Higher ratio: likely BPH"}',
            'note': '<10% high risk, 10-25% intermediate, >25% likely benign'
        }

    # GCT panel
    afp = parameters.get('AFP', {}).get('value')
    bhcg = parameters.get('Beta_hCG', {}).get('value')
    ldh = parameters.get('Onco_LDH', {}).get('value')
    if afp and bhcg and ldh:
        calc['GCT Risk Classification'] = {
            'value': 'See interpretation', 'formula': 'AFP + Beta-hCG + LDH (IGCCCG staging)',
            'interpretation': 'Good prognosis: AFP <1000, hCG <5000, LDH <1.5x ULN. Intermediate: any between. Poor: AFP >10000 or hCG >50000 or LDH >10x ULN.',
            'note': 'IGCCCG classification for nonseminomatous germ cell tumors'
        }

    patterns = []
    if afp and isinstance(afp, (int,float)) and afp > 400:
        patterns.append('**Markedly Elevated AFP**: Consider hepatocellular carcinoma (in cirrhosis) or germ cell tumor.')
    if total_psa and isinstance(total_psa, (int,float)) and total_psa > 10:
        patterns.append(f'**PSA >10**: ~50% probability of prostate cancer. Recommend MRI and biopsy.')

    edu = """### 🎓 Oncology Markers Learning Points

**1. Tumor Markers Are NOT Screening Tests** (with few exceptions): Most tumor markers lack sensitivity and specificity for screening. Exceptions: PSA (controversial), AFP in cirrhosis surveillance, calcitonin in MEN2 families.

**2. Primary Use is Monitoring**: Tumor markers are most valuable for monitoring treatment response and detecting recurrence. A rising trend is more informative than a single value.

**3. False Positives Are Common**: CEA elevated in smoking. CA 125 in menstruation/endometriosis. PSA in BPH/prostatitis. Chromogranin A with PPI use. ALWAYS consider benign causes.

**4. PSA Interpretation**: PSA 4-10 is the "gray zone." Use free/total ratio, PSA density, PSA velocity, and MRI to improve specificity. Shared decision-making for screening (USPSTF).

**5. Ki-67 is Context-Dependent**: Interpretation varies by tumor type. In breast cancer: <14% luminal A, >30% aggressive. In NETs: defines grade (G1 <3%, G2 3-20%, G3 >20%). In lymphoma: helps distinguish indolent from aggressive.

**6. Two-Marker Strategy**: AFP + US for HCC screening. CA 125 + HE4 (ROMA) for ovarian cancer risk. AFP + hCG for germ cell tumors. Using combinations improves diagnostic accuracy.
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': calc,
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': '\n\n'.join(patterns),
        'educational_content': edu, 'recommendations': []
    }
