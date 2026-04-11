"""
Configuration Module
====================
Centralized configuration constants and settings for the LabIQ platform.
Supports environment variable overrides via python-dotenv.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── AI / API Configuration ───────────────────────────────────────────────────
AI_MODEL = os.getenv("LABIQ_AI_MODEL", "claude-sonnet-4-20250514")
AI_MAX_TOKENS = int(os.getenv("LABIQ_AI_MAX_TOKENS", "2000"))

# ── Application Defaults ─────────────────────────────────────────────────────
DEFAULT_AGE = int(os.getenv("LABIQ_DEFAULT_AGE", "35"))
DEFAULT_SEX = os.getenv("LABIQ_DEFAULT_SEX", "male")
DEFAULT_ACTIVE_PANELS = ["CBC", "LFT", "KFT", "LIPID", "DIABETES", "TFT"]

# ── OCR Settings ─────────────────────────────────────────────────────────────
OCR_MAX_TEXT_PREVIEW = 3000

# ── Report Settings ──────────────────────────────────────────────────────────
DEFAULT_REPORT_TITLE = "Comprehensive Lab Investigation Report"
DEFAULT_REPORT_FOOTER = "Educational tool only — not for clinical use."
