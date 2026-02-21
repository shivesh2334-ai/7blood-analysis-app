"""Urine Routine & Microscopy Analysis Engine"""
from typing import Dict

URINE_REFERENCE_RANGES = {
    'Urine_pH': {'Default': {'low': 4.5, 'high': 8.0, 'unit': '', 'critical_low': 4.0, 'critical_high': 9.0}},
    'Specific_Gravity': {'Default': {'low': 1.005, 'high': 1.030, 'unit': '', 'critical_low': 1.000, 'critical_high': 1.050}},
    'Urine_RBC': {'Default': {'low': 0, 'high': 2, 'unit': '/hpf', 'critical_low': 0, 'critical_high': 100}},
    'Urine_WBC': {'Default': {'low': 0, 'high': 5, 'unit': '/hpf', 'critical_low': 0, 'critical_high': 200}},
    'Urine_Epithelial': {'Default': {'low': 0, 'high': 5, 'unit': '/hpf', 'critical_low': 0, 'critical_high': 100}},
    'Protein_Creatinine_Ratio': {'Default': {'low': 0, 'high': 150, 'unit': 'mg/g', 'critical_low': 0, 'critical_high': 5000}},
    'Albumin_Creatinine_Ratio': {'Default': {'low': 0, 'high': 30, 'unit': 'mg/g', 'critical_low': 0, 'critical_high': 5000}},
    'Microalbumin': {'Default': {'low': 0, 'high': 30, 'unit': 'mg/L', 'critical_low': 0, 'critical_high': 500}},
}

URINE_QUALITATIVE_NORMALS = {
    'Urine_Color': ['pale yellow', 'yellow', 'straw', 'amber'],
    'Urine_Appearance': ['clear', 'slightly hazy'],
    'Urine_Protein': ['negative', 'nil', 'absent', 'trace'],
    'Urine_Glucose': ['negative', 'nil', 'absent'],
    'Urine_Ketones': ['negative', 'nil', 'absent'],
    'Urine_Bilirubin': ['negative', 'nil', 'absent'],
    'Urine_Urobilinogen': ['normal', 'negative', '<1.0', '0.2'],
    'Urine_Blood': ['negative', 'nil', 'absent'],
    'Urine_Nitrite': ['negative', 'nil', 'absent'],
    'Urine_Leukocyte_Esterase': ['negative', 'nil', 'absent'],
    'Urine_Casts': ['none', 'nil', 'absent', 'none seen', 'occasional hyaline'],
    'Urine_Crystals': ['none', 'nil', 'absent', 'none seen'],
    'Urine_Bacteria': ['none', 'nil', 'absent', 'none seen', 'few'],
    'Urine_Yeast': ['none', 'nil', 'absent', 'none seen'],
}

URINE_DIFFERENTIALS = {
    'Urine_Protein': {
        'abnormal': {'title': 'Proteinuria', 'differentials': [
            {'condition': 'Diabetic Nephropathy', 'discussion': 'Most common cause of nephrotic-range proteinuria. Microalbuminuria is earliest sign. Screen annually in diabetics.'},
            {'condition': 'Glomerulonephritis', 'discussion': 'Immune-mediated. IgA nephropathy most common worldwide. Check complement, ANA, ANCA, anti-GBM.'},
            {'condition': 'Orthostatic Proteinuria', 'discussion': 'Benign condition in young adults. Protein present only when upright. Split urine collection for diagnosis.'},
            {'condition': 'Overflow Proteinuria', 'discussion': 'Multiple myeloma (Bence Jones protein), myoglobinuria. Dipstick may be negative (detects albumin, not globulins).'},
        ]}
    },
    'Urine_Blood': {
        'abnormal': {'title': 'Hematuria', 'differentials': [
            {'condition': 'UTI', 'discussion': 'Most common cause. Dysuria, frequency, positive nitrite/leukocyte esterase. Culture for confirmation.'},
            {'condition': 'Nephrolithiasis', 'discussion': 'Renal colic + hematuria. CT KUB for diagnosis. RBC without casts.'},
            {'condition': 'Glomerulonephritis', 'discussion': 'RBC casts = glomerular origin. Dysmorphic RBCs. IgA nephropathy, post-infectious, lupus nephritis.'},
            {'condition': 'Bladder/Renal Cancer', 'discussion': 'Painless gross hematuria in adults >40. Cystoscopy and imaging required. Risk factors: smoking, chemical exposure.'},
            {'condition': 'Contamination/Menstruation', 'discussion': 'Always consider in females. Clean catch technique important.'},
        ]}
    },
    'Urine_Glucose': {
        'abnormal': {'title': 'Glucosuria', 'differentials': [
            {'condition': 'Diabetes Mellitus', 'discussion': 'Glucose spills into urine when blood glucose exceeds renal threshold (~180 mg/dL). Not a screening test for DM.'},
            {'condition': 'Renal Glycosuria', 'discussion': 'Low renal glucose threshold. Benign. Normal blood glucose. Can occur in pregnancy, Fanconi syndrome.'},
            {'condition': 'SGLT2 Inhibitors', 'discussion': 'Mechanism of action causes intentional glucosuria. Expected finding on medication.'},
        ]}
    },
    'Urine_WBC': {
        'high': {'title': 'Pyuria (Elevated Urine WBC)', 'differentials': [
            {'condition': 'Urinary Tract Infection', 'discussion': 'WBC >5/hpf with positive nitrite and/or leukocyte esterase strongly suggests UTI. Culture >100,000 CFU/mL.'},
            {'condition': 'Sterile Pyuria', 'discussion': 'WBCs without bacteria. Consider: TB, interstitial nephritis, nephrolithiasis, contamination, recently treated UTI, STI (chlamydia).'},
            {'condition': 'Interstitial Nephritis', 'discussion': 'Drug-induced (NSAIDs, antibiotics, PPI). WBC casts, eosinophiluria. Urine eosinophil stain (Hansel).'},
        ]}
    }
}


def _classify_qualitative(param, value):
    if not isinstance(value, str):
        return {'status': 'unknown', 'message': str(value), 'color': 'gray'}
    normals = URINE_QUALITATIVE_NORMALS.get(param, [])
    val_lower = value.lower().strip()
    is_normal = any(n in val_lower for n in [n.lower() for n in normals])
    if is_normal:
        return {'status': 'normal', 'message': f'Normal: {value}', 'color': 'green', 'low': None, 'high': None}
    else:
        return {'status': 'abnormal', 'message': f'Abnormal: {value}', 'color': 'orange', 'low': None, 'high': None}


def _classify_quantitative(param, value, sex='Default'):
    ref = URINE_REFERENCE_RANGES.get(param, {}).get('Default', {})
    if not ref: return {'status': 'unknown', 'message': str(value), 'color': 'gray'}
    r = {'value': value, 'unit': ref.get('unit',''), 'low': ref.get('low'), 'high': ref.get('high'),
         'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if value > ref.get('critical_high', float('inf')): r.update({'status': 'critical_high', 'message': f'CRITICAL HIGH: {value}', 'color': 'red'})
    elif value > ref.get('high', float('inf')): r.update({'status': 'high', 'message': f'HIGH: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    elif value < ref.get('low', 0): r.update({'status': 'low', 'message': f'LOW: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    else: r.update({'status': 'normal', 'message': f'NORMAL: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'green'})
    return r


def analyze_urine(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values = {}, [], []
    qualitative_params = set(URINE_QUALITATIVE_NORMALS.keys())
    quantitative_params = set(URINE_REFERENCE_RANGES.keys())
    
    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None: continue
        
        if pname in qualitative_params and isinstance(val, str):
            c = _classify_qualitative(pname, val)
        elif pname in quantitative_params and isinstance(val, (int, float)):
            c = _classify_quantitative(pname, val, sex)
        elif isinstance(val, str):
            c = _classify_qualitative(pname, val)
        elif isinstance(val, (int, float)):
            c = _classify_quantitative(pname, val, sex)
        else:
            c = {'status': 'unknown', 'message': str(val), 'color': 'gray', 'low': None, 'high': None}
        
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = 'abnormal' if c['status'] == 'abnormal' else c['status'].replace('critical_', '')
            if pname in URINE_DIFFERENTIALS:
                if d in URINE_DIFFERENTIALS[pname]:
                    diff = URINE_DIFFERENTIALS[pname][d]
                elif 'abnormal' in URINE_DIFFERENTIALS[pname]:
                    diff = URINE_DIFFERENTIALS[pname]['abnormal']
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c.get('status', ''):
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        
        results[pname] = {'value': val, 'unit': pdata.get('unit',''), 'classification': c, 'differential': diff}

    # UTI pattern check
    patterns = []
    nitrite = str(parameters.get('Urine_Nitrite', {}).get('value', '')).lower()
    le = str(parameters.get('Urine_Leukocyte_Esterase', {}).get('value', '')).lower()
    wbc_val = parameters.get('Urine_WBC', {}).get('value', 0)
    bacteria = str(parameters.get('Urine_Bacteria', {}).get('value', '')).lower()
    
    uti_signs = 0
    if 'positive' in nitrite or '+' in nitrite: uti_signs += 1
    if 'positive' in le or '+' in le: uti_signs += 1
    if isinstance(wbc_val, (int, float)) and wbc_val > 5: uti_signs += 1
    if 'many' in bacteria or 'moderate' in bacteria or '++' in bacteria: uti_signs += 1
    
    if uti_signs >= 2:
        patterns.append('**UTI Pattern**: Multiple findings suggest urinary tract infection. Recommend urine culture.')

    # Proteinuria assessment
    acr = parameters.get('Albumin_Creatinine_Ratio', {}).get('value')
    if acr:
        if acr >= 300: patterns.append('**Macroalbuminuria (ACR ≥300)**: Significant proteinuria. Evaluate for diabetic/glomerular disease.')
        elif acr >= 30: patterns.append('**Microalbuminuria (ACR 30-299)**: Early nephropathy. Optimize BP and glucose control.')

    edu = """### 🎓 Urine Analysis Learning Points

**1. Dipstick vs Microscopy**: Dipstick is a screening tool. False positives/negatives occur. Microscopy provides definitive cellular analysis.

**2. UTI Diagnosis**: Nitrite + leukocyte esterase + pyuria (>5 WBC/hpf) strongly suggests UTI. However, nitrite is negative with some organisms (enterococci, pseudomonas). Gold standard: culture >100,000 CFU/mL.

**3. RBC Casts = Glomerular Disease**: The presence of RBC casts localizes hematuria to the glomerulus. Dysmorphic RBCs also suggest glomerular origin. Non-dysmorphic RBCs suggest lower urinary tract.

**4. Microalbuminuria Screening**: ACR 30-299 mg/g = microalbuminuria. First sign of diabetic nephropathy. Screen all diabetics annually. ACE inhibitor/ARB reduces progression.

**5. Specific Gravity**: Low (<1.005) = dilute (diabetes insipidus, water intoxication). High (>1.030) = concentrated (dehydration, SIADH, contrast dye). Fixed at 1.010 = isosthenuria (renal tubular damage).
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': {},
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': '\n\n'.join(patterns),
        'educational_content': edu, 'recommendations': []
    }
