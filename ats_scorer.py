"""ats_scorer.py — Comprehensive ATS scoring with format analysis and improvement suggestions"""
import re
from nlp_engine import extract_job_keywords, resume_job_similarity


def _normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def _count_words(text: str) -> int:
    return len(text.split())


def _has_section(text: str, section: str) -> bool:
    return bool(re.search(r'\b' + re.escape(section) + r'\b', text, re.IGNORECASE))


def _detect_contact_info(text: str) -> dict:
    email_ok = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
    phone_ok  = bool(re.search(r'\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4}', text))
    linkedin  = bool(re.search(r'linkedin\.com', text, re.IGNORECASE))
    return {"email": email_ok, "phone": phone_ok, "linkedin": linkedin}


def _count_bullets(text: str) -> int:
    return len(re.findall(r'^\s*[•\-\*·]', text, re.MULTILINE))


def _count_metrics(text: str) -> int:
    pattern = re.compile(
        r'\b\d+[\.,]?\d*\s*(%|percent|million|thousand|k\b|\$|hours?|days?|weeks?|months?|years?)\b',
        re.IGNORECASE,
    )
    return len(pattern.findall(text))


def _format_score(resume_text: str) -> tuple[float, list[str]]:
    """
    Check resume format and return (score 0-1, format_suggestions list).
    """
    score       = 0.0
    suggestions = []
    word_count  = _count_words(resume_text)

    # Length check (ideal: 400–900 words)
    if 400 <= word_count <= 900:
        score += 0.25
    elif 200 <= word_count < 400 or 900 < word_count <= 1200:
        score += 0.12
        suggestions.append(
            f"Resume length is {word_count} words. Aim for 450–800 words (1–2 pages)."
        )
    else:
        suggestions.append(
            f"Resume length ({word_count} words) is outside ideal range (450–800). "
            "Trim or expand accordingly."
        )

    # Required sections
    required_sections = ["experience", "skills", "education"]
    missing_sections  = [s for s in required_sections if not _has_section(resume_text, s)]
    if not missing_sections:
        score += 0.25
    else:
        suggestions.append(
            f"Missing critical sections: {', '.join(s.title() for s in missing_sections)}. "
            "ATS parsers expect these headings."
        )
        score += 0.05 * (len(required_sections) - len(missing_sections))

    # Contact information
    contact = _detect_contact_info(resume_text)
    contact_score = sum(contact.values()) / len(contact)
    score += 0.15 * contact_score
    if not contact["email"]:
        suggestions.append("Add your email address — required by all ATS systems.")
    if not contact["phone"]:
        suggestions.append("Add a phone number for recruiter contact.")
    if not contact["linkedin"]:
        suggestions.append("Include your LinkedIn URL to boost credibility.")

    # Bullet points
    bullet_count = _count_bullets(resume_text)
    if bullet_count >= 8:
        score += 0.20
    elif bullet_count >= 4:
        score += 0.12
        suggestions.append(
            f"Only {bullet_count} bullet points detected. Use 8–15 bullets to highlight achievements."
        )
    else:
        suggestions.append(
            "Use bullet points (•) to structure experience. Unstructured paragraphs score poorly in ATS."
        )

    # Quantified achievements
    metric_count = _count_metrics(resume_text)
    if metric_count >= 5:
        score += 0.15
    elif metric_count >= 2:
        score += 0.08
        suggestions.append(
            f"Only {metric_count} quantified metrics found. Add at least 5 concrete numbers "
            "(%, $, headcount, time saved) to strengthen your impact statements."
        )
    else:
        suggestions.append(
            "No quantified achievements found. Employers and ATS systems heavily favour measurable results."
        )

    return min(score, 1.0), suggestions


def score_resume(resume_text: str, job_description: str) -> dict:
    """
    Full ATS scoring:
      - keyword_score  (40%) : matched keywords / total job keywords
      - semantic_score (20%) : TF-IDF cosine similarity
      - format_score   (40%) : format & structure checks

    Returns a dict with ats_score, breakdown, matched/missing keywords, suggestions.
    """
    job_kws    = extract_job_keywords(job_description)
    resume_norm = _normalize(resume_text)

    # Keyword matching
    matched  = [kw for kw in job_kws if kw.lower() in resume_norm]
    missing  = [kw for kw in job_kws if kw.lower() not in resume_norm]
    kw_score = len(matched) / max(len(job_kws), 1)

    # Semantic similarity
    sem_score = resume_job_similarity(resume_text, job_description)

    # Format score
    fmt_score, fmt_suggestions = _format_score(resume_text)

    # Weighted total
    total = round((0.40 * kw_score + 0.20 * sem_score + 0.40 * fmt_score) * 100, 1)

    # Keyword suggestions
    kw_suggestions = []
    if kw_score < 0.60 and missing:
        kw_suggestions.append(
            f"Add these missing keywords from the job description: "
            f"{', '.join(missing[:10])}"
        )
    if kw_score < 0.40:
        kw_suggestions.append(
            "Keyword match is critically low. Rewrite your skills section to mirror "
            "the exact language used in the job posting."
        )

    all_suggestions = kw_suggestions + fmt_suggestions

    # Priority flag
    if total < 50:
        priority = "Critical — Major revision needed"
    elif total < 65:
        priority = "Low — Significant improvements required"
    elif total < 80:
        priority = "Medium — Targeted keyword & format fixes"
    else:
        priority = "High — Minor polish only"

    return {
        "ats_score":         total,
        "priority":          priority,
        "keyword_match_pct": round(kw_score * 100, 1),
        "semantic_score":    round(sem_score * 100, 1),
        "format_score":      round(fmt_score * 100, 1),
        "matched_keywords":  matched,
        "missing_keywords":  missing[:15],
        "total_job_keywords": len(job_kws),
        "matched_count":     len(matched),
        "word_count":        _count_words(resume_text),
        "bullet_count":      _count_bullets(resume_text),
        "metric_count":      _count_metrics(resume_text),
        "contact_info":      _detect_contact_info(resume_text),
        "suggestions":       all_suggestions,
    }


def print_ats_report(result: dict):
    score = result["ats_score"]
    color_label = (
        "EXCELLENT" if score >= 85 else
        "GOOD"      if score >= 70 else
        "FAIR"      if score >= 55 else "POOR"
    )
    print("\n" + "="*60)
    print("  ATS SCORE REPORT")
    print("="*60)
    print(f"  Overall ATS Score  : {score:.1f}% — {color_label}")
    print(f"  Priority Level     : {result['priority']}")
    print(f"  Keyword Match      : {result['keyword_match_pct']}%  ({result['matched_count']}/{result['total_job_keywords']} keywords)")
    print(f"  Semantic Similarity: {result['semantic_score']}%")
    print(f"  Format Score       : {result['format_score']}%")
    print(f"  Word Count         : {result['word_count']}")
    print(f"  Bullet Points      : {result['bullet_count']}")
    print(f"  Quantified Metrics : {result['metric_count']}")

    contact = result.get("contact_info", {})
    print(f"  Contact Info       : Email={'✓' if contact.get('email') else '✗'}  Phone={'✓' if contact.get('phone') else '✗'}  LinkedIn={'✓' if contact.get('linkedin') else '✗'}")

    if result["matched_keywords"]:
        print(f"\n  MATCHED KEYWORDS   : {', '.join(result['matched_keywords'][:10])}")
    if result["missing_keywords"]:
        print(f"  MISSING KEYWORDS   : {', '.join(result['missing_keywords'][:10])}")

    if result["suggestions"]:
        print("\n  IMPROVEMENT SUGGESTIONS:")
        for i, s in enumerate(result["suggestions"], 1):
            print(f"  {i}. {s}")
    print("="*60)
