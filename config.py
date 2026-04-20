# config.py — Job-AI Resume Optimizer
# Loads from environment variables first, then falls back to defaults below.
import os
from pathlib import Path

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

# ── Email / Gmail ─────────────────────────────────────────────────────────────
EMAIL_USER  = _env("GMAIL_USER",         "raoufmayahi@gmail.com")
EMAIL_PASS  = _env("GMAIL_APP_PASSWORD", "eqqeshwtbkssvmym")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587

# Gmail labels (auto-created by gmail_manager.create_labels())
GMAIL_LABEL_JOBS      = "Job-AI/All-Jobs"
GMAIL_LABEL_APPLIED   = "Job-AI/Applied"
GMAIL_LABEL_GENERATED = "Job-AI/Generated-Resumes"

# ── Adzuna API (free tier — get keys at developer.adzuna.com) ─────────────────
ADZUNA_APP_ID  = _env("ADZUNA_APP_ID",  "your_adzuna_app_id")
ADZUNA_APP_KEY = _env("ADZUNA_APP_KEY", "your_adzuna_app_key")

# ── User profile ──────────────────────────────────────────────────────────────
USER_PROFILE_PATH = Path(__file__).parent / "data" / "user_profile.json"
RESUME_PATH       = _env("RESUME_PATH", "")          # optional: path to base resume PDF/DOCX

# ── Job search settings ───────────────────────────────────────────────────────
LOCATION    = _env("JOB_LOCATION", "Ontario, Canada")
MAX_DAYS_OLD = int(_env("MAX_DAYS_OLD", "20"))
MAX_JOBS     = int(_env("MAX_JOBS",     "30"))

# ── ATS keyword groups (used to boost scoring) ────────────────────────────────
WELDING_KEYWORDS = ['weld', 'tssa', 'cwb', 'fabricat', 'steel', 'blueprint']
LEAN_KEYWORDS    = ['lean', 'six sigma', 'kaizen', '5s', 'continuous improvement', 'root cause']
QUALITY_KEYWORDS = ['iso', 'iatf', 'as9100', 'qms', 'defect', 'quality']
SAFETY_KEYWORDS  = ['hse', 'ohsa', 'jhsc', 'lti', 'safety']

# ── Exclusion list for irrelevant industries ──────────────────────────────────
EXCLUDED_INDUSTRIES = [
    'food', 'dairy', 'bakery', 'restaurant', 'tim hortons',
    'mcdonald', 'server', 'cook', 'chef', 'retail', 'cashier',
    'pizza', 'grocery',
]

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_BASE_DIR = Path.home() / "Desktop" / "Job_Applications"
HISTORY_FILE    = Path(__file__).parent / "data" / "resume_history.json"
