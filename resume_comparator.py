"""resume_comparator.py — Side-by-side resume comparison with ATS diff"""
import re
from difflib import SequenceMatcher, unified_diff


def _normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def _word_set(text: str) -> set:
    return set(_normalize(text).split())


def _count_sections(text: str) -> dict:
    found = {}
    section_names = [
        "summary", "experience", "skills", "education",
        "certifications", "achievements", "competencies",
        "objective", "projects",
    ]
    lower = text.lower()
    for s in section_names:
        found[s] = s in lower
    return found


def _extract_metrics(text: str) -> list:
    pattern = re.compile(
        r'\b\d+[\.,]?\d*\s*(%|percent|million|thousand|k\b|\$|hours?|days?|weeks?|months?|years?)\b',
        re.IGNORECASE,
    )
    return pattern.findall(text)


def _sentence_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def compare_resumes(resume_a: str, resume_b: str,
                    label_a: str = "Resume A", label_b: str = "Resume B",
                    ats_score_a: float = None, ats_score_b: float = None) -> dict:
    """
    Compare two resume texts and return a detailed diff report.
    """
    words_a = _word_set(resume_a)
    words_b = _word_set(resume_b)

    shared          = words_a & words_b
    unique_to_a     = words_a - words_b
    unique_to_b     = words_b - words_a
    similarity      = round(len(shared) / max(len(words_a | words_b), 1) * 100, 1)
    content_overlap = round(_sentence_similarity(resume_a, resume_b) * 100, 1)

    sections_a = _count_sections(resume_a)
    sections_b = _count_sections(resume_b)

    metrics_a = _extract_metrics(resume_a)
    metrics_b = _extract_metrics(resume_b)

    word_count_a = len(resume_a.split())
    word_count_b = len(resume_b.split())

    # Section diff
    section_diff = {}
    for s in sections_a:
        section_diff[s] = {
            label_a: sections_a[s],
            label_b: sections_b.get(s, False),
        }

    # Unique strong words (not filler)
    _STOP = {"the","a","an","in","of","to","and","for","with","on","at","by",
              "is","are","was","were","be","been","has","have","had","that",
              "this","it","as","or","not","from","they","we","you","i"}
    meaningful_a = {w for w in unique_to_a if len(w) > 3 and w not in _STOP}
    meaningful_b = {w for w in unique_to_b if len(w) > 3 and w not in _STOP}

    return {
        "label_a":         label_a,
        "label_b":         label_b,
        "ats_score_a":     ats_score_a,
        "ats_score_b":     ats_score_b,
        "word_count_a":    word_count_a,
        "word_count_b":    word_count_b,
        "word_similarity": similarity,
        "content_overlap": content_overlap,
        "shared_keywords": sorted(shared)[:30],
        "unique_to_a":     sorted(meaningful_a)[:20],
        "unique_to_b":     sorted(meaningful_b)[:20],
        "metric_count_a":  len(metrics_a),
        "metric_count_b":  len(metrics_b),
        "sections":        section_diff,
        "recommendation":  _recommend(
            similarity, ats_score_a, ats_score_b,
            len(metrics_a), len(metrics_b), label_a, label_b,
        ),
    }


def _recommend(similarity, score_a, score_b, metrics_a, metrics_b, la, lb) -> str:
    lines = []
    if score_a is not None and score_b is not None:
        winner = la if score_a >= score_b else lb
        lines.append(f"{winner} scores higher on ATS ({max(score_a, score_b):.1f}%). Use it as your base.")
    if similarity > 85:
        lines.append("The two resumes are very similar. Differentiate with unique keywords per job.")
    elif similarity < 40:
        lines.append("Large content divergence — ensure both cover the same core competencies.")
    if metrics_a > metrics_b:
        lines.append(f"{la} has more quantified metrics ({metrics_a} vs {metrics_b}). Carry those into {lb}.")
    elif metrics_b > metrics_a:
        lines.append(f"{lb} has more quantified metrics ({metrics_b} vs {metrics_a}). Carry those into {la}.")
    if not lines:
        lines.append("Resumes are well-balanced. Fine-tune keywords per job posting for best ATS results.")
    return " ".join(lines)


def print_comparison(report: dict):
    la, lb = report["label_a"], report["label_b"]
    print("\n" + "="*65)
    print("  RESUME COMPARISON REPORT")
    print("="*65)

    # ATS scores
    if report["ats_score_a"] is not None:
        print(f"  ATS Score  — {la:20}: {report['ats_score_a']}%")
        print(f"  ATS Score  — {lb:20}: {report['ats_score_b']}%")
        print()

    # Word counts
    print(f"  Word Count — {la:20}: {report['word_count_a']} words")
    print(f"  Word Count — {lb:20}: {report['word_count_b']} words")
    print(f"  Keyword Similarity          : {report['word_similarity']}%")
    print(f"  Content Overlap (sentences) : {report['content_overlap']}%")
    print(f"  Quantified Metrics — {la[:10]:10}: {report['metric_count_a']}")
    print(f"  Quantified Metrics — {lb[:10]:10}: {report['metric_count_b']}")

    # Section coverage
    print("\n  SECTION COVERAGE:")
    for section, vals in report["sections"].items():
        a_sym = "✓" if vals.get(la) else "✗"
        b_sym = "✓" if vals.get(lb) else "✗"
        print(f"    {section:18} {la[:12]:12}:{a_sym}  {lb[:12]:12}:{b_sym}")

    # Unique keywords
    if report["unique_to_a"]:
        print(f"\n  KEYWORDS ONLY IN {la[:20]}:")
        print(f"    {', '.join(report['unique_to_a'][:15])}")
    if report["unique_to_b"]:
        print(f"\n  KEYWORDS ONLY IN {lb[:20]}:")
        print(f"    {', '.join(report['unique_to_b'][:15])}")

    print(f"\n  RECOMMENDATION:")
    print(f"    {report['recommendation']}")
    print("="*65)


def export_comparison_html(report: dict, output_path: str):
    """Export the comparison as a simple HTML file."""
    la, lb = report["label_a"], report["label_b"]

    def _score_badge(score):
        if score is None:
            return "N/A"
        color = "#27ae60" if score >= 85 else "#f39c12" if score >= 70 else "#e74c3c"
        return f'<span style="color:{color};font-weight:bold">{score}%</span>'

    section_rows = ""
    for sec, vals in report["sections"].items():
        a = "✓" if vals.get(la) else "✗"
        b = "✓" if vals.get(lb) else "✗"
        color_a = "#27ae60" if a == "✓" else "#e74c3c"
        color_b = "#27ae60" if b == "✓" else "#e74c3c"
        section_rows += (
            f"<tr><td>{sec.title()}</td>"
            f"<td style='color:{color_a};text-align:center'>{a}</td>"
            f"<td style='color:{color_b};text-align:center'>{b}</td></tr>"
        )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Resume Comparison — {la} vs {lb}</title>
<style>
  body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;color:#333}}
  h1{{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0}}
  .card{{background:#f9f9f9;border:1px solid #ddd;border-radius:6px;padding:20px}}
  .card h3{{margin-top:0;color:#2c3e50}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#2c3e50;color:white;padding:10px}}
  td{{padding:8px;border-bottom:1px solid #eee}}
  .rec{{background:#eaf4fb;border-left:4px solid #3498db;padding:15px;border-radius:4px}}
  .kw{{font-size:0.85em;background:#ecf0f1;padding:3px 7px;border-radius:10px;margin:2px;display:inline-block}}
</style>
</head><body>
<h1>Resume Comparison Report</h1>

<div class="grid">
  <div class="card">
    <h3>{la}</h3>
    <p>ATS Score: {_score_badge(report['ats_score_a'])}</p>
    <p>Word Count: <strong>{report['word_count_a']}</strong></p>
    <p>Quantified Metrics: <strong>{report['metric_count_a']}</strong></p>
  </div>
  <div class="card">
    <h3>{lb}</h3>
    <p>ATS Score: {_score_badge(report['ats_score_b'])}</p>
    <p>Word Count: <strong>{report['word_count_b']}</strong></p>
    <p>Quantified Metrics: <strong>{report['metric_count_b']}</strong></p>
  </div>
</div>

<h2>Overall Similarity</h2>
<p>Keyword similarity: <strong>{report['word_similarity']}%</strong> &nbsp;|&nbsp;
   Content overlap: <strong>{report['content_overlap']}%</strong></p>

<h2>Section Coverage</h2>
<table>
  <tr><th>Section</th><th>{la}</th><th>{lb}</th></tr>
  {section_rows}
</table>

<h2>Unique Keywords</h2>
<div class="grid">
  <div>
    <strong>Only in {la}:</strong><br>
    {''.join(f'<span class="kw">{w}</span>' for w in report['unique_to_a'][:15])}
  </div>
  <div>
    <strong>Only in {lb}:</strong><br>
    {''.join(f'<span class="kw">{w}</span>' for w in report['unique_to_b'][:15])}
  </div>
</div>

<h2>Recommendation</h2>
<div class="rec">{report['recommendation']}</div>

</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Comparison saved → {output_path}")
