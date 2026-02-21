"""Thyroid Function Test (TFT) Analysis Engine"""
from typing import Dict

TFT_REFERENCE_RANGES = {
    'TSH': {'Default': {'low': 0.4, 'high': 4.0, 'unit': 'mIU/L', 'critical_low': 0.01, 'critical_high': 50}},
    'T3': {'Default': {'low': 80, 'high': 200, 'unit': 'ng/dL', 'critical_low': 30, 'critical_high': 500}},
    'T4': {'Default': {'low': 5.0, 'high': 12.0, 'unit': 'µg/dL', 'critical_low': 2.0, 'critical_high': 25}},
    'FT3': {'Default': {'low': 2.3, 'high': 4.2, 'unit': 'pg/mL', 'critical_low': 1.0, 'critical_high': 10}},
    'FT4': {'Default': {'low': 0.8, 'high': 1.8, 'unit': 'ng/dL', 'critical_low': 0.3, 'critical_high': 5.0}},
    'Reverse_T3': {'Default': {'low': 10, 'high': 24, 'unit': 'ng/dL', 'critical_low': 5, 'critical_high': 80}},
    'T3_Uptake': {'Default': {'low': 24, 'high': 37, 'unit': '%', 'critical_low': 15, 'critical_high': 55}},
    'Anti_TPO': {'Default': {'low': 0, 'high': 35, 'unit': 'IU/mL', 'critical_low': 0, 'critical_high': 2000}},
    'Anti_Thyroglobulin': {'Default': {'low': 0, 'high': 40, 'unit': 'IU/mL', 'critical_low': 0, 'critical_high': 2000}},
    'TSH_Receptor_Ab': {'Default': {'low': 0, 'high': 1.75, 'unit': 'IU/L', 'critical_low': 0, 'critical_high': 50}},
    'Thyroglobulin': {'Default': {'low': 0, 'high': 55, 'unit': 'ng/mL', 'critical_low': 0, 'critical_high': 500}},
}

TFT_DIFFERENTIALS = {
    'TSH': {
        'high': {'title': 'Elevated TSH', 'differentials': [
            {'condition': 'Primary Hypothyroidism', 'discussion': 'High TSH + low FT4. Most common: Hashimoto thyroiditis (anti-TPO+). Also post-thyroidectomy, post-radioiodine, iodine deficiency.'},
            {'condition': 'Subclinical Hypothyroidism', 'discussion': 'High TSH + normal FT4. Treat if TSH >10, symptoms present, or anti-TPO positive. Monitor if TSH 4-10.'},
            {'condition': 'Recovery from Non-Thyroidal Illness', 'discussion': 'TSH may transiently rise to 10-20 during recovery phase of sick euthyroid syndrome.'},
            {'condition': 'TSH-Secreting Pituitary Adenoma', 'discussion': 'Rare. High TSH + high FT4. Inappropriate TSH secretion. MRI pituitary.'},
        ]},
        'low': {'title': 'Suppressed TSH', 'differentials': [
            {'condition': 'Graves Disease', 'discussion': 'Most common cause of hyperthyroidism. Diffuse goiter, ophthalmopathy, dermopathy. TSH receptor antibodies positive. Radioiodine uptake elevated and diffuse.'},
            {'condition': 'Toxic Multinodular Goiter', 'discussion': 'Multiple autonomous nodules. More common in elderly. Radioiodine scan shows patchy uptake.'},
            {'condition': 'Thyroiditis (Subacute/Painless)', 'discussion': 'Transient thyrotoxicosis from thyroid destruction. Painful (de Quervain) or painless (postpartum). Low radioiodine uptake distinguishes from Graves.'},
            {'condition': 'Exogenous Thyroid Hormone', 'discussion': 'Overtreatment, factitious use. Low thyroglobulin if exogenous.'},
            {'condition': 'Central Hypothyroidism', 'discussion': 'Pituitary/hypothalamic disease. Low/normal TSH + low FT4. Check other pituitary hormones. MRI pituitary.'},
        ]}
    },
    'Anti_TPO': {
        'high': {'title': 'Elevated Anti-TPO Antibodies', 'differentials': [
            {'condition': 'Hashimoto Thyroiditis', 'discussion': 'Most common cause of hypothyroidism in iodine-sufficient areas. Anti-TPO positive in >90%. Lymphocytic infiltration of thyroid.'},
            {'condition': 'Graves Disease', 'discussion': 'Anti-TPO can be positive in 50-80% of Graves patients. TSH receptor antibody is more specific.'},
            {'condition': 'Other Autoimmune Diseases', 'discussion': 'Can be positive in Type 1 DM, SLE, RA, Sjogren without thyroid disease (5-10% of general population).'},
        ]}
    },
    'TSH_Receptor_Ab': {
        'high': {'title': 'Elevated TSH Receptor Antibodies (TRAb)', 'differentials': [
            {'condition': 'Graves Disease', 'discussion': 'Highly specific (>99%). Stimulating antibodies cause hyperthyroidism. Useful for diagnosis, monitoring, and predicting relapse. Important in pregnancy (neonatal thyrotoxicosis risk).'},
        ]}
    }
}


def _get_ref(p, sex='Default'):
    return TFT_REFERENCE_RANGES.get(p, {}).get(sex, TFT_REFERENCE_RANGES.get(p, {}).get('Default', {}))

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


def analyze_tft(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values = {}, [], []
    
    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None or not isinstance(val, (int, float)): continue
        c = _classify(pname, val, sex)
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = c['status'].replace('critical_', '')
            if pname in TFT_DIFFERENTIALS and d in TFT_DIFFERENTIALS[pname]:
                diff = TFT_DIFFERENTIALS[pname][d]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c['status']:
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        results[pname] = {'value': val, 'unit': pdata.get('unit',''), 'classification': c, 'differential': diff}

    # Pattern recognition
    tsh = parameters.get('TSH', {}).get('value')
    ft4 = parameters.get('FT4', {}).get('value')
    ft3 = parameters.get('FT3', {}).get('value')
    patterns = []
    
    if tsh and ft4:
        if tsh > 4.0 and ft4 < 0.8:
            patterns.append('**Primary Hypothyroidism**: High TSH + Low FT4')
        elif tsh > 4.0 and ft4 >= 0.8 and ft4 <= 1.8:
            patterns.append('**Subclinical Hypothyroidism**: High TSH + Normal FT4')
        elif tsh < 0.4 and ft4 > 1.8:
            patterns.append('**Overt Hyperthyroidism**: Low TSH + High FT4')
        elif tsh < 0.4 and ft4 >= 0.8 and ft4 <= 1.8:
            if ft3 and ft3 > 4.2:
                patterns.append('**T3 Thyrotoxicosis**: Low TSH + Normal FT4 + High FT3')
            else:
                patterns.append('**Subclinical Hyperthyroidism**: Low TSH + Normal FT4')
        elif tsh < 0.4 and ft4 < 0.8:
            patterns.append('**Central Hypothyroidism**: Low TSH + Low FT4 (pituitary/hypothalamic)')
        elif tsh > 4.0 and ft4 > 1.8:
            patterns.append('**TSH-Secreting Adenoma or Thyroid Hormone Resistance**: High TSH + High FT4')

    edu = """### 🎓 Thyroid Function Learning Points

**1. TSH is the Screening Test**: TSH is the most sensitive indicator of thyroid function. Start with TSH; if abnormal, check FT4 (and FT3 if hyperthyroid).

**2. Inverse Log-Linear Relationship**: Small changes in FT4 cause large changes in TSH. A 2-fold change in FT4 causes a 100-fold change in TSH. This is why TSH is more sensitive.

**3. Pattern Recognition**:
- High TSH + Low FT4 = Primary hypothyroidism
- High TSH + Normal FT4 = Subclinical hypothyroidism
- Low TSH + High FT4 = Hyperthyroidism
- Low TSH + Normal FT4 = Subclinical hyperthyroidism or T3 thyrotoxicosis
- Low TSH + Low FT4 = Central hypothyroidism (pituitary)

**4. Antibodies Tell the Etiology**: Anti-TPO → Hashimoto. TRAb → Graves. Anti-Tg → thyroid cancer monitoring.

**5. Sick Euthyroid Syndrome**: Acute illness can cause low T3, low TSH, low FT4. Don't diagnose thyroid disease during acute illness unless clinically obvious.
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': {},
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': '\n\n'.join(patterns),
        'educational_content': edu, 'recommendations': []
    }
