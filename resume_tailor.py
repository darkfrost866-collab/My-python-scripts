"""resume_tailor.py — Tailored resume generation with keyword insertion + section scoring"""
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from nlp_engine import extract_job_keywords, score_resume_sections
except Exception:
    def extract_job_keywords(jd, top_n=30): return []
    def score_resume_sections(r, jd): return {}

try:
    from paraphraser import paraphrase_resume_section
except Exception:
    def paraphrase_resume_section(text, jd=""): return text

try:
    from config import USER_PROFILE_PATH
    _profile = json.loads(Path(USER_PROFILE_PATH).read_text(encoding="utf-8")) if Path(USER_PROFILE_PATH).exists() else {}
except Exception:
    _profile = {}

# ── Keyword insertion helpers ─────────────────────────────────────────────────

def _missing_keywords(resume_text: str, job_description: str) -> list[str]:
    kws = extract_job_keywords(job_description)
    norm = re.sub(r'[^a-z0-9 ]', ' ', resume_text.lower())
    return [kw for kw in kws if kw.lower() not in norm]


def _build_keyword_phrase(keywords: list[str], max_kw: int = 6) -> str:
    """Turn top missing keywords into a natural-sounding skills phrase."""
    kws = [kw.title() for kw in keywords[:max_kw] if len(kw) > 2]
    if not kws:
        return ""
    if len(kws) == 1:
        return kws[0]
    return ", ".join(kws[:-1]) + f", and {kws[-1]}"


# ── Core bullets library ──────────────────────────────────────────────────────

_BASE_BULLETS = [
    "Engineered a 15% improvement in shift effectiveness through disciplined Lean Six Sigma "
    "methodology and systematic root cause analysis across multi-shift operations",
    "Achieved zero Lost Time Injuries over a consecutive 24-month period by championing OHSA "
    "compliance, JHSC safety initiatives, and a culture of proactive hazard identification",
    "Resolved 90% of labour disputes through collaborative engagement, preserving production "
    "continuity and team cohesion for 45+ unionized personnel",
    "Drove 12% waste reduction and supported a $2M capacity expansion through optimized "
    "material procurement and continuous improvement initiatives",
    "Maintained 100% adherence to quality management systems (ISO 9001 / IATF 16949) through "
    "rigorous process auditing and real-time corrective action protocols",
]

_CONDITIONAL_BULLETS = {
    'weld':       "Directed precision welding and fabrication operations as a certified TSSA "
                  "(1G–6G) and CWB Level 2 Welding Inspector, ensuring zero code violations",
    'lean':       "Spearheaded Lean / Kaizen events that reduced changeover time by 20% and "
                  "eliminated $180K in annual scrap costs",
    'iso':        "Championed ISO 9001 / IATF 16949 compliance programs; achieved a 98% "
                  "first-pass audit score across all process checkpoints",
    'automotive': "Managed high-volume automotive assembly lines delivering JIT production with "
                  "a defect rate below 0.3 PPM",
    'aerospace':  "Applied AS9100D aerospace standards in precision-machined sub-assembly "
                  "environments with zero non-conformance reports",
    'six sigma':  "Deployed Six Sigma DMAIC framework on two critical throughput bottlenecks, "
                  "recovering 8% lost capacity",
    'union':      "Fostered transparent communications within a 60+ member unionized workforce, "
                  "reducing grievances by 40% year-over-year",
    'erp':        "Optimized ERP/SAP production scheduling, reducing WIP inventory by 18% while "
                  "maintaining 99.5% on-time delivery",
    'safety':     "Implemented a behaviour-based safety program that cut recordable incidents "
                  "by 35% in the first 12 months",
    'quality':    "Led cross-functional quality circles that identified and eliminated root causes "
                  "of top-5 recurring defects, saving $320K annually",
}


def tailor_resume(job: dict, paraphrase: bool = False) -> str:
    """
    Build a tailored bullet set for the given job.
    Returns a formatted bullet string with job-specific keywords inserted.
    """
    desc = job.get('description', '').lower()
    bullets = list(_BASE_BULLETS)  # copy

    # Add conditional bullets
    for trigger, bullet in _CONDITIONAL_BULLETS.items():
        if trigger in desc and len(bullets) < 8:
            bullets.append(bullet)

    # Insert missing keywords as a skills addendum bullet
    missing = _missing_keywords('\n'.join(bullets), job.get('description', ''))
    if missing:
        kw_phrase = _build_keyword_phrase(missing)
        if kw_phrase:
            bullets.append(
                f"Additional competencies aligned with this role: {kw_phrase}"
            )

    # Cap at 6 bullets for readability
    selected = bullets[:6]
    block = '\n'.join(f"• {b}" for b in selected)

    # Optionally paraphrase to avoid verbatim JD language
    if paraphrase:
        block = paraphrase_resume_section(block, job.get('description', ''))

    return block


def section_relevance_report(resume_text: str, job_description: str) -> dict:
    """
    Return a relevance score (0–100) for each resume section vs. the job description.
    """
    return score_resume_sections(resume_text, job_description)


def generate_cover_letter(company: str, title: str, job_description: str = "") -> str:
    today = datetime.now().strftime('%B %d, %Y')

    # Pull personalisation details from profile if available
    name    = _profile.get('personal', {}).get('name',    'Raouf Mayahi')
    address = _profile.get('personal', {}).get('location','York, Ontario')
    phone   = _profile.get('personal', {}).get('phone',   '(416) 897-7889')
    email   = _profile.get('personal', {}).get('email',   'raoufmayahi@gmail.com')
    linkedin = _profile.get('personal', {}).get('linkedin','linkedin.com/in/raoufmayahi')

    # Extract top keywords from job description for a personalised paragraph
    kw_list = extract_job_keywords(job_description)[:8] if job_description else []
    kw_sentence = ""
    if kw_list:
        kw_phrase = ", ".join(kw_list[:5])
        kw_sentence = (
            f"Your posting specifically highlights {kw_phrase}, "
            "areas where my hands-on record of achievement is directly transferable."
        )

    return f"""{name}
{address}
{phone} | {email} | {linkedin}

{today}

Hiring Manager
{company}
Ontario, Canada

Dear Hiring Manager,

RE: Application for {title} Position

I am writing to express my strong interest in the {title} position at {company}. With over \
14 years of progressive leadership experience in heavy manufacturing, custom fabrication, and \
high-precision assembly operations, I offer a proven track record of driving operational \
excellence, cultivating safety-first cultures, and delivering quantifiable productivity \
improvements in unionized environments.{' ' + kw_sentence if kw_sentence else ''}

In my current capacity as Production Supervisor at Active Dynamics, I provide strategic \
leadership to a team of 45+ unionized professionals across multi-shift manufacturing operations. \
Through the disciplined application of Lean Six Sigma principles and comprehensive root cause \
analysis, I successfully engineered a 15% improvement in shift effectiveness while simultaneously \
achieving zero Lost Time Injuries over a consecutive 24-month period — underscoring my commitment \
to balancing productivity objectives with uncompromising safety standards.

My approach to labour relations has been instrumental in maintaining operational stability. By \
fostering transparent communication and implementing collaborative problem-solving frameworks, I \
have resolved 90% of labour disputes at the supervisory level, preserving production schedules \
and enhancing team cohesion.

My technical qualifications include TSSA certification (1G through 6G), CWB Level 2 Welding \
Inspector, Lean Six Sigma Green Belt, and extensive experience with ISO 9001, IATF 16949, and \
AS9100 quality management systems. At Howden Canada I maintained 100% quality compliance while \
supporting a 12% facility capacity expansion through optimized material procurement and waste \
reduction initiatives.

{company}'s reputation for manufacturing excellence aligns directly with my professional philosophy. \
I am confident my combination of technical expertise, proven leadership, and dedication to \
operational excellence would make me a valuable addition to your team. I would welcome the \
opportunity to discuss how my background can support {company}'s strategic goals.

Thank you for your time and consideration. I look forward to speaking with you soon.

Sincerely,

{name}

Enclosures: Resume
"""


def full_resume_text(job: dict, bullets: str) -> str:
    """
    Assemble the complete resume as plain text (used for ATS scoring & history).
    """
    p = _profile.get('personal', {})
    name     = p.get('name',     'Raouf Mayahi')
    title_ln = p.get('title',    'Production Supervisor | Operations Leader')
    location = p.get('location', 'York, Ontario')
    phone    = p.get('phone',    '(416) 897-7889')
    email_ad = p.get('email',    'raoufmayahi@gmail.com')
    linkedin = p.get('linkedin', 'linkedin.com/in/raoufmayahi')

    summary = _profile.get('summary', '')

    skills = _profile.get('skills', {})
    all_skills = []
    for group in skills.values():
        all_skills.extend(group)

    certs = _profile.get('certifications', [])

    exp_block = ""
    for exp in _profile.get('experience', []):
        exp_block += (
            f"\n{exp.get('company','').upper()} | {exp.get('title','')} | "
            f"{exp.get('start','')} – {exp.get('end','')}\n"
        )
        for b in exp.get('bullets', []):
            exp_block += f"• {b}\n"

    edu_block = ""
    for edu in _profile.get('education', []):
        edu_block += f"• {edu.get('degree','')} — {edu.get('institution','')} ({edu.get('year','')})\n"

    return f"""{name}
{title_ln}
{location} | {phone} | {email_ad} | {linkedin}

TARGET POSITION: {job.get('title','').upper()}

PROFESSIONAL SUMMARY
{summary}

CORE COMPETENCIES
{chr(10).join('• ' + s for s in all_skills[:12])}

KEY ACHIEVEMENTS
{bullets}

PROFESSIONAL EXPERIENCE
{exp_block}
EDUCATION & CERTIFICATIONS
{edu_block}
{chr(10).join('• ' + c for c in certs)}
"""
