# Job-Resume AI System (Python starter)

Implements your requested features in modular Python.

## What it does
- Input: fetches jobs via Adzuna free API (Canada), searches keywords, filters by location/industry
- Output: generates tailored resume from your profile + job description, predicts ATS score, suggests improvements, compares resumes
- Optimization: inserts job keywords, scores each section, suggests format fixes, paraphrases bullets
- Tone: humanizes language, runs sentiment analysis
- NLP: entity recognition (spaCy), sentiment (TextBlob), topic modeling (LDA), TF-IDF keywords
- Email UX: send notifications via Gmail SMTP, read commands from inbox subject "JOB: ...", stores in Gmail label

## Important API reality check
- LinkedIn Jobs API is currently unavailable for new partnerships. Access requires Apply Connect approval.
- Indeed public API was retired in 2020. Sponsored Jobs API now requires paid access.
- Use free alternatives: Adzuna, JSearch (RapidAPI), Remotive, Arbeitnow. This starter uses Adzuna.

## Setup
1. pip install -r requirements.txt
2. python -m spacy download en_core_web_sm
3. python -m textblob.download_corpora
4. Set env vars: ADZUNA_APP_ID, ADZUNA_APP_KEY, GMAIL_USER, GMAIL_APP_PASSWORD
5. Edit USER_PROFILE in config.py
6. python main.py

## Email interface examples
Send yourself an email with subject:
- JOB: find python toronto
- JOB: filter industry technology

The bot polls unseen emails and triggers run_daily().
