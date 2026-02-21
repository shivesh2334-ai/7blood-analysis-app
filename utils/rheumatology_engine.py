"""Rheumatology Markers Analysis Engine"""
from typing import Dict

RHEUM_REFERENCE_RANGES = {
    'RF': {'Default': {'low': 0, 'high': 14, 'unit': 'IU/mL', 'critical_low': 0, 'critical_high': 1000}},
    'Anti_CCP': {'Default': {'low': 0, 'high': 20, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 500}},
    'Anti_dsDNA': {'Default': {'low': 0, 'high': 25, 'unit': 'IU/mL', 'critical_low': 0, 'critical_high': 1000}},
    'Anti_Smith': {'Default': {'low': 0, 'high': 20, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 500}},
    'Complement_C3': {'Default': {'low': 90, 'high': 180, 'unit': 'mg/dL', 'critical_low': 30, 'critical_high': 300}},
    'Complement_C4': {'Default': {'low': 10, 'high': 40, 'unit': 'mg/dL', 'critical_low': 2, 'critical_high': 80}},
    'Anti_Phospholipid_IgG': {'Default': {'low': 0, 'high': 20, 'unit': 'GPL', 'critical_low': 0, 'critical_high': 200}},
    'Anti_Phospholipid_IgM': {'Default': {'low': 0, 'high': 20, 'unit': 'MPL', 'critical_low': 0, 'critical_high': 200}},
    'Anti_Cardiolipin_IgG': {'Default': {'low': 0, 'high': 20, 'unit': 'GPL', 'critical_low': 0, 'critical_high': 200}},
    'Anti_Cardiolipin_IgM': {'Default': {'low': 0, 'high': 20, 'unit': 'MPL', 'critical_low': 0, 'critical_high': 200}},
    'Beta2_Glycoprotein': {'Default': {'low': 0, 'high': 20, 'unit': 'U/mL', 'critical_low': 0, 'critical_high': 200}},
    'CRP': {'Default': {'low': 0, 'high': 5, 'unit': 'mg/L', 'critical_low': 0, 'critical_high': 500}},
    'hs_CRP': {'Default': {'low': 0, 'high': 1.0, 'unit': 'mg/L', 'critical_low': 0, 'critical_high': 50}},
    'ASO': {'Default': {'low': 0, 'high': 200, 'unit': 'IU/mL', 'critical_low': 0, 'critical_high': 1000}},
}

RHEUM_DIFFERENTIALS = {
    'RF': {
        'high': {'title': 'Elevated Rheumatoid Factor', 'differentials': [
            {'condition': 'Rheumatoid Arthritis', 'discussion': 'RF positive in 70-80% of RA. Higher titers correlate with more severe disease. Seropositive RA has worse prognosis.'},
            {'condition': 'Sjogren Syndrome', 'discussion': 'RF positive in >90%. Dry eyes, dry mouth. Check anti-SSA/SSB.'},
            {'condition': 'Other Autoimmune', 'discussion': 'SLE, scleroderma, mixed connective tissue disease. RF is not specific.'},
            {'condition': 'Infections', 'discussion': 'Hepatitis C (up to 70% RF+), endocarditis, TB, syphilis. Always check HCV.'},
            {'condition': 'Elderly/False Positive', 'discussion': 'Up to 5-10% of healthy elderly are RF positive. Increases with age.'},
        ]}
    },
    'Anti_CCP': {
        'high': {'title': 'Elevated Anti-CCP', 'differentials': [
            {'condition': 'Rheumatoid Arthritis', 'discussion': 'More specific than RF (95% vs 80%). Positive years before symptom onset. Predicts erosive disease. RF+/CCP+ = high probability RA.'},
            {'condition': 'Other Autoimmune', 'discussion': 'Occasionally positive in psoriatic arthritis, SLE, Sjogren. Very rarely false positive.'},
        ]}
    },
    'Anti_dsDNA': {
        'high': {'title': 'Elevated Anti-dsDNA', 'differentials': [
            {'condition': 'Systemic Lupus Erythematosus', 'discussion': 'Highly specific for SLE (>95%). Titers correlate with disease activity, especially lupus nephritis. Monitor serially.'},
            {'condition': 'Drug-Induced Lupus', 'discussion': 'Usually anti-histone antibody positive, not anti-dsDNA. Procainamide, hydralazine, isoniazid.'},
        ]}
    },
    'Complement_C3': {
        'low': {'title': 'Low Complement C3', 'differentials': [
            {'condition': 'Active SLE', 'discussion': 'Complement consumption during active flares. Low C3 and C4. Monitor with anti-dsDNA for disease activity.'},
            {'condition': 'Post-Infectious GN', 'discussion': 'Low C3 with normal C4. Transient. Post-streptococcal most common.'},
            {'condition': 'Membranoproliferative GN', 'discussion': 'Persistent low C3. C3 nephritic factor may be present.'},
            {'condition': 'Genetic Deficiency', 'discussion': 'Rare hereditary complement deficiencies predispose to infections and SLE.'},
        ]}
    },
    'CRP': {
        'high': {'title': 'Elevated CRP', 'differentials': [
            {'condition': 'Infection', 'discussion': 'CRP rises within 6-8 hours of infection, peaks at 48 hours. Bacterial > viral. CRP >100 mg/L strongly suggests bacterial infection.'},
            {'condition': 'Autoimmune Inflammation', 'discussion': 'RA, vasculitis, PMR/GCA, IBD. Notably, SLE often has NORMAL CRP (unless serositis or infection).'},
            {'condition': 'Cardiovascular Risk', 'discussion': 'hs-CRP: <1.0 low risk, 1.0-3.0 average, >3.0 high risk. >10 = acute process (not for CV risk assessment).'},
            {'condition': 'Malignancy', 'discussion': 'Tumor-associated inflammation. Lymphoma, renal cell carcinoma.'},
        ]}
    },
    'ASO': {
        'high': {'title': 'Elevated ASO Titer', 'differentials': [
            {'condition': 'Recent Streptococcal Infection', 'discussion': 'Rises 1-3 weeks after pharyngitis, peaks at 3-5 weeks. Used to diagnose rheumatic fever (Jones criteria) and post-streptococcal GN.'},
            {'condition': 'Rheumatic Fever', 'discussion': 'Elevated ASO is one of the Jones criteria supporting evidence. Major criteria: carditis, arthritis, chorea, erythema marginatum, subcutaneous nodules.'},
        ]}
    }
}

def _get_ref(p, sex='Default'):
    return RHEUM_REFERENCE_RANGES.get(p, {}).get(sex, RHEUM_REFERENCE_RANGES.get(p, {}).get('Default', {}))

def _classify(p, v, sex='Default'):
    ref = _get_ref(p, sex)
    if not ref: return {'status': 'unknown', 'message': str(v), 'color': 'gray'}
    r = {'value': v, 'unit': ref.get('unit',''), 'low': ref.get('low'), 'high': ref.get('high'),
         'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if v > ref.get('critical_high', float('inf')): r.update({'status': 'critical_high', 'message': f'CRITICAL HIGH: {v}', 'color': 'red'})
    elif v > ref.get('high', float('inf')): r.update({'status': 'high', 'message': f'HIGH: {v} (Ref: <{ref["high"]})', 'color': 'orange'})
    elif v < ref.get('low', 0) and ref.get('low', 0) > 0: r.update({'status': 'low', 'message': f'LOW: {v} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    else: r.update({'status': 'normal', 'message': f'NORMAL: {v} (Ref: <{ref["high"]})', 'color': 'green'})
    return r

def _classify_qual(p, v):
    val = str(v).lower().strip()
    positive_terms = ['positive', 'detected', 'reactive', 'yes', '+']
    if any(t in val for t in positive_terms):
        return {'status': 'abnormal', 'message': f'Positive: {v}', 'color': 'orange', 'low': None, 'high': None}
    return {'status': 'normal', 'message': f'Negative: {v}', 'color': 'green', 'low': None, 'high': None}


def analyze_rheumatology(parameters: Dict, sex: str = 'Default') -> Dict:
    results, abnormalities, critical_values = {}, [], []
    qual_params = {'ANA', 'ANA_Pattern', 'Lupus_Anticoagulant', 'HLA_B27'}
    
    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None: continue
        
        if pname in qual_params or isinstance(val, str):
            c = _classify_qual(pname, val)
        elif isinstance(val, (int, float)):
            c = _classify(pname, val, sex)
        else:
            c = {'status': 'unknown', 'message': str(val), 'color': 'gray', 'low': None, 'high': None}
        
        diff = None
        if c['status'] not in ('normal', 'unknown'):
            d = c['status'].replace('critical_', '')
            if d == 'abnormal': d = 'high'
            if pname in RHEUM_DIFFERENTIALS and d in RHEUM_DIFFERENTIALS[pname]:
                diff = RHEUM_DIFFERENTIALS[pname][d]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c.get('status', ''):
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        
        results[pname] = {'value': val, 'unit': pdata.get('unit',''), 'classification': c, 'differential': diff}

    # Pattern recognition
    patterns = []
    rf = parameters.get('RF', {}).get('value')
    ccp = parameters.get('Anti_CCP', {}).get('value')
    if rf and isinstance(rf, (int,float)) and rf > 14 and ccp and isinstance(ccp, (int,float)) and ccp > 20:
        patterns.append('**Seropositive RA Pattern**: RF+ and Anti-CCP+ — high probability of rheumatoid arthritis with erosive disease risk.')
    
    ana = str(parameters.get('ANA', {}).get('value', '')).lower()
    dsdna = parameters.get('Anti_dsDNA', {}).get('value')
    c3 = parameters.get('Complement_C3', {}).get('value')
    c4 = parameters.get('Complement_C4', {}).get('value')
    if ('positive' in ana or '1:' in ana) and dsdna and isinstance(dsdna, (int,float)) and dsdna > 25:
        lupus_features = ['ANA+', 'Anti-dsDNA+']
        if c3 and isinstance(c3, (int,float)) and c3 < 90: lupus_features.append('Low C3')
        if c4 and isinstance(c4, (int,float)) and c4 < 10: lupus_features.append('Low C4')
        patterns.append(f'**SLE Pattern**: {", ".join(lupus_features)} — evaluate for systemic lupus erythematosus.')

    # APS pattern
    acl_g = parameters.get('Anti_Cardiolipin_IgG', {}).get('value', 0)
    acl_m = parameters.get('Anti_Cardiolipin_IgM', {}).get('value', 0)
    b2gp = parameters.get('Beta2_Glycoprotein', {}).get('value', 0)
    la = str(parameters.get('Lupus_Anticoagulant', {}).get('value', '')).lower()
    aps_pos = sum([
        isinstance(acl_g, (int,float)) and acl_g > 20,
        isinstance(acl_m, (int,float)) and acl_m > 20,
        isinstance(b2gp, (int,float)) and b2gp > 20,
        'positive' in la
    ])
    if aps_pos >= 2:
        patterns.append('**Antiphospholipid Syndrome Pattern**: Multiple APS markers positive — evaluate for thrombotic risk.')

    edu = """### 🎓 Rheumatology Markers Learning Points

**1. ANA Interpretation**: ANA is a screening test — positive in 95% of SLE but also in 5-15% of healthy individuals. Titer and pattern matter: homogeneous = SLE/drug-induced; speckled = mixed CTD, Sjogren; nucleolar = scleroderma; centromere = limited scleroderma.

**2. RF vs Anti-CCP**: RF is sensitive but not specific (positive in infections, other autoimmune, elderly). Anti-CCP is highly specific (>95%) for RA and predicts erosive disease. RF+/CCP+ = strong RA diagnosis.

**3. Complement in SLE**: Low C3/C4 = active disease with complement consumption. Rising complement = response to treatment. Normal complement does not exclude SLE.

**4. CRP in Rheumatic Disease**: CRP is elevated in RA, PMR/GCA, vasculitis. Notably, CRP is often NORMAL in active SLE (unless serositis or superimposed infection). This distinguishes SLE flare from infection.

**5. APS Criteria**: Requires at least one clinical (thrombosis or pregnancy morbidity) AND one laboratory criterion (lupus anticoagulant, anticardiolipin, anti-beta2GPI). Lab test must be positive on TWO occasions 12 weeks apart.
"""

    return {
        'parameters': results, 'abnormalities': abnormalities, 'critical_values': critical_values,
        'quality_checks': [], 'calculated_indices': {},
        'total_parameters': len(results), 'abnormal_count': len(abnormalities),
        'critical_count': len(critical_values), 'pattern_summary': '\n\n'.join(patterns),
        'educational_content': edu, 'recommendations': []
    }
