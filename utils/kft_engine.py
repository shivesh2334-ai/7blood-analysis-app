"""
Kidney Function Test (KFT) Analysis Engine
Renal markers + Electrolytes with comprehensive differential diagnosis.
"""
from typing import Dict, List, Optional

KFT_REFERENCE_RANGES = {
    'Creatinine': {
        'Male': {'low': 0.7, 'high': 1.3, 'unit': 'mg/dL', 'critical_low': 0.3, 'critical_high': 10.0},
        'Female': {'low': 0.6, 'high': 1.1, 'unit': 'mg/dL', 'critical_low': 0.3, 'critical_high': 10.0},
        'Default': {'low': 0.6, 'high': 1.3, 'unit': 'mg/dL', 'critical_low': 0.3, 'critical_high': 10.0},
    },
    'BUN': {'Default': {'low': 7, 'high': 20, 'unit': 'mg/dL', 'critical_low': 2, 'critical_high': 100}},
    'Urea': {'Default': {'low': 15, 'high': 45, 'unit': 'mg/dL', 'critical_low': 5, 'critical_high': 200}},
    'Uric_Acid': {
        'Male': {'low': 3.5, 'high': 7.2, 'unit': 'mg/dL', 'critical_low': 1.0, 'critical_high': 15.0},
        'Female': {'low': 2.5, 'high': 6.0, 'unit': 'mg/dL', 'critical_low': 1.0, 'critical_high': 15.0},
        'Default': {'low': 2.5, 'high': 7.2, 'unit': 'mg/dL', 'critical_low': 1.0, 'critical_high': 15.0},
    },
    'eGFR': {'Default': {'low': 90, 'high': 120, 'unit': 'mL/min/1.73m²', 'critical_low': 15, 'critical_high': 200}},
    'Cystatin_C': {'Default': {'low': 0.55, 'high': 1.15, 'unit': 'mg/L', 'critical_low': 0.2, 'critical_high': 5.0}},
    'Sodium': {'Default': {'low': 136, 'high': 145, 'unit': 'mEq/L', 'critical_low': 120, 'critical_high': 160}},
    'Potassium': {'Default': {'low': 3.5, 'high': 5.0, 'unit': 'mEq/L', 'critical_low': 2.5, 'critical_high': 6.5}},
    'Chloride': {'Default': {'low': 98, 'high': 106, 'unit': 'mEq/L', 'critical_low': 80, 'critical_high': 120}},
    'Bicarbonate': {'Default': {'low': 22, 'high': 29, 'unit': 'mEq/L', 'critical_low': 10, 'critical_high': 40}},
    'Calcium': {'Default': {'low': 8.5, 'high': 10.5, 'unit': 'mg/dL', 'critical_low': 6.0, 'critical_high': 14.0}},
    'Phosphorus': {'Default': {'low': 2.5, 'high': 4.5, 'unit': 'mg/dL', 'critical_low': 1.0, 'critical_high': 8.0}},
    'Magnesium': {'Default': {'low': 1.7, 'high': 2.2, 'unit': 'mg/dL', 'critical_low': 1.0, 'critical_high': 4.0}},
}

KFT_DIFFERENTIALS = {
    'Creatinine': {
        'high': {
            'title': 'Elevated Creatinine',
            'differentials': [
                {'condition': 'Acute Kidney Injury (AKI)', 'discussion': 'Rapid rise in creatinine over hours-days. Prerenal (dehydration, heart failure), intrinsic (ATN, glomerulonephritis), or postrenal (obstruction). Check urine output, fractional excretion of sodium.'},
                {'condition': 'Chronic Kidney Disease (CKD)', 'discussion': 'Gradual elevation with reduced eGFR. Stages 1-5 based on GFR. Most common causes: diabetes, hypertension. Check urine albumin/creatinine ratio, renal ultrasound.'},
                {'condition': 'Dehydration/Prerenal', 'discussion': 'BUN/Creatinine ratio >20:1 suggests prerenal etiology. Responds to IV fluids.'},
                {'condition': 'Medications', 'discussion': 'NSAIDs, ACE inhibitors, ARBs, aminoglycosides, contrast dye can elevate creatinine. Some drugs (trimethoprim, cimetidine) inhibit tubular secretion of creatinine without true GFR reduction.'},
                {'condition': 'Rhabdomyolysis', 'discussion': 'Massive muscle breakdown releases myoglobin. Check CK (markedly elevated), urine myoglobin. Dark urine. Risk of AKI.'},
            ]
        },
    },
    'BUN': {
        'high': {
            'title': 'Elevated BUN',
            'differentials': [
                {'condition': 'Prerenal Azotemia', 'discussion': 'BUN rises disproportionately to creatinine (ratio >20:1). Dehydration, CHF, GI bleeding (protein load).'},
                {'condition': 'GI Bleeding', 'discussion': 'Blood in GI tract is digested as protein, increasing BUN. BUN/Cr ratio often >30:1.'},
                {'condition': 'High Protein Diet/Catabolism', 'discussion': 'Increased protein intake, burns, sepsis, corticosteroids increase urea production.'},
                {'condition': 'Renal Failure', 'discussion': 'Both BUN and creatinine rise proportionally in intrinsic renal disease.'},
            ]
        },
    },
    'Sodium': {
        'low': {
            'title': 'Hyponatremia (<136 mEq/L)',
            'differentials': [
                {'condition': 'SIADH', 'discussion': 'Euvolemic hyponatremia. Common causes: CNS disease, pulmonary disease, medications (SSRIs, carbamazepine). Check urine osmolality (>100), urine sodium (>40).'},
                {'condition': 'Heart Failure/Cirrhosis', 'discussion': 'Hypervolemic hyponatremia. Dilutional due to fluid retention despite total body sodium excess.'},
                {'condition': 'Diuretic Use', 'discussion': 'Thiazides are the most common medication cause. Hypovolemic hyponatremia.'},
                {'condition': 'Hypothyroidism/Adrenal Insufficiency', 'discussion': 'Endocrine causes. Check TSH, morning cortisol.'},
                {'condition': 'Psychogenic Polydipsia', 'discussion': 'Excessive water intake overwhelming renal diluting capacity.'},
            ]
        },
        'high': {
            'title': 'Hypernatremia (>145 mEq/L)',
            'differentials': [
                {'condition': 'Dehydration/Water Loss', 'discussion': 'Most common cause. Inadequate water intake, insensible losses, diarrhea. Free water deficit calculation needed.'},
                {'condition': 'Diabetes Insipidus', 'discussion': 'Central (lack of ADH) or nephrogenic (resistance to ADH). Large volumes of dilute urine. Water deprivation test for diagnosis.'},
                {'condition': 'Osmotic Diuresis', 'discussion': 'Hyperglycemia, mannitol, urea cause water loss exceeding sodium loss.'},
            ]
        }
    },
    'Potassium': {
        'low': {
            'title': 'Hypokalemia (<3.5 mEq/L)',
            'differentials': [
                {'condition': 'GI Losses', 'discussion': 'Diarrhea, vomiting, NG suction. Check urine potassium to differentiate renal vs extrarenal losses.'},
                {'condition': 'Diuretic Use', 'discussion': 'Loop and thiazide diuretics cause renal potassium wasting. Check urine K >20 mEq/L.'},
                {'condition': 'Renal Tubular Acidosis', 'discussion': 'Types I and II cause hypokalemia. Check arterial blood gas, urine pH.'},
                {'condition': 'Hyperaldosteronism', 'discussion': 'Primary (Conn syndrome) or secondary. Hypertension + hypokalemia + metabolic alkalosis. Check aldosterone/renin ratio.'},
            ]
        },
        'high': {
            'title': 'Hyperkalemia (>5.0 mEq/L)',
            'differentials': [
                {'condition': 'Pseudohyperkalemia', 'discussion': 'Hemolyzed sample, fist clenching, prolonged tourniquet. ALWAYS rule out first. Repeat with proper technique.'},
                {'condition': 'Renal Failure', 'discussion': 'Most common true cause. Reduced renal excretion. Critical when >6.0 — ECG changes, cardiac arrest risk.'},
                {'condition': 'Medications', 'discussion': 'ACE inhibitors, ARBs, spironolactone, NSAIDs, trimethoprim, heparin.'},
                {'condition': 'Acidosis', 'discussion': 'Metabolic acidosis causes transcellular shift of K+ out of cells. DKA is a classic cause.'},
                {'condition': 'Tissue Destruction', 'discussion': 'Rhabdomyolysis, tumor lysis syndrome, massive hemolysis, burns.'},
            ]
        }
    },
    'Calcium': {
        'high': {
            'title': 'Hypercalcemia',
            'differentials': [
                {'condition': 'Primary Hyperparathyroidism', 'discussion': 'Most common outpatient cause. Elevated PTH with elevated calcium. Parathyroid adenoma (85%).'},
                {'condition': 'Malignancy', 'discussion': 'Most common inpatient cause. PTHrP-mediated (squamous cell, renal, breast) or osteolytic metastases (myeloma, breast). Check PTHrP, PTH.'},
                {'condition': 'Vitamin D Excess', 'discussion': 'Granulomatous disease (sarcoidosis, TB) or exogenous. Check 25-OH and 1,25-OH vitamin D.'},
                {'condition': 'Thiazide Diuretics', 'discussion': 'Decrease renal calcium excretion.'},
            ]
        },
        'low': {
            'title': 'Hypocalcemia',
            'differentials': [
                {'condition': 'Hypoparathyroidism', 'discussion': 'Post-surgical (most common), autoimmune. Low PTH with low calcium.'},
                {'condition': 'Vitamin D Deficiency', 'discussion': 'Inadequate sun exposure, malabsorption. Low 25-OH vitamin D. Secondary hyperparathyroidism.'},
                {'condition': 'Chronic Kidney Disease', 'discussion': 'Reduced 1,25-OH vitamin D production, hyperphosphatemia.'},
                {'condition': 'Hypoalbuminemia', 'discussion': 'Corrected calcium = measured Ca + 0.8 × (4.0 - albumin). Ionized calcium may be normal.'},
            ]
        }
    },
    'eGFR': {
        'low': {
            'title': 'Reduced eGFR',
            'differentials': [
                {'condition': 'CKD Stage 3a (45-59)', 'discussion': 'Mildly to moderately decreased. Monitor every 3-6 months. Control BP, glucose. Avoid nephrotoxins.'},
                {'condition': 'CKD Stage 3b (30-44)', 'discussion': 'Moderately to severely decreased. Nephrology referral. Monitor for complications (anemia, bone disease).'},
                {'condition': 'CKD Stage 4 (15-29)', 'discussion': 'Severely decreased. Prepare for renal replacement therapy. AV fistula planning.'},
                {'condition': 'CKD Stage 5 (<15)', 'discussion': 'Kidney failure. Dialysis or transplant needed. Urgent nephrology management.'},
            ]
        }
    },
    'Uric_Acid': {
        'high': {
            'title': 'Hyperuricemia',
            'differentials': [
                {'condition': 'Gout', 'discussion': 'Crystal arthropathy. Monosodium urate crystals in joint fluid. Acute flares, tophi. Not all hyperuricemia causes gout.'},
                {'condition': 'Renal Disease', 'discussion': 'Decreased renal excretion is the most common cause of hyperuricemia.'},
                {'condition': 'Tumor Lysis Syndrome', 'discussion': 'Massive cell turnover releases purines. Usually post-chemotherapy. Check K+, phosphorus, calcium, LDH.'},
                {'condition': 'Metabolic Syndrome', 'discussion': 'Associated with insulin resistance, hypertension, dyslipidemia.'},
            ]
        }
    }
}

KFT_LEARNING = {
    'Creatinine': 'Creatinine is produced from muscle metabolism at a constant rate. It is freely filtered by the glomerulus and not reabsorbed. Serum creatinine is inversely related to GFR but is an insensitive marker — GFR must decline ~50% before creatinine rises above normal. Muscle mass, diet (cooked meat), and certain drugs affect levels independently of GFR.',
    'BUN': 'Blood Urea Nitrogen reflects both renal function and protein metabolism. Unlike creatinine, BUN is reabsorbed in the collecting duct (enhanced by ADH). The BUN/Creatinine ratio is diagnostically valuable: >20:1 suggests prerenal disease or GI bleeding; <10:1 suggests liver disease or malnutrition.',
    'eGFR': 'Estimated GFR is calculated using CKD-EPI equation (2021 race-free equation) from creatinine, age, and sex. It is more sensitive than creatinine alone for detecting early CKD. CKD is defined as eGFR <60 for ≥3 months. Staging: G1 ≥90, G2 60-89, G3a 45-59, G3b 30-44, G4 15-29, G5 <15.',
    'Sodium': 'Sodium is the primary determinant of serum osmolality and ECF volume. Hyponatremia is the most common electrolyte disorder in hospitalized patients. Always assess volume status first (hypovolemic vs euvolemic vs hypervolemic). Rapid correction risks osmotic demyelination syndrome — correct ≤8 mEq/L per 24 hours.',
    'Potassium': 'Potassium is the major intracellular cation. 98% is intracellular. Small changes in serum K+ have major effects on cardiac conduction. Hyperkalemia >6.0 is a medical emergency — check ECG for peaked T waves, widened QRS, sine wave pattern. Treatment: calcium gluconate (cardioprotection), insulin+glucose, kayexalate, dialysis.',
    'Calcium': 'Total calcium includes protein-bound (40%), complexed (10%), and ionized/free (50%). Only ionized calcium is physiologically active. Always correct for albumin: corrected Ca = measured Ca + 0.8 × (4.0 - albumin). Calcium homeostasis involves PTH, vitamin D, and calcitonin.',
    'Phosphorus': 'Phosphorus is inversely related to calcium via PTH. In CKD, phosphorus rises as GFR falls, stimulating PTH (secondary hyperparathyroidism) and contributing to renal osteodystrophy. Acute severe hypophosphatemia (<1.0) can cause rhabdomyolysis, respiratory failure, and cardiac dysfunction.',
    'Magnesium': 'Magnesium is often the forgotten electrolyte. Hypomagnesemia causes refractory hypokalemia and hypocalcemia — always check Mg when K or Ca are low and not responding to replacement. Common causes: alcoholism, diuretics, PPI use, diarrhea.',
}


def _get_ref(param: str, sex: str = 'Default') -> Dict:
    if param in KFT_REFERENCE_RANGES:
        refs = KFT_REFERENCE_RANGES[param]
        return refs.get(sex, refs.get('Default', {}))
    return {}


def _classify(param: str, value: float, sex: str = 'Default') -> Dict:
    ref = _get_ref(param, sex)
    if not ref:
        return {'status': 'unknown', 'message': 'No reference range', 'color': 'gray'}
    result = {'value': value, 'unit': ref.get('unit', ''), 'low': ref.get('low'), 'high': ref.get('high'),
              'critical_low': ref.get('critical_low'), 'critical_high': ref.get('critical_high')}
    if value < ref.get('critical_low', float('-inf')):
        result.update({'status': 'critical_low', 'message': f'CRITICAL LOW: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'red'})
    elif value > ref.get('critical_high', float('inf')):
        result.update({'status': 'critical_high', 'message': f'CRITICAL HIGH: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'red'})
    elif value < ref.get('low', 0):
        result.update({'status': 'low', 'message': f'LOW: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    elif value > ref.get('high', float('inf')):
        result.update({'status': 'high', 'message': f'HIGH: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'orange'})
    else:
        result.update({'status': 'normal', 'message': f'NORMAL: {value} (Ref: {ref["low"]}-{ref["high"]})', 'color': 'green'})
    return result


def analyze_kft(parameters: Dict, sex: str = 'Default') -> Dict:
    results = {}
    abnormalities = []
    critical_values = []
    quality_checks = []

    for pname, pdata in parameters.items():
        val = pdata.get('value')
        if val is None or not isinstance(val, (int, float)):
            continue
        c = _classify(pname, val, sex)
        diff = None
        learning = KFT_LEARNING.get(pname)
        if c['status'] not in ('normal', 'unknown'):
            direction = c['status'].replace('critical_', '')
            if pname in KFT_DIFFERENTIALS and direction in KFT_DIFFERENTIALS[pname]:
                diff = KFT_DIFFERENTIALS[pname][direction]
            abnormalities.append({'parameter': pname, 'classification': c, 'differential': diff})
            if 'critical' in c['status']:
                critical_values.append({'parameter': pname, 'value': val, 'status': c['status'], 'message': c['message']})
        results[pname] = {'value': val, 'unit': pdata.get('unit', c.get('unit', '')),
                          'classification': c, 'differential': diff, 'learning': learning}

    # Quality: BUN/Creatinine ratio
    bun = parameters.get('BUN', {}).get('value')
    cr = parameters.get('Creatinine', {}).get('value')
    calc_indices = {}
    if bun and cr and cr > 0:
        ratio = round(bun / cr, 1)
        interp = ('Prerenal (dehydration, CHF, GI bleed)' if ratio > 20 else
                  'Normal' if ratio >= 10 else
                  'Intrinsic renal disease, liver disease, or malnutrition')
        calc_indices['BUN/Creatinine Ratio'] = {
            'value': ratio, 'formula': 'BUN / Creatinine',
            'interpretation': interp, 'note': '>20 prerenal; 10-20 normal; <10 intrinsic/hepatic'
        }

    # Anion gap
    na = parameters.get('Sodium', {}).get('value')
    cl = parameters.get('Chloride', {}).get('value')
    hco3 = parameters.get('Bicarbonate', {}).get('value')
    if na and cl and hco3:
        ag = round(na - (cl + hco3), 1)
        calc_indices['Anion Gap'] = {
            'value': ag, 'formula': 'Na - (Cl + HCO3)',
            'interpretation': ('Elevated — consider MUDPILES: Methanol, Uremia, DKA, Propylene glycol, INH/Iron, Lactic acidosis, Ethylene glycol, Salicylates' if ag > 12
                              else 'Normal' if ag >= 8
                              else 'Low — consider hypoalbuminemia, multiple myeloma'),
            'note': 'Normal: 8-12 mEq/L (with K+: 10-20)'
        }

    # Corrected calcium
    ca = parameters.get('Calcium', {}).get('value')
    alb_data = parameters.get('Albumin', {}).get('value')
    if ca and alb_data and alb_data < 4.0:
        corrected = round(ca + 0.8 * (4.0 - alb_data), 1)
        calc_indices['Corrected Calcium'] = {
            'value': corrected, 'formula': 'Ca + 0.8 × (4.0 - Albumin)',
            'interpretation': f'{corrected} mg/dL (corrected for albumin {alb_data})',
            'note': 'Use when albumin <4.0 g/dL. Normal corrected: 8.5-10.5'
        }

    # CKD staging from eGFR
    egfr = parameters.get('eGFR', {}).get('value')
    if egfr:
        if egfr >= 90: stage = 'G1 (Normal or high)'
        elif egfr >= 60: stage = 'G2 (Mildly decreased)'
        elif egfr >= 45: stage = 'G3a (Mild-moderately decreased)'
        elif egfr >= 30: stage = 'G3b (Moderate-severely decreased)'
        elif egfr >= 15: stage = 'G4 (Severely decreased)'
        else: stage = 'G5 (Kidney failure)'
        calc_indices['CKD Stage'] = {
            'value': stage, 'formula': 'Based on eGFR (CKD-EPI)',
            'interpretation': stage, 'note': 'CKD defined as eGFR <60 for ≥3 months'
        }

    # Quality checks
    if bun and cr:
        quality_checks.append({
            'rule': 'BUN/Creatinine Ratio Assessment',
            'severity': 'pass' if 10 <= (bun/cr if cr > 0 else 0) <= 20 else 'warning',
            'interpretation': f'BUN/Cr ratio: {bun/cr:.1f}. ' + (
                'Normal range.' if 10 <= bun/cr <= 20 else
                'Elevated: consider prerenal causes, GI bleeding.' if bun/cr > 20 else
                'Low: consider liver disease, malnutrition, intrinsic renal.')
        })

    # Pattern summary
    patterns = []
    if cr and _classify('Creatinine', cr, sex)['status'] in ('high', 'critical_high'):
        if bun and cr > 0 and bun / cr > 20:
            patterns.append('**Prerenal azotemia pattern**: elevated BUN/Cr ratio >20:1')
        else:
            patterns.append('**Renal impairment**: elevated creatinine')
    
    na_val = parameters.get('Sodium', {}).get('value')
    k_val = parameters.get('Potassium', {}).get('value')
    electrolyte_issues = []
    if na_val and na_val < 136: electrolyte_issues.append('hyponatremia')
    if na_val and na_val > 145: electrolyte_issues.append('hypernatremia')
    if k_val and k_val < 3.5: electrolyte_issues.append('hypokalemia')
    if k_val and k_val > 5.0: electrolyte_issues.append('hyperkalemia')
    if electrolyte_issues:
        patterns.append(f'**Electrolyte abnormalities**: {", ".join(electrolyte_issues)}')
    
    pattern_summary = '\n\n'.join(patterns) if patterns else 'No significant renal or electrolyte pattern identified.'

    # Educational content
    edu = """### 🎓 KFT Learning Points

**1. Creatinine vs GFR**: Creatinine is a late marker — GFR must drop ~50% before creatinine rises. eGFR is more sensitive for early CKD detection.

**2. BUN/Creatinine Ratio**: This simple ratio differentiates prerenal (>20:1) from intrinsic renal disease (~10-15:1) and identi
