# config.py — Job Resume AI Starter
# Updated for Gmail + Adzuna API

# --- EMAIL (Gmail App Password) ---
EMAIL_USER = "raoufmayahi@gmail.com"  # <— change to your Gmail
EMAIL_PASS = "eqqeshwtbkssvmym"  # from myaccount.google.com > App passwords
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- ADZUNA API (free tier) ---
# Get free keys at https://developer.adzuna.com
ADZUNA_APP_ID = "your_adzuna_app_id"
ADZUNA_APP_KEY = "your_adzuna_app_key"

# --- RESUME PATH ---
# Not used directly now (resume is embedded), but keep for reference
RESUME_PATH = r"C:\Users\FARA\Desktop\job_resume_ai_starter\RAOUF_MAYAHI.pdf"

# --- JOB SEARCH SETTINGS ---
LOCATION = "Ontario, Canada"
MAX_DAYS_OLD = 20
MAX_JOBS = 30

# --- TAILORING KEYWORDS ---
# Used to boost ATS score
WELDING_KEYWORDS = ['weld', 'tssa', 'cwb', 'fabricat', 'steel', 'blueprint']
LEAN_KEYWORDS = ['lean', 'six sigma', 'kaizen', '5s', 'continuous improvement', 'root cause']
QUALITY_KEYWORDS = ['iso', 'iatf', 'as9100', 'qms', 'defect', 'quality']
SAFETY_KEYWORDS = ['hse', 'ohsa', 'jhsc', 'lti', 'safety']