"""
OCR and Document Parsing Module with Enhanced Debugging and Value Validation.
Handles extraction of blood parameters from uploaded documents with confidence scoring,
unit normalization, and physiological validation.
"""

import re
import io
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# =============================================
# ENUMS AND DATACLASSES
# =============================================

class ValidationStatus(Enum):
    """Enum for parameter value validation status."""
    VALID = "valid"
    QUESTIONABLE = "questionable"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class ParsingStepStatus(Enum):
    """Enum for parsing step status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ParsedValue:
    """Represents a parsed blood parameter value with metadata."""
    value: float
    unit: str  # Standard unit
    original_unit: str  # Unit as found in text
    confidence_score: float  # 0-1, based on pattern match quality
    raw_match: str  # Original matched text
    validation_status: str  # ValidationStatus enum value
    validation_message: str  # Reason for validation status
    pattern_used: str = ""  # Which pattern matched
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for UI display and serialization."""
        return {
            'value': self.value,
            'unit': self.unit,
            'original_unit': self.original_unit,
            'confidence_score': round(self.confidence_score, 2),
            'raw_match': self.raw_match,
            'validation_status': self.validation_status,
            'validation_message': self.validation_message,
            'pattern_used': self.pattern_used
        }
    
    def is_reliable(self) -> bool:
        """Check if value is reliable for analysis."""
        return (self.validation_status == ValidationStatus.VALID.value and 
                self.confidence_score >= 0.7)


@dataclass
class ParsingStep:
    """Represents a step in the parsing process for debugging."""
    step_name: str
    status: str  # ParsingStepStatus enum value
    timestamp: datetime
    items_processed: int = 0
    items_found: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    details: Dict = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for UI display."""
        return {
            'step_name': self.step_name,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'items_processed': self.items_processed,
            'items_found': self.items_found,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': self.details
        }


@dataclass
class ParsingQualityMetrics:
    """Metrics about the overall parsing quality."""
    total_parameters_expected: int = 0
    total_parameters_found: int = 0
    reliable_parameters: int = 0
    questionable_parameters: int = 0
    invalid_parameters: int = 0
    average_confidence: float = 0.0
    parsing_success_rate: float = 0.0  # percentage
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for UI display."""
        return {
            'total_parameters_found': self.total_parameters_found,
            'reliable_parameters': self.reliable_parameters,
            'questionable_parameters': self.questionable_parameters,
            'invalid_parameters': self.invalid_parameters,
            'average_confidence': round(self.average_confidence, 2),
            'parsing_success_rate': f"{self.parsing_success_rate:.1f}%"
        }


# =============================================
# REFERENCE RANGES FOR VALIDATION
# =============================================

PHYSIOLOGICAL_RANGES = {
    'RBC': {'min': 3.5, 'max': 5.5, 'unit': 'x10¹²/L'},
    'Hemoglobin': {'min': 7.0, 'max': 18.0, 'unit': 'g/dL'},
    'Hematocrit': {'min': 20, 'max': 55, 'unit': '%'},
    'MCV': {'min': 70, 'max': 100, 'unit': 'fL'},
    'WBC': {'min': 2.0, 'max': 30.0, 'unit': 'x10⁹/L'},
    'Platelets': {'min': 50, 'max': 500, 'unit': 'x10⁹/L'},
    'Hemoglobin': {'min': 7.0, 'max': 20.0, 'unit': 'g/dL'},
    'ALT': {'min': 5, 'max': 300, 'unit': 'IU/L'},
    'AST': {'min': 5, 'max': 300, 'unit': 'IU/L'},
    'Creatinine': {'min': 0.4, 'max': 2.0, 'unit': 'mg/dL'},
    'Total_Cholesterol': {'min': 100, 'max': 400, 'unit': 'mg/dL'},
    'Triglycerides': {'min': 30, 'max': 600, 'unit': 'mg/dL'},
    'TSH': {'min': 0.2, 'max': 10.0, 'unit': 'µIU/mL'},
    'Fasting_Glucose': {'min': 40, 'max': 500, 'unit': 'mg/dL'},
}

UNIT_CONVERSIONS = {
    # Glucose conversions (mg/dL ↔ mmol/L)
    'glucose': {'mg/dL': 1, 'mmol/L': 0.0555},
    # Cholesterol conversions
    'cholesterol': {'mg/dL': 1, 'mmol/L': 0.0259},
    # Creatinine conversions
    'creatinine': {'mg/dL': 1, 'µmol/L': 88.4},
    # BUN conversions
    'bun': {'mg/dL': 1, 'mmol/L': 0.357},
}

PARAMETER_PATTERNS = {
    # Complete Blood Count (CBC)
    'RBC': {
        'patterns': [
            r'(?:RBC|Red\s*Blood\s*Cell(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
            r'(?:Erythrocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10¹²/L',
        'alt_units': ['million/µL', 'M/µL', '10^12/L']
    },
    'Hemoglobin': {
        'patterns': [
            r'(?:Hemoglobin|Haemoglobin|Hgb|Hb|HGB)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'g/dL',
        'alt_units': ['g/L', 'g/dl']
    },
    'Hematocrit': {
        'patterns': [
            r'(?:Hematocrit|Haematocrit|HCT|Hct|PCV|Packed\s*Cell\s*Volume)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': '%',
        'alt_units': ['%', 'L/L']
    },
    'MCV': {
        'patterns': [r'(?:MCV|Mean\s*Corpuscular\s*Volume)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'fL', 'alt_units': ['fl', 'fL']
    },
    'WBC': {
        'patterns': [
            r'(?:WBC|White\s*Blood\s*Cell(?:s)?(?:\s*Count)?|Total\s*Leucocyte\s*Count|TLC)\s*[:\-]?\s*([\d.]+)',
            r'(?:Leukocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L', 'alt_units': ['K/µL', '10^9/L']
    },
    'Platelets': {
        'patterns': [
            r'(?:Platelet(?:s)?(?:\s*Count)?|PLT|Plt)\s*[:\-]?\s*([\d.]+)',
            r'(?:Thrombocyte(?:s)?(?:\s*Count)?)\s*[:\-]?\s*([\d.]+)',
        ],
        'unit': 'x10⁹/L', 'alt_units': ['K/µL', '10^9/L']
    },
    # Liver Function Tests (LFT)
    'ALT': {
        'patterns': [r'(?:ALT|SGPT|Alanine\s*(?:Amino)?transferase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L', 'IU/L']
    },
    'AST': {
        'patterns': [r'(?:AST|SGOT|Aspartate\s*(?:Amino)?transferase)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'IU/L', 'alt_units': ['U/L', 'IU/L']
    },
    # Kidney Function Tests (KFT)
    'Creatinine': {
        'patterns': [r'(?:Creatinine|Creat|CREA)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['µmol/L', 'umol/L']
    },
    'BUN': {
        'patterns': [r'(?:BUN|Blood\s*Urea\s*Nitrogen|Urea\s*Nitrogen)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    # Lipid Profile
    'Total_Cholesterol': {
        'patterns': [r'(?:Total\s*Cholesterol|T[\.\s]*Chol|Cholesterol\s*Total)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    'Triglycerides': {
        'patterns': [r'(?:Triglycerides|TG|TGL|TRIG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    # Blood Sugar
    'Fasting_Glucose': {
        'patterns': [r'(?:Fasting\s*Glucose|Fasting\s*Blood\s*Sugar|FBS|FBG)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'mg/dL', 'alt_units': ['mmol/L']
    },
    # Thyroid Function Tests (TFT)
    'TSH': {
        'patterns': [r'(?:TSH|Thyroid\s*Stimulating\s*Hormone|Thyrotropin)\s*[:\-]?\s*([\d.]+)'],
        'unit': 'µIU/mL', 'alt_units': ['mIU/L', 'mU/L']
    },
}


# =============================================
# UTILITY FUNCTIONS
# =============================================

def normalize_unit(value: float, original_unit: str, target_unit: str) -> Tuple[float, bool]:
    """
    Convert value between different unit systems.
    
    Args:
        value: The numeric value
        original_unit: The original unit
        target_unit: The target unit
    
    Returns:
        Tuple of (converted_value, conversion_successful)
    """
    if original_unit == target_unit:
        return value, True
    
    # Normalize unit strings
    original_unit = original_unit.strip().lower()
    target_unit = target_unit.strip().lower()
    
    # Try to find matching conversion pair
    for conversion_group, conversions in UNIT_CONVERSIONS.items():
        unit_keys = [k.lower() for k in conversions.keys()]
        if original_unit in unit_keys and target_unit in unit_keys:
            # Found matching conversion group
            original_factor = conversions[list(conversions.keys())[unit_keys.index(original_unit)]]
            target_factor = conversions[list(conversions.keys())[unit_keys.index(target_unit)]]
            
            if target_factor > 0:
                converted = value * (original_factor / target_factor)
                return converted, True
    
    # No conversion found
    return value, False


def validate_parameter_value(param_name: str, value: float, unit: str = "") -> Dict:
    """
    Validate if a parameter value is physiologically reasonable.
    
    Args:
        param_name: Name of the parameter
        value: The numeric value
        unit: The unit of measurement
    
    Returns:
        Dict with 'status', 'message', and 'is_valid' keys
    """
    # Check for invalid numeric values
    if value < 0:
        return {
            'status': ValidationStatus.INVALID.value,
            'message': 'Negative values are physiologically invalid',
            'is_valid': False
        }
    
    if value == 0:
        return {
            'status': ValidationStatus.QUESTIONABLE.value,
            'message': 'Zero value is unlikely; may be OCR error',
            'is_valid': False
        }
    
    # Check against physiological ranges
    if param_name in PHYSIOLOGICAL_RANGES:
        range_info = PHYSIOLOGICAL_RANGES[param_name]
        min_val = range_info['min']
        max_val = range_info['max']
        
        if value < min_val:
            return {
                'status': ValidationStatus.QUESTIONABLE.value,
                'message': f'Value below typical physiological range ({min_val}-{max_val})',
                'is_valid': True  # Still valid but questionable
            }
        elif value > max_val:
            return {
                'status': ValidationStatus.QUESTIONABLE.value,
                'message': f'Value above typical physiological range ({min_val}-{max_val})',
                'is_valid': True  # Still valid but questionable
            }
        else:
            return {
                'status': ValidationStatus.VALID.value,
                'message': 'Within normal physiological range',
                'is_valid': True
            }
    
    # Unknown parameter
    return {
        'status': ValidationStatus.UNKNOWN.value,
        'message': 'Parameter not in validation database',
        'is_valid': True  # Assume valid if not in database
    }


def get_parsing_confidence(param_name: str, pattern_index: int, 
                          total_patterns: int, match_length: int) -> float:
    """
    Calculate confidence score for parsed value.
    
    Factors:
    - First pattern match = higher confidence
    - Exact pattern match length matters
    - Earlier patterns typically more specific
    
    Args:
        param_name: Name of parameter
        pattern_index: Which pattern matched (0-indexed)
        total_patterns: Total patterns available
        match_length: Length of matched text
    
    Returns:
        Confidence score 0-1
    """
    # Base confidence decreases with pattern index (first pattern is most specific)
    base_confidence = max(0.9 - (pattern_index * 0.15), 0.5)
    
    # Match length bonus (longer matches are typically more reliable)
    length_bonus = min(match_length / 50, 0.1)  # Max 10% bonus
    
    confidence = min(base_confidence + length_bonus, 1.0)
    return confidence


def extract_text_from_image(image: Image.Image, debug: bool = False) -> Tuple[str, ParsingStep]:
    """
    Extract text from an image using Tesseract OCR.
    
    Args:
        image: PIL Image object
        debug: Enable debug mode
    
    Returns:
        Tuple of (extracted_text, parsing_step)
    """
    step = ParsingStep(
        step_name="OCR Image Extraction",
        status=ParsingStepStatus.SUCCESS.value,
        timestamp=datetime.now()
    )
    
    if pytesseract is None:
        error_msg = "pytesseract not installed"
        step.status = ParsingStepStatus.FAILED.value
        step.errors.append(error_msg)
        return "", step
    
    try:
        # Preprocess image for better OCR
        image_gray = image.convert('L')
        text = pytesseract.image_to_string(image_gray, config='--psm 6 --oem 3')
        
        step.items_found = len(text.split('\n'))
        
        if debug:
            step.details = {
                'image_size': image.size,
                'text_length': len(text),
                'lines_extracted': step.items_found
            }
        
        return text, step
        
    except Exception as e:
        step.status = ParsingStepStatus.FAILED.value
        step.errors.append(f"OCR Error: {str(e)}")
        return "", step


def extract_text_from_pdf(pdf_bytes: bytes, debug: bool = False) -> Tuple[str, ParsingStep]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_bytes: PDF file bytes
        debug: Enable debug mode
    
    Returns:
        Tuple of (extracted_text, parsing_step)
    """
    step = ParsingStep(
        step_name="PDF Text Extraction",
        status=ParsingStepStatus.SUCCESS.value,
        timestamp=datetime.now()
    )
    
    all_text = ""
    pages_processed = 0
    
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages_processed = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                if row:
                                    all_text += " ".join([str(c) if c else "" for c in row]) + "\n"
                
                step.items_found = pages_processed
                
        except Exception as e:
            step.status = ParsingStepStatus.WARNING.value
            step.warnings.append(f"PDF text extraction partial: {str(e)}")

    # Fallback to image-based OCR if text extraction was insufficient
    if len(all_text.strip()) < 50:
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=300)
            
            for img_num, img in enumerate(images):
                ocr_text, _ = extract_text_from_image(img, debug=debug)
                all_text += ocr_text + "\n"
            
            if step.status == ParsingStepStatus.SUCCESS.value:
                step.status = ParsingStepStatus.PARTIAL.value
            step.warnings.append("Fell back to image OCR for complete text extraction")
            
        except Exception as e:
            if step.status == ParsingStepStatus.SUCCESS.value:
                step.status = ParsingStepStatus.FAILED.value
            step.errors.append(f"PDF Image OCR Error: {str(e)}")

    if debug:
        step.details = {
            'pages_processed': pages_processed,
            'total_text_length': len(all_text),
            'extraction_method': 'text' if pages_processed > 0 else 'ocr'
        }

    return all_text, step


def parse_parameters(text: str, debug: bool = False) -> Tuple[Dict, ParsingStep]:
    """
    Parse blood parameters from extracted text with validation.
    
    Args:
        text: Extracted text from document
        debug: Enable debug mode
    
    Returns:
        Tuple of (results_dict, parsing_step)
    """
    step = ParsingStep(
        step_name="Parameter Parsing",
        status=ParsingStepStatus.SUCCESS.value,
        timestamp=datetime.now(),
        items_processed=len(PARAMETER_PATTERNS)
    )
    
    results = {}
    
    for param_name, config in PARAMETER_PATTERNS.items():
        param_found = False
        
        for pattern_idx, pattern in enumerate(config['patterns']):
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                try:
                    value_str = match.group(1).strip()
                    value = float(value_str)
                    
                    # Get standard unit
                    standard_unit = config['unit']
                    original_unit = standard_unit
                    
                    # Calculate confidence
                    confidence = get_parsing_confidence(
                        param_name, 
                        pattern_idx, 
                        len(config['patterns']),
                        len(match.group(0))
                    )
                    
                    # Validate value
                    validation = validate_parameter_value(param_name, value, standard_unit)
                    
                    # Create parsed value object
                    parsed_value = ParsedValue(
                        value=value,
                        unit=standard_unit,
                        original_unit=original_unit,
                        confidence_score=confidence,
                        raw_match=match.group(0),
                        validation_status=validation['status'],
                        validation_message=validation['message'],
                        pattern_used=f"Pattern {pattern_idx}"
                    )
                    
                    results[param_name] = parsed_value
                    param_found = True
                    step.items_found += 1
                    
                    if debug:
                        if param_name not in step.details:
                            step.details[param_name] = []
                        step.details[param_name].append(parsed_value.to_dict())
                    
                    break  # Found match, move to next parameter
                    
                except (ValueError, IndexError) as e:
                    if debug:
                        step.warnings.append(f"{param_name}: Failed to parse value - {str(e)}")
                    continue
        
        if not param_found and debug:
            step.details[param_name] = "Not found"

    # Calculate quality metrics within parsing step
    if results:
        reliable_count = sum(1 for pv in results.values() if pv.is_reliable())
        step.details['quality_summary'] = {
            'total_found': len(results),
            'reliable': reliable_count,
            'avg_confidence': round(sum(pv.confidence_score for pv in results.values()) / len(results), 2)
        }

    return results, step


def extract_patient_info(text: str, debug: bool = False) -> Tuple[Dict, ParsingStep]:
    """
    Extract patient demographic information from text.
    
    Args:
        text: Extracted text from document
        debug: Enable debug mode
    
    Returns:
        Tuple of (patient_info_dict, parsing_step)
    """
    step = ParsingStep(
        step_name="Patient Info Extraction",
        status=ParsingStepStatus.SUCCESS.value,
        timestamp=datetime.now()
    )
    
    info = {}
    
    # Name extraction
    name_match = re.search(r'(?:Patient\s*Name|Name|Patient)\s*[:\-]?\s*([A-Za-z\s.]+?)(?:\n|$|Age|Sex)', text, re.IGNORECASE)
    if name_match:
        info['name'] = name_match.group(1).strip()
        step.items_found += 1

    # Age extraction
    age_match = re.search(r'(?:Age)\s*[:\-]?\s*(\d+)\s*(?:years?|yrs?|Y)?', text, re.IGNORECASE)
    if age_match:
        info['age'] = age_match.group(1)
        step.items_found += 1

    # Sex extraction
    sex_match = re.search(r'(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)', text, re.IGNORECASE)
    if sex_match:
        val = sex_match.group(1).strip().upper()
        info['sex'] = 'Male' if val in ['M', 'MALE'] else 'Female'
        step.items_found += 1

    # Date extraction
    date_match = re.search(r'(?:Date|Collection\s*Date|Report\s*Date)\s*[:\-]?\s*([\d/\-\.]+)', text, re.IGNORECASE)
    if date_match:
        info['date'] = date_match.group(1)
        step.items_found += 1

    if debug:
        step.details = info

    return info, step


def process_uploaded_file(uploaded_file, debug: bool = False) -> Tuple[str, Dict, Dict, List[ParsingStep], ParsingQualityMetrics]:
    """
    Process an uploaded file and return extracted text, parameters, patient info, and metadata.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        debug: Enable debug mode for detailed logging
    
    Returns:
        Tuple of:
        - extracted_text: Raw extracted text
        - parameters: Dict of ParsedValue objects
        - patient_info: Dict of patient information
        - parsing_steps: List of ParsingStep objects
        - quality_metrics: ParsingQualityMetrics object
    """
    parsing_steps = []
    file_type = uploaded_file.type
    file_bytes = uploaded_file.read()
    extracted_text = ""

    # Step 1: Extract text from file
    if 'pdf' in file_type:
        extracted_text, pdf_step = extract_text_from_pdf(file_bytes, debug=debug)
        parsing_steps.append(pdf_step)
    elif 'image' in file_type or file_type in ['image/jpeg', 'image/jpg', 'image/png']:
        image = Image.open(io.BytesIO(file_bytes))
        extracted_text, image_step = extract_text_from_image(image, debug=debug)
        parsing_steps.append(image_step)
    else:
        error_step = ParsingStep(
            step_name="File Type Validation",
            status=ParsingStepStatus.FAILED.value,
            timestamp=datetime.now(),
            errors=["Unsupported file format"]
        )
        parsing_steps.append(error_step)
        
        # Initialize empty metrics
        metrics = ParsingQualityMetrics()
        return "", {}, {}, parsing_steps, metrics

    # Step 2: Parse parameters
    parameters, param_step = parse_parameters(extracted_text, debug=debug)
    parsing_steps.append(param_step)

    # Step 3: Extract patient info
    patient_info, patient_step = extract_patient_info(extracted_text, debug=debug)
    parsing_steps.append(patient_step)

    # Calculate quality metrics
    metrics = ParsingQualityMetrics(
        total_parameters_found=len(parameters),
        reliable_parameters=sum(1 for pv in parameters.values() if pv.is_reliable()),
        questionable_parameters=sum(1 for pv in parameters.values() 
                                   if pv.validation_status == ValidationStatus.QUESTIONABLE.value),
        invalid_parameters=sum(1 for pv in parameters.values() 
                              if pv.validation_status == ValidationStatus.INVALID.value),
        average_confidence=sum(pv.confidence_score for pv in parameters.values()) / len(parameters) if parameters else 0,
        parsing_success_rate=(len(parameters) / len(PARAMETER_PATTERNS) * 100) if PARAMETER_PATTERNS else 0
    )

    return extracted_text, parameters, patient_info, parsing_steps, metrics
