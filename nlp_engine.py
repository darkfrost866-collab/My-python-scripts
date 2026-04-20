"""nlp_engine.py — Advanced NLP: entity recognition, sentiment, topic modelling, TF-IDF"""
import re
from collections import Counter

from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

# ── Domain keyword bank (fallback when spaCy is unavailable) ─────────────────
_DOMAIN_KEYWORDS = {
    "certifications": {
        "tssa", "cwb", "iso", "iatf", "as9100", "lean", "six sigma", "pmp",
        "cpa", "jhsc", "whmis", "ohsa",
    },
    "skills": {
        "lean", "kaizen", "5s", "root cause", "erp", "sap", "kpi", "mrp",
        "autocad", "solidworks", "six sigma", "scrum", "agile",
    },
    "job_titles": {
        "supervisor", "manager", "director", "lead", "engineer", "analyst",
        "coordinator", "specialist", "technician", "inspector", "operator",
    },
    "industries": {
        "automotive", "aerospace", "manufacturing", "fabrication", "welding",
        "logistics", "pharmaceutical", "food", "electronics",
    },
}

_STOP_WORDS_EXTRA = {
    "must", "will", "role", "work", "team", "year", "day", "able", "new",
    "provide", "ensure", "include", "require", "strong", "excellent",
    "looking", "preferred", "experience", "candidates", "please", "apply",
}


# ── Named Entity Recognition ──────────────────────────────────────────────────

def extract_entities(text: str) -> list[tuple[str, str]]:
    """Return list of (entity_text, entity_label) using spaCy NER."""
    if not nlp:
        return _fallback_entities(text)
    doc = nlp(text[:50000])
    seen = set()
    entities = []
    for ent in doc.ents:
        key = (ent.text.lower(), ent.label_)
        if key not in seen:
            seen.add(key)
            entities.append((ent.text, ent.label_))
    return entities


def _fallback_entities(text: str) -> list[tuple[str, str]]:
    """Simple regex fallback when spaCy is unavailable."""
    entities = []
    for label, kws in _DOMAIN_KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                entities.append((kw, label.upper()))
    return entities


def extract_org_entities(text: str) -> list[str]:
    """Return company / organisation names from text."""
    return [t for t, l in extract_entities(text) if l in ("ORG", "COMPANY")]


def extract_skill_entities(text: str) -> list[str]:
    """Return skills, certifications, and product names from text."""
    skill_labels = {"ORG", "PRODUCT", "WORK_OF_ART", "SKILLS", "CERTIFICATIONS"}
    return [t for t, l in extract_entities(text) if l in skill_labels]


# ── Sentiment Analysis ────────────────────────────────────────────────────────

def sentiment(text: str) -> dict:
    blob = TextBlob(text)
    pol  = blob.sentiment.polarity
    subj = blob.sentiment.subjectivity
    if pol > 0.3:
        label = "Positive"
    elif pol < -0.1:
        label = "Negative"
    else:
        label = "Neutral"
    return {
        "polarity":     round(pol, 3),
        "subjectivity": round(subj, 3),
        "label":        label,
    }


def sentence_sentiments(text: str) -> list[dict]:
    """Sentence-level sentiment breakdown."""
    blob = TextBlob(text)
    return [
        {
            "sentence":   str(s),
            "polarity":   round(s.sentiment.polarity, 3),
            "subjectivity": round(s.sentiment.subjectivity, 3),
        }
        for s in blob.sentences
    ]


# ── TF-IDF Keyword Extraction ─────────────────────────────────────────────────

def keywords_tfidf(text: str, top_n: int = 20) -> list[tuple[str, float]]:
    """Extract top TF-IDF keywords from a single document."""
    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=200,
        token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z0-9\-]{2,}\b',
    )
    try:
        X = vec.fit_transform([text])
        scores = zip(vec.get_feature_names_out(), X.toarray()[0])
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
    except Exception:
        return []


# ── Topic Modelling (LDA) ─────────────────────────────────────────────────────

def topic_model(docs: list[str], n_topics: int = 3,
                top_words: int = 8) -> list[list[str]]:
    """Run LDA and return top words per topic."""
    if len(docs) < 2:
        return []
    vec = CountVectorizer(
        stop_words="english",
        max_df=0.9,
        min_df=1,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z0-9\-]{2,}\b',
    )
    try:
        X = vec.fit_transform(docs)
        lda = LatentDirichletAllocation(
            n_components=n_topics, random_state=42, max_iter=20
        )
        lda.fit(X)
        feature_names = vec.get_feature_names_out()
        topics = []
        for topic in lda.components_:
            top_idx = topic.argsort()[: -top_words - 1: -1]
            topics.append([feature_names[i] for i in top_idx])
        return topics
    except Exception:
        return []


# ── Semantic Similarity ───────────────────────────────────────────────────────

def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using TF-IDF vectors.
    Returns a value between 0 and 1.
    """
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vec.fit_transform([text_a, text_b])
        sim = cosine_similarity(matrix[0], matrix[1])[0][0]
        return round(float(sim), 3)
    except Exception:
        return 0.0


def resume_job_similarity(resume_text: str, job_description: str) -> float:
    return semantic_similarity(resume_text, job_description)


# ── Keyword extraction for ATS ────────────────────────────────────────────────

def extract_job_keywords(job_description: str, top_n: int = 30) -> list[str]:
    """
    Unified keyword extractor: combines entity-based and TF-IDF keywords.
    Returns a deduplicated list of relevant keywords for ATS matching.
    """
    entities = extract_entities(job_description)
    entity_kws = [
        t for t, l in entities
        if l in ("ORG", "PRODUCT", "WORK_OF_ART", "SKILLS", "CERTIFICATIONS",
                 "SKILLS", "GPE", "NORP")
        and len(t) > 2
    ]

    tfidf_kws = [w for w, s in keywords_tfidf(job_description, top_n=40) if s > 0.05]

    # Domain keyword hits
    jd_lower = job_description.lower()
    domain_kws = []
    for group in _DOMAIN_KEYWORDS.values():
        for kw in group:
            if kw in jd_lower:
                domain_kws.append(kw)

    combined = list(dict.fromkeys(entity_kws + tfidf_kws + domain_kws))

    # Remove generic stop words
    filtered = [
        kw for kw in combined
        if kw.lower() not in _STOP_WORDS_EXTRA and len(kw) > 2
    ]
    return filtered[:top_n]


# ── Section relevance scoring ─────────────────────────────────────────────────

def score_resume_sections(resume_text: str, job_description: str) -> dict:
    """
    Split resume into sections and score each one's relevance to the job.
    Returns {section_name: relevance_score (0-100)}.
    """
    section_pattern = re.compile(
        r'(SUMMARY|EXPERIENCE|SKILLS|EDUCATION|CERTIFICATIONS?|'
        r'COMPETENCIES|ACHIEVEMENTS?|PROJECTS?|OBJECTIVE)',
        re.IGNORECASE,
    )
    parts = section_pattern.split(resume_text)
    sections = {}

    current_name = "header"
    for part in parts:
        if section_pattern.match(part):
            current_name = part.strip().lower()
        else:
            if current_name not in sections:
                sections[current_name] = ""
            sections[current_name] += part

    scored = {}
    for name, content in sections.items():
        if len(content.split()) < 5:
            continue
        sim = resume_job_similarity(content, job_description)
        scored[name] = round(sim * 100, 1)

    return scored


def print_section_scores(scores: dict):
    print("\n  RESUME SECTION RELEVANCE SCORES:")
    for section, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score / 5)
        print(f"    {section.title():20}: {score:5.1f}%  {bar}")
