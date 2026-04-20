"""tone_analyzer.py — Resume tone analysis + improvement suggestions using NLP"""
import re
from textblob import TextBlob

# Passive-voice pattern (basic heuristic)
_PASSIVE_RE = re.compile(
    r'\b(was|were|is|are|been|being|be)\s+\w+ed\b', re.IGNORECASE
)

# Weak / filler words that reduce professional tone
_WEAK_WORDS = {
    "helped", "assisted", "tried", "attempted", "sort of", "kind of",
    "basically", "actually", "very", "really", "just", "maybe", "perhaps",
    "things", "stuff", "various", "a number of", "many different",
}

# Strong action verbs that signal professional tone
_STRONG_VERBS = {
    "achieved", "accelerated", "built", "championed", "delivered", "designed",
    "developed", "directed", "drove", "engineered", "executed", "generated",
    "implemented", "improved", "increased", "launched", "led", "managed",
    "optimized", "oversaw", "produced", "reduced", "resolved", "spearheaded",
    "streamlined", "transformed", "exceeded",
}

# Overly formal / robotic phrases to flag
_ROBOTIC_PHRASES = [
    "utilized", "leveraged synergies", "paradigm shift", "going forward",
    "at the end of the day", "circle back", "touch base", "deep dive",
    "bandwidth", "move the needle", "low-hanging fruit", "best-of-breed",
]

# Quantifier patterns — rewards concrete metrics
_METRIC_RE = re.compile(r'\b\d+[\.,]?\d*\s*(%|percent|million|thousand|k\b|\$|hours?|days?|weeks?|months?|years?)\b', re.IGNORECASE)


def analyze_tone(text: str) -> dict:
    """
    Return a tone report with:
      - overall_score (0-100)
      - sentiment (polarity / subjectivity)
      - tone_label
      - passive_count
      - weak_word_hits
      - strong_verb_count
      - metric_count
      - suggestions list
    """
    blob = TextBlob(text)
    polarity    = blob.sentiment.polarity      # -1 .. 1
    subjectivity = blob.sentiment.subjectivity # 0 .. 1

    words_lower = text.lower().split()
    sentences   = [str(s) for s in blob.sentences]

    # Passive voice
    passive_matches = _PASSIVE_RE.findall(text)
    passive_count   = len(passive_matches)

    # Weak words
    weak_hits = [w for w in _WEAK_WORDS if w in text.lower()]

    # Strong verbs
    strong_count = sum(1 for w in words_lower if w.rstrip(".,;:") in _STRONG_VERBS)

    # Robotic phrases
    robotic_hits = [p for p in _ROBOTIC_PHRASES if p in text.lower()]

    # Quantified achievements
    metric_count = len(_METRIC_RE.findall(text))

    # ── Scoring ───────────────────────────────────────────────────────────────
    score = 50

    # Reward strong action verbs (up to +20)
    score += min(strong_count * 3, 20)

    # Reward concrete metrics (up to +15)
    score += min(metric_count * 3, 15)

    # Penalise passive voice
    score -= min(passive_count * 4, 20)

    # Penalise weak/filler words
    score -= min(len(weak_hits) * 3, 15)

    # Penalise robotic phrases
    score -= min(len(robotic_hits) * 5, 15)

    # Sentiment band: professional tone is slightly positive & low subjectivity
    if 0.05 <= polarity <= 0.6 and subjectivity <= 0.5:
        score += 10
    elif polarity < 0:
        score -= 10

    score = max(0, min(100, round(score)))

    # ── Tone label ────────────────────────────────────────────────────────────
    if score >= 80:
        tone_label = "Professional & Confident"
    elif score >= 65:
        tone_label = "Moderately Professional"
    elif score >= 50:
        tone_label = "Neutral / Needs Strengthening"
    else:
        tone_label = "Weak / Passive — Needs Rewriting"

    # ── Suggestions ──────────────────────────────────────────────────────────
    suggestions = []

    if passive_count > 2:
        suggestions.append(
            f"Reduce passive voice ({passive_count} instances). "
            "Start bullets with strong action verbs like 'Led', 'Engineered', 'Delivered'."
        )

    if weak_hits:
        suggestions.append(
            f"Replace weak/filler words: {', '.join(weak_hits[:5])}. "
            "Use specific, impact-driven language instead."
        )

    if strong_count < 4:
        suggestions.append(
            "Add more strong action verbs: Spearheaded, Optimized, Accelerated, Championed, Streamlined."
        )

    if metric_count < 3:
        suggestions.append(
            "Include at least 3–5 quantified achievements (%, $, headcount, time saved) "
            "to make impact concrete and ATS-friendly."
        )

    if robotic_hits:
        suggestions.append(
            f"Remove corporate jargon: {', '.join(robotic_hits[:3])}. "
            "Use plain, direct language."
        )

    if subjectivity > 0.6:
        suggestions.append(
            "Tone is too subjective/opinionated. Focus on verifiable facts and results."
        )

    if polarity < 0.05:
        suggestions.append(
            "Tone feels flat or slightly negative. Highlight achievements and positive outcomes."
        )

    if not suggestions:
        suggestions.append("Tone is strong. Minor refinements may further elevate impact.")

    return {
        "overall_score":  score,
        "tone_label":     tone_label,
        "polarity":       round(polarity, 3),
        "subjectivity":   round(subjectivity, 3),
        "passive_count":  passive_count,
        "weak_word_hits": weak_hits,
        "strong_verb_count": strong_count,
        "metric_count":   metric_count,
        "robotic_phrases": robotic_hits,
        "suggestions":    suggestions,
    }


def improve_tone(text: str) -> str:
    """Apply basic automatic tone improvements: strip weak filler words."""
    improved = text
    replacements = {
        r'\bhelped\b':     "supported",
        r'\bassisted\b':   "contributed to",
        r'\btried\b':      "worked to",
        r'\bvery\b':       "",
        r'\breally\b':     "",
        r'\bjust\b':       "",
        r'\butilized\b':   "used",
        r'\bleveraged\b':  "applied",
        r'\bbasically\b':  "",
        r'\bactually\b':   "",
        r'\bthings\b':     "processes",
        r'\bstuff\b':      "materials",
    }
    for pattern, replacement in replacements.items():
        improved = re.sub(pattern, replacement, improved, flags=re.IGNORECASE)
    # Clean up double spaces from removed words
    improved = re.sub(r'  +', ' ', improved)
    improved = re.sub(r' ,', ',', improved)
    improved = re.sub(r' \.', '.', improved)
    return improved.strip()


def print_tone_report(report: dict):
    print("\n" + "="*55)
    print("  TONE ANALYSIS REPORT")
    print("="*55)
    print(f"  Overall Tone Score : {report['overall_score']}/100")
    print(f"  Tone Label         : {report['tone_label']}")
    print(f"  Sentiment Polarity : {report['polarity']} (positive > 0)")
    print(f"  Subjectivity       : {report['subjectivity']} (objective < 0.5)")
    print(f"  Passive Voice Uses : {report['passive_count']}")
    print(f"  Strong Verbs Found : {report['strong_verb_count']}")
    print(f"  Quantified Metrics : {report['metric_count']}")
    if report['weak_word_hits']:
        print(f"  Weak Words Found   : {', '.join(report['weak_word_hits'][:6])}")
    if report['robotic_phrases']:
        print(f"  Jargon Flagged     : {', '.join(report['robotic_phrases'][:4])}")
    print("\n  SUGGESTIONS:")
    for i, s in enumerate(report['suggestions'], 1):
        print(f"  {i}. {s}")
    print("="*55)
