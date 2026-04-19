# ats_scorer.py - simple ATS simulation
import re
from nlp_engine import extract_job_keywords

def normalize(text):
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())

def score_resume(resume_text, job_description):
    job_kw = extract_job_keywords(job_description)
    resume_norm = normalize(resume_text)
    matches = sum(1 for kw in job_kw if kw.lower() in resume_norm)
    keyword_score = matches / max(len(job_kw), 1)

    # format checks
    length_ok = 400 < len(resume_text.split()) < 900
    has_sections = all(s in resume_text.lower() for s in ["experience", "skills", "education"])
    format_score = (0.5 if length_ok else 0.2) + (0.5 if has_sections else 0)

    total = round((0.7 * keyword_score + 0.3 * format_score) * 100, 1)
    
    suggestions = []
    if keyword_score < 0.6:
        missing = [kw for kw in job_kw if kw.lower() not in resume_norm][:10]
        suggestions.append(f"Add missing keywords: {', '.join(missing)}")
    if not length_ok:
        suggestions.append("Adjust resume length to 1-2 pages (~500-800 words)")
    if not has_sections:
        suggestions.append("Ensure clear headings: Experience, Skills, Education")

    return {"ats_score": total, "keyword_match": round(keyword_score*100,1), "suggestions": suggestions, "matched_keywords": matches, "total_keywords": len(job_kw)}
