"""paraphraser.py — NLP-based resume paraphrasing without copying job-description wording"""
import re
import random

# ── Synonym map for common resume / job-description words ────────────────────
_SYNONYMS: dict[str, list[str]] = {
    # leadership / management
    "led":            ["directed", "oversaw", "spearheaded", "championed"],
    "managed":        ["administered", "supervised", "coordinated", "orchestrated"],
    "supervised":     ["oversaw", "directed", "monitored", "guided"],
    "directed":       ["led", "coordinated", "steered", "governed"],
    "oversaw":        ["supervised", "managed", "administered", "monitored"],
    "coordinated":    ["organized", "aligned", "orchestrated", "facilitated"],
    # improvement / change
    "improved":       ["enhanced", "elevated", "optimized", "strengthened"],
    "increased":      ["boosted", "accelerated", "expanded", "grew"],
    "reduced":        ["minimized", "decreased", "cut", "lowered"],
    "optimized":      ["streamlined", "refined", "enhanced", "improved"],
    "streamlined":    ["simplified", "optimized", "restructured", "modernized"],
    "developed":      ["built", "crafted", "established", "engineered"],
    "implemented":    ["deployed", "executed", "introduced", "rolled out"],
    "created":        ["designed", "built", "developed", "established"],
    "designed":       ["architected", "crafted", "developed", "engineered"],
    "built":          ["constructed", "developed", "established", "created"],
    # achievement / delivery
    "achieved":       ["attained", "delivered", "accomplished", "secured"],
    "delivered":      ["executed", "completed", "produced", "accomplished"],
    "exceeded":       ["surpassed", "outperformed", "eclipsed"],
    "ensured":        ["guaranteed", "maintained", "upheld", "secured"],
    "maintained":     ["sustained", "preserved", "upheld", "retained"],
    # analysis / problem solving
    "analyzed":       ["assessed", "evaluated", "examined", "investigated"],
    "resolved":       ["addressed", "rectified", "eliminated", "corrected"],
    "identified":     ["pinpointed", "discovered", "recognized", "detected"],
    "evaluated":      ["assessed", "reviewed", "appraised", "examined"],
    # collaboration / support
    "collaborated":   ["partnered", "worked", "cooperated", "engaged"],
    "supported":      ["assisted", "aided", "contributed to", "facilitated"],
    "trained":        ["mentored", "coached", "developed", "guided"],
    "mentored":       ["coached", "guided", "trained", "developed"],
    # common adjectives
    "effective":      ["impactful", "efficient", "productive", "robust"],
    "significant":    ["substantial", "considerable", "notable", "marked"],
    "successful":     ["effective", "productive", "accomplishing", "winning"],
    "responsible":    ["accountable", "tasked", "entrusted"],
    "key":            ["critical", "pivotal", "central", "core"],
    "strong":         ["robust", "solid", "rigorous", "effective"],
    # operations
    "utilized":       ["applied", "used", "employed", "leveraged"],
    "leveraged":      ["applied", "harnessed", "employed", "used"],
    "executed":       ["carried out", "performed", "completed", "conducted"],
    "conducted":      ["performed", "executed", "carried out", "ran"],
    "monitored":      ["tracked", "observed", "measured", "reviewed"],
    "reported":       ["presented", "communicated", "documented", "submitted"],
}

# Phrases that should NOT be copied verbatim from a job description
_PHRASES_TO_REPHRASE = [
    (r"must have experience in",        "experience required in"),
    (r"responsible for",                "tasked with"),
    (r"you will be",                    "the role involves"),
    (r"we are looking for",             "ideal candidate brings"),
    (r"the ideal candidate",            "top performers"),
    (r"strong communication skills",    "clear cross-functional communication"),
    (r"attention to detail",            "precision and quality focus"),
    (r"fast-paced environment",         "high-velocity operations"),
    (r"team player",                    "collaborative contributor"),
    (r"self-starter",                   "proactive and self-directed"),
    (r"results[-\s]driven",             "outcome-focused"),
    (r"proven track record",            "demonstrated history of"),
    (r"ability to",                     "demonstrated capacity to"),
    (r"work independently",             "operate autonomously"),
    (r"excellent interpersonal skills", "strong stakeholder engagement"),
]


def _replace_word(word: str) -> str:
    """Return a synonym for word if available, preserving capitalisation."""
    clean = word.strip(".,;:!?\"'()-").lower()
    if clean not in _SYNONYMS:
        return word
    synonym = random.choice(_SYNONYMS[clean])
    # Preserve leading capitalisation
    if word[0].isupper():
        synonym = synonym[0].upper() + synonym[1:]
    return synonym


def paraphrase_sentence(sentence: str, strength: float = 0.5) -> str:
    """
    Paraphrase a single sentence.
    strength=0.5 means ~50% chance each synonymisable word is swapped.
    """
    # First apply phrase-level rewrites
    result = sentence
    for pattern, replacement in _PHRASES_TO_REPHRASE:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Then word-level synonym substitution
    tokens = result.split()
    new_tokens = []
    for token in tokens:
        if random.random() < strength:
            new_tokens.append(_replace_word(token))
        else:
            new_tokens.append(token)
    return " ".join(new_tokens)


def paraphrase_bullets(text: str, strength: float = 0.45) -> str:
    """
    Paraphrase a block of resume bullet points.
    Returns the rewritten block.
    """
    lines = text.split("\n")
    rewritten = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            rewritten.append(line)
            continue
        # Preserve bullet marker
        marker = ""
        body   = stripped
        if stripped.startswith(("•", "-", "*", "·")):
            marker = stripped[0] + " "
            body   = stripped[1:].strip()

        new_body = paraphrase_sentence(body, strength=strength)
        rewritten.append(marker + new_body if marker else new_body)
    return "\n".join(rewritten)


def paraphrase_resume_section(section_text: str, job_description: str = "") -> str:
    """
    Paraphrase a resume section, also avoiding exact phrases from job_description.
    Extra protection: if any sentence shares a 5-word sequence with the JD, force
    paraphrase of that sentence at higher strength.
    """
    if not job_description:
        return paraphrase_bullets(section_text)

    jd_lower = job_description.lower()

    def _jd_overlap(sentence: str) -> bool:
        words = sentence.lower().split()
        for i in range(len(words) - 4):
            seq = " ".join(words[i:i+5])
            if seq in jd_lower:
                return True
        return False

    lines = section_text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        marker   = ""
        body     = stripped
        if stripped.startswith(("•", "-", "*", "·")):
            marker = stripped[0] + " "
            body   = stripped[1:].strip()
        strength = 0.75 if _jd_overlap(body) else 0.40
        new_body = paraphrase_sentence(body, strength=strength)
        result.append(marker + new_body if marker else new_body)
    return "\n".join(result)


def show_diff(original: str, paraphrased: str):
    """Print a simple side-by-side diff of original vs paraphrased."""
    orig_lines = original.split("\n")
    para_lines = paraphrased.split("\n")
    print("\n" + "="*70)
    print("  PARAPHRASE COMPARISON")
    print("="*70)
    for i, (o, p) in enumerate(zip(orig_lines, para_lines), 1):
        if o.strip() != p.strip():
            print(f"  [{i}] ORIGINAL  : {o.strip()}")
            print(f"      REWRITTEN : {p.strip()}")
            print()
    print("="*70)
