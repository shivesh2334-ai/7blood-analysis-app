"""
Learning Engine - Provides educational content for parameters and panels.
"""
from typing import Optional


def get_learning_content(panel: str) -> str:
    """Get general learning content for a panel."""
    content = {
        'CBC': 'The Complete Blood Count is the most commonly ordered blood test. It provides information about three cell lines: red blood cells (oxygen transport), white blood cells (immune function), and platelets (hemostasis).',
        'LFT': 'Liver Function Tests include both biochemical markers of injury (ALT, AST, ALP) and functional markers of synthetic capacity (albumin, PT/INR). The R value helps classify injury pattern.',
        'KFT': 'Kidney Function Tests assess glomerular filtration (creatinine, eGFR), tubular function (electrolytes), and overall renal homeostasis. BUN/Creatinine ratio helps differentiate prerenal from intrinsic disease.',
        'Lipid': 'The Lipid Profile assesses cardiovascular risk. LDL is the primary treatment target. Non-HDL cholesterol captures all atherogenic particles. Triglycerides >500 carry pancreatitis risk.',
        'Sugar': 'Blood glucose assessment includes acute (fasting/random glucose) and chronic (HbA1c) measurements. HOMA-IR quantifies insulin resistance. C-peptide distinguishes endogenous from exogenous insulin.',
        'Urine': 'Urine Routine & Microscopy provides non-invasive assessment of kidney and urinary tract. Dipstick screening plus microscopy for cellular elements, casts, and crystals.',
        'TFT': 'Thyroid Function Tests follow a hierarchical approach: TSH first, then FT4/FT3. The inverse log-linear TSH-FT4 relationship makes TSH the most sensitive screening test.',
        'Rheumatology': 'Rheumatology markers help identify autoimmune diseases. Sensitivity vs specificity trade-offs are critical: ANA is sensitive for SLE; Anti-CCP is specific for RA.',
        'Oncology': 'Tumor markers are primarily used for monitoring, not screening. Rising trends are more informative than single values. Always consider benign causes of elevation.',
    }
    return content.get(panel, '')


def get_parameter_education(param: str) -> Optional[str]:
    """Get educational content for a specific parameter."""
    # This can be expanded as needed
    return None
