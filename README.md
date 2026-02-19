# 🩸 Hematology Blood Investigation Analysis Tool

An AI-powered Streamlit application for extracting, analyzing, and interpreting Complete Blood Count (CBC) and other blood investigation reports. Designed as a learning and clinical analysis tool for hematologists and medical professionals.

## Features

- **Multi-format Upload**: Supports PDF, JPG, JPEG, PNG blood report uploads
- **Automated OCR Extraction**: Extracts blood parameters from uploaded documents
- **Manual Editing**: Add, edit, or delete extracted parameters
- **Quality Assessment**: Evaluates sample quality based on the "Rule of Threes" and other checks
- **Parameter-by-Parameter Analysis**: Detailed abnormality detection with differential diagnosis
- **AI Review**: Claude AI-powered comprehensive review of findings
- **Downloadable Reports**: Export analysis as professional PDF reports

## Reference Ranges (Adults)

| Parameter | Unit | Male | Female |
|-----------|------|------|--------|
| RBC | x10¹²/L | 4.5-5.5 | 4.0-5.0 |
| Hemoglobin | g/dL | 13.5-17.5 | 12.0-16.0 |
| Hematocrit | % | 38.3-48.6 | 35.5-44.9 |
| MCV | fL | 80-100 | 80-100 |
| MCH | pg | 27-33 | 27-33 |
| MCHC | g/dL | 32-36 | 32-36 |
| RDW-CV | % | 11.5-14.5 | 11.5-14.5 |
| WBC | x10⁹/L | 4.0-11.0 | 4.0-11.0 |
| Platelets | x10⁹/L | 150-400 | 150-400 |
| MPV | fL | 7.5-12.5 | 7.5-12.5 |
| Reticulocyte | % | 0.5-2.5 | 0.5-2.5 |

## Setup

### Prerequisites
- Python 3.9+
- Tesseract OCR installed on your system
- Claude API key from Anthropic

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/blood-analysis-app.git
cd blood-analysis-app

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# For PDF support, install poppler
# Ubuntu: sudo apt-get install poppler-utils
# Mac: brew install poppler
# Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases
