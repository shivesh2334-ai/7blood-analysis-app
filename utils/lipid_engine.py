"""
Lipid Profile Analysis Engine
Standard + advanced lipid panel with cardiovascular risk assessment.
"""
from typing import Dict

LIPID_REFERENCE_RANGES = {
    'Total_Cholesterol': {'Default': {'low': 0, 'high': 200, 'unit': 'mg/dL', 'critical_low': 0, 'critical_high': 500}},
    'HDL': {
        'Male': {'low': 40, 'high': 60, 'unit': 'mg/dL', 'critical_low': 10, 'critical_high': 120},
        'Female': {'low': 50, 'high': 60, 'unit': 'mg/dL', 'critical_low': 10, 'critical_high': 120},
        'Default': {'low': 40, 'high': 60, 'unit': 'mg/dL', 'critical_low': 10, 'critical_high': 120},
    },
    'LDL': {'Default': {'low': 0, 'high': 100, 'unit': 'mg/dL', 'critical_low': 0, 'critical_high': 500}},
    'VLDL': {'Default': {'low': 2, 'high': 30, 'unit': 'mg/dL', 'critical_low': 0, 'critical_high': 100}},
    'Triglycerides': {'Default': {'low': 0, 'high': 150, 'unit': 'mg/dL', 'critical_low': 0, 'critical_high': 1000}},
    'Non_HDL': {'Default': {'low': 0, 'high': 130, 'unit': 'mg/dL', 'critical_low': 0, 'critical_high': 400}},
    'TC_HDL_Ratio': {'Default': {'low': 0, 'high': 4.5, 'unit': '', 'critical_low': 0, 'critical_high': 15}},
    'LDL_HDL_Ratio': {'Default': {'low': 0, 'high': 3.0, 'unit': '', 'critical_low': 0, 'critical_high': 10}},
    'ApoA1': {'Default': {'low': 120, 'high': 180, 'unit': 'mg/dL', 'critical_low': 50, 'critical_high': 250}},
    'ApoB': {'Default': {'low': 40, 'high': 100, 'unit': 'mg/dL', 'critical_low': 20, 'critical_high': 250}},
    'Lp_a': {'Default': {'low': 0, 'high': 75, 'unit': 'nmol/L', 'critical_low': 0, 'critical_high': 500}},
}

LIPID_DIFFERENTIALS = {
    'Total_Cholesterol': {
        'high': {'title': 'Hypercholesterolemia', 'differentials': [
            {'condition': 'Primary/Familial Hypercholesterolemia', 'discussion': 'Genetic disorder of LDL receptor. FH heterozygous: TC 300-500. FH homozygous: TC >500. Tendon xanthomas, premature ASCVD.'},
            {'condition': 'Dietary/Lifestyle', 'discussion': 'High saturated fat intake, sedentary lifestyle. Most common cause.'},
            {'condition': 'Hypothyroidism', 'discussion': 'Reduced LDL receptor expression. Always check TSH in new hypercholesterolemia.'},
            {'condition': 'Nephrotic Syndrome', 'discussion': 'Hepatic overproduction of lipoproteins in response to albumin loss.'},
            {'condition': 'Medications', 'discussion': 'Corticosteroids, thiazides, retinoids, cyclosporine, protease inhibitors.'},
        ]}
    },
    'Triglycerides': {
        'high': {'title': 'Hypertriglyceridemia', 'differentials': [
            {'condition': 'Metabolic Syndrome/Insulin Resistance', 'discussion': 'Most common cause. Associated with central obesity, low HDL, hyperglycemia, hypertension.'},
            {'condition': 'Diabetes Mellitus', 'discussion': 'Insulin deficiency impairs lipoprotein lipase activity. TG >500 risk of pancreatitis.'},
            {'condition': 'Alcohol Use', 'discussion': 'Alcohol stimulates hepatic VLDL production. Can cause massive hypertriglyceridemia.'},
            {'condition': 'Medications', 'discussion': 'Estrogens, beta-blockers, thiazides, retinoids, atypical antipsychotics.'},
            {'condition': 'Familial Hypertriglyceridemia', 'discussion': 'Genetic disorders of triglyceride metabolism. Type I (LPL deficiency): TG >1000.'},
        ]}
    },
    'HDL': {
        'low': {'title': 'Low HDL-Cholesterol', 'differentials': [
            {'condition': 'Metabolic Syndrome', 'discussion': 'Low HDL is a key component. Associated with insulin resistance, central obesity.'},
            {'condition': 'Smoking', 'discussion': 'Reduces HDL by 5-10 mg/dL. Cessation partially reverses this.'},
            {'condition': 'Sedentary Lifestyle', 'discussion': 'Regular aerobic exercise raises HDL by 5-10%.'},
            {'condition': 'Medications', 'discussion': 'Beta-blockers, anabolic steroids, progestins.'},
        ]}
    },
    'LDL': {
        'high': {'title': 'Elevated LDL-Cholesterol', 'differentials': [
            {'condition': 'Familial Hypercholesterolemia', 'discussion': 'Genetic LDL receptor dysfunction. Dutch Lipid Clinic Network Score for diagnosis. Early statin therapy critical.'},
            {'condition': 'Dietary', 'discussion': 'High saturated fat and cholesterol intake.'},
            {'condition': 'Secondary Causes', 'discussion': 'Hypothyroidism, nephrotic syndrome, obstructive liver disease, anorexia nervosa.'},
        ]}
    },
    'Lp_a': {
        'high': {'title': 'Elevated Lipoprotein(a)', 'differentials': [
            {'condition': 'Genetic (Primary)', 'discussion': 'Lp(a) levels are >90% genetically determined. Independent ASCVD risk factor. >50 mg/dL (>125 nmol/L) = high risk. Not significantly modifiable by lifestyle. PCSK9 inhibitors reduce by ~25%.'},
        ]}
    }
}


def _get_ref(param, sex='Default'):
    if param in LIPID_REFERENCE_RANGES:
        refs = LIPID_REFERENCE_RANGES[param]
        return refs.get(sex, refs.get('Default', {}))
    return {}


def _classify(param, value, sex='Default'):
    ref = _get_ref(param, sex)
    if not ref:
        return {'status': 'unknown', 'message': 'No reference', 'color': 'gray'}
    r = {'value': value, 'unit': ref.get('unit', ''), 'low': ref.get('low'), 'high': ref.get('high'),
         'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if value < ref.get('critical_low', float('-inf')):
        r.update({'status': 'critical_low', 'message': f'CRITICAL LOW: {value}', 'color': 'red'})
    elif value > ref.get('critical_high', float('inf')):
        r.update({'status': 'critical_high', 'message': f'CRITICAL HIGH: {value}', 'color': 'red'})
    elif value > ref.get('high', float('inf')):
        r.update({'status': 'high', 'message': f'HIGH: {value} (Ref: ≤{ref["high"]})', 'color': 'orange'})
    elif value < ref.get('low', 0) and ref.get('low', 0) > 0:
        r.update({'status': 'low', 'message': f'LOW: {value} (Ref: ≥{ref["low"]})', 'color': 'orange'})
    else:
        r.update({'status': 'normal', 'message': f'NORMAL: {value}', 'color': 'green'})
    return r


def analyze_lipid(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values, calc_indices = {}, [], [], {}

    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None or not isinstance(val, (int, float)):
            continue
        c = _classify(pname, val, sex)
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = c['status'].replace('critical_', '')
            if pname in LIPID_DIFFERENTIALS and d in LIPID_DIFFERENTIALS[pname]:
                diff = LIPID_DIFFERENTIALS[pname][d]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c['status']:
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        
        learning = {
            'Total_Cholesterol': 'Desirable <200, Borderline 200-239, High ≥240 mg/dL. Sum of HDL + LDL + VLDL.',
            'LDL': 'Primary target for therapy. Goals vary by risk: <70 very high risk, <100 high risk, <130 moderate, <160 low risk. Friedewald: LDL = TC - HDL - (TG/5) if TG<400.',
            'HDL': 'Protective factor. <40 (men) or <50 (women) is low. >60 is protective. Exercise, moderate alcohol, and niacin raise HDL.',
            'Triglycerides': 'Normal <150, Borderline 150-199, High 200-499, Very High ≥500 (pancreatitis risk). Fasting sample required for accuracy.',
        }.get(pname)
        
        results[pname] = {'value': val, 'unit': pdata.get('unit', c.get('unit', '')),
                          'classification': c, 'differential': diff, 'learning': learning}

    # Calculated indices
    tc = parameters.get('Total_Cholesterol', {}).get('value')
    hdl = parameters.get('HDL', {}).get('value')
    ldl = parameters.get('LDL', {}).get('value')
    tg = parameters.get('Triglycerides', {}).get('value')

    if tc and hdl and hdl > 0:
        ratio = round(tc / hdl, 1)
        calc_indices['TC/HDL Ratio'] = {
            'value': ratio, 'formula': 'TC / HDL',
            'interpretation': f'{ratio} — {"Optimal (<4.5)" if ratio < 4.5 else "Elevated (increased CV risk)"}',
            'note': 'Optimal <4.5 for men, <4.0 for women'
        }

    if tc and hdl:
        non_hdl = round(tc - hdl, 0)
        calc_indices['Non-HDL Cholesterol'] = {
            'value': non_hdl, 'formula': 'TC - HDL',
            'interpretation': f'{non_hdl} mg/dL — {"Optimal (<130)" if non_hdl < 130 else "Elevated (target is LDL goal + 30)"}',
            'note': 'Better predictor than LDL alone, includes all atherogenic particles'
        }

    if tc and hdl and tg and tg < 400:
        calc_ldl = round(tc - hdl - tg / 5, 0)
        calc_indices['Friedewald LDL'] = {
            'value': calc_ldl, 'formula': 'TC - HDL - (TG/5)',
            'interpretation': f'{calc_ldl} mg/dL (calculated; valid if TG <400)',
            'note': 'Compare with directly measured LDL if available'
        }

    if tg and tg >= 500:
        calc_indices['Pancreatitis Risk'] = {
            'value': 'HIGH', 'formula': 'TG ≥500 mg/dL',
            'interpretation': 'Triglycerides ≥500 mg/dL — significant risk of acute pancreatitis!',
            'note': 'Immediate treatment needed: fibrates, dietary restriction, consider insulin if DKA'
        }

    # LDL classification
    ldl_goals = []
    if ldl:
        if ldl < 70: ldl_goals.append('At optimal level for very high-risk patients')
        elif ldl < 100: ldl_goals.append('Optimal for high-risk; above goal for very high-risk')
        elif ldl < 130: ldl_goals.append('Near/above optimal; above goal for most patients with risk factors')
        elif ldl < 160: ldl_goals.append('Borderline high')
        elif ldl < 190: ldl_goals.append('High')
        else: ldl_goals.append('Very high — consider familial hypercholesterolemia screening')

    pattern_summary = '\n\n'.join([
        f'**LDL Assessment**: {"; ".join(ldl_goals)}' if ldl_goals else '',
        f'**Triglyceride Assessment**: {"Normal" if not tg or tg < 150 else "Borderline (150-199)" if tg < 200 else "High (200-499)" if tg < 500 else "VERY HIGH (≥500) — PANCREATITIS RISK"}' if tg else '',
    ])

    edu = """### 🎓 Lipid Profile Learning Points

**1. LDL is the Primary Target**: ACC/AHA guidelines focus on statin intensity based on 10-year ASCVD risk rather than specific LDL targets, though LDL goals are still used clinically.

**2. Non-HDL is Often Better than LDL**: Non-HDL cholesterol (TC minus HDL) captures all atherogenic particles including VLDL and IDL. It's the secondary target when TG is elevated.

**3. Friedewald Equation Limitations**: LDL = TC - HDL - TG/5 is inaccurate when TG >400 or in non-fasting samples. Martin-Hopkins equation is more accurate at low LDL and high TG.

**4. Lp(a) is Genetically Determined**: Levels >50 mg/dL (>125 nmol/L) are an independent risk factor for ASCVD. Screen once in lifetime. Not significantly modifiable by lifestyle. PCSK9 inhibitors reduce ~25%.

**5. Triglycerides and Pancreatitis**: TG ≥500 carries pancreatitis risk. Immediate treatment: dietary fat restriction, fibrates. TG >1000: very high risk — consider LPL deficiency.
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': calc_indices,
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': pattern_summary,
        'educational_content': edu, 'recommendations': []
    }
