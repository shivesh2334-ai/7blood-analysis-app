"""Blood Sugar / HbA1c Analysis Engine"""
from typing import Dict

SUGAR_REFERENCE_RANGES = {
    'Fasting_Glucose': {'Default': {'low': 70, 'high': 100, 'unit': 'mg/dL', 'critical_low': 40, 'critical_high': 500}},
    'Random_Glucose': {'Default': {'low': 70, 'high': 140, 'unit': 'mg/dL', 'critical_low': 40, 'critical_high': 600}},
    'PP_Glucose': {'Default': {'low': 70, 'high': 140, 'unit': 'mg/dL', 'critical_low': 40, 'critical_high': 500}},
    'HbA1c': {'Default': {'low': 4.0, 'high': 5.6, 'unit': '%', 'critical_low': 3.0, 'critical_high': 15.0}},
    'eAG': {'Default': {'low': 70, 'high': 114, 'unit': 'mg/dL', 'critical_low': 50, 'critical_high': 400}},
    'Insulin': {'Default': {'low': 2.6, 'high': 24.9, 'unit': 'µIU/mL', 'critical_low': 0, 'critical_high': 200}},
    'C_Peptide': {'Default': {'low': 0.8, 'high': 3.1, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 20}},
    'HOMA_IR': {'Default': {'low': 0, 'high': 2.5, 'unit': '', 'critical_low': 0, 'critical_high': 25}},
}

SUGAR_DIFFERENTIALS = {
    'Fasting_Glucose': {
        'high': {'title': 'Elevated Fasting Glucose', 'differentials': [
            {'condition': 'Diabetes Mellitus', 'discussion': 'FBG ≥126 mg/dL on two occasions = diabetes. Type 2 most common (>90%). Check HbA1c for confirmation.'},
            {'condition': 'Impaired Fasting Glucose (Prediabetes)', 'discussion': 'FBG 100-125 mg/dL. 5-10% annual conversion to diabetes. Lifestyle intervention reduces risk by 58%.'},
            {'condition': 'Stress Hyperglycemia', 'discussion': 'Acute illness, surgery, trauma, corticosteroids cause transient elevation. Repeat after recovery.'},
            {'condition': 'Cushing Syndrome', 'discussion': 'Cortisol excess causes insulin resistance. Check 24-hour urine cortisol, overnight dexamethasone suppression.'},
            {'condition': 'Medications', 'discussion': 'Corticosteroids, thiazides, atypical antipsychotics, tacrolimus, niacin.'},
        ]},
        'low': {'title': 'Hypoglycemia', 'differentials': [
            {'condition': 'Insulin/Sulfonylurea Excess', 'discussion': 'Most common cause in diabetics. Check insulin, C-peptide, sulfonylurea screen. Whipple triad required.'},
            {'condition': 'Insulinoma', 'discussion': 'Beta-cell tumor. Inappropriately high insulin and C-peptide with low glucose. 72-hour fast for diagnosis.'},
            {'condition': 'Adrenal Insufficiency', 'discussion': 'Cortisol deficiency impairs gluconeogenesis. Check morning cortisol, ACTH stimulation test.'},
            {'condition': 'Liver Failure', 'discussion': 'Impaired gluconeogenesis and glycogenolysis in severe hepatic disease.'},
            {'condition': 'Sepsis', 'discussion': 'Increased glucose utilization and impaired gluconeogenesis.'},
        ]}
    },
    'HbA1c': {
        'high': {'title': 'Elevated HbA1c', 'differentials': [
            {'condition': 'Diabetes Mellitus', 'discussion': 'HbA1c ≥6.5% = diabetes. Reflects average glucose over 2-3 months. Target <7% for most adults (ADA).'},
            {'condition': 'Prediabetes', 'discussion': 'HbA1c 5.7-6.4%. Increased risk of diabetes. Lifestyle modification recommended.'},
            {'condition': 'Falsely Elevated', 'discussion': 'Iron deficiency anemia, asplenia, uremia, hypertriglyceridemia can falsely elevate HbA1c. Consider fructosamine in these cases.'},
        ]},
        'low': {'title': 'Low HbA1c', 'differentials': [
            {'condition': 'Hemolytic Anemia', 'discussion': 'Shortened RBC lifespan reduces glycation time, falsely lowering HbA1c.'},
            {'condition': 'Recent Transfusion', 'discussion': 'Donor RBCs dilute glycated hemoglobin.'},
            {'condition': 'Hemoglobin Variants', 'discussion': 'HbS, HbC, HbE can cause falsely low or high HbA1c depending on assay method.'},
        ]}
    },
    'HOMA_IR': {
        'high': {'title': 'Elevated HOMA-IR (Insulin Resistance)', 'differentials': [
            {'condition': 'Metabolic Syndrome', 'discussion': 'Central obesity, dyslipidemia, hypertension, hyperglycemia. HOMA-IR >2.5 suggests insulin resistance.'},
            {'condition': 'PCOS', 'discussion': 'Insulin resistance is a key feature of polycystic ovary syndrome.'},
            {'condition': 'Non-Alcoholic Fatty Liver Disease', 'discussion': 'Strong association with insulin resistance.'},
            {'condition': 'Type 2 Diabetes (early)', 'discussion': 'Insulin resistance precedes hyperglycemia by years.'},
        ]}
    },
}


def _get_ref(p, sex='Default'):
    if p in SUGAR_REFERENCE_RANGES:
        refs = SUGAR_REFERENCE_RANGES[p]
        return refs.get(sex, refs.get('Default', {}))
    return {}


def _classify(p, v, sex='Default'):
    ref = _get_ref(p, sex)
    if not ref: return {'status': 'unknown', 'message': 'No reference', 'color': 'gray'}
    r = {'value': v, 'unit': ref.get('unit',''), 'low': ref.get('low'), 'high': ref.get('high'),
         'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if v < ref.get('critical_low', float('-inf')): r.update({'status': 'critical_low', 'message': f'CRITICAL LOW: {v}', 'color': 'red'})
    elif v > ref.get('critical_high', float('inf')): r.update({'status': 'critical_high', 'message': f'CRITICAL HIGH: {v}', 'color': 'red'})
    elif v < ref.get('low', 0): r.update({'status': 'low', 'message': f'LOW: {v} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    elif v > ref.get('high', float('inf')): r.update({'status': 'high', 'message': f'HIGH: {v} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    else: r.update({'status': 'normal', 'message': f'NORMAL: {v} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'green'})
    return r


def analyze_sugar(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values, calc_indices = {}, [], [], {}
    
    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None or not isinstance(val, (int, float)): continue
        c = _classify(pname, val, sex)
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = c['status'].replace('critical_', '')
            if pname in SUGAR_DIFFERENTIALS and d in SUGAR_DIFFERENTIALS[pname]:
                diff = SUGAR_DIFFERENTIALS[pname][d]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c['status']:
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        results[pname] = {'value': val, 'unit': pdata.get('unit',''), 'classification': c, 'differential': diff}

    # Calculated indices
    hba1c = parameters.get('HbA1c', {}).get('value')
    if hba1c:
        eag = round(28.7 * hba1c - 46.7, 0)
        calc_indices['Calculated eAG'] = {
            'value': eag, 'formula': 'eAG = 28.7 × HbA1c - 46.7',
            'interpretation': f'{eag} mg/dL', 'note': 'Estimated average glucose from HbA1c'
        }

    fasting = parameters.get('Fasting_Glucose', {}).get('value')
    insulin = parameters.get('Insulin', {}).get('value')
    if fasting and insulin:
        homa = round((fasting * insulin) / 405, 2)
        calc_indices['Calculated HOMA-IR'] = {
            'value': homa, 'formula': '(Fasting Glucose × Fasting Insulin) / 405',
            'interpretation': f'{homa} — {"Normal (<2.5)" if homa < 2.5 else "Insulin resistant (≥2.5)"}',
            'note': '<1.0 = insulin sensitive; 1.0-2.5 = normal; >2.5 = insulin resistant'
        }

    # Diabetes classification
    patterns = []
    if fasting:
        if fasting >= 126: patterns.append('**Fasting glucose ≥126**: Diagnostic of diabetes (if confirmed)')
        elif fasting >= 100: patterns.append('**Fasting glucose 100-125**: Impaired fasting glucose (prediabetes)')
    if hba1c:
        if hba1c >= 6.5: patterns.append('**HbA1c ≥6.5%**: Diagnostic of diabetes')
        elif hba1c >= 5.7: patterns.append('**HbA1c 5.7-6.4%**: Prediabetes')

    edu = """### 🎓 Blood Sugar Learning Points

**1. Diagnostic Criteria for Diabetes**: FBG ≥126 mg/dL, HbA1c ≥6.5%, 2-hr OGTT ≥200, or random glucose ≥200 with symptoms. Two abnormal tests needed (can be same sample).

**2. HbA1c Limitations**: Falsely low in hemolysis, transfusion, hemoglobinopathies. Falsely high in iron deficiency, splenectomy. Use fructosamine or CGM when unreliable.

**3. HOMA-IR**: Simple index of insulin resistance. Values >2.5 indicate resistance. Useful for metabolic syndrome assessment and PCOS evaluation. Not standardized across labs.

**4. Hypoglycemia Workup**: Whipple triad required: symptoms + low glucose + symptom resolution with glucose correction. Check insulin, C-peptide, proinsulin, sulfonylurea screen during hypoglycemic episode.

**5. C-Peptide**: Produced 1:1 with insulin. Low C-peptide with high insulin = exogenous insulin. High C-peptide with high insulin = endogenous (insulinoma, sulfonylurea).
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': calc_indices,
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': '\n\n'.join(patterns),
        'educational_content': edu, 'recommendations': []
    }
