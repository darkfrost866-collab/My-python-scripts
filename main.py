"""main.py — Job-AI Resume Optimizer — Interactive CLI"""
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

# ── Imports ────────────────────────────────────────────────────────────────────
from job_fetcher   import fetch_all, filter_jobs, search_jobs
from resume_tailor import tailor_resume, generate_cover_letter, full_resume_text
from pdf_generator import (
    create_resume_pdf, create_resume_docx,
    create_cover_pdf, create_cover_docx,
)
from ats_scorer     import score_resume, print_ats_report
from nlp_engine     import (
    extract_entities, sentiment, topic_model,
    keywords_tfidf, print_section_scores,
    score_resume_sections,
)
from tone_analyzer  import analyze_tone, improve_tone, print_tone_report
from paraphraser    import paraphrase_resume_section, show_diff
from resume_comparator import compare_resumes, print_comparison, export_comparison_html
from resume_history    import (
    save_resume, list_history, search_history,
    print_history, export_history_html, export_history_csv,
)
from email_bot     import send_job_digest, send_resume_ready, send_applied_confirmation
from gmail_manager import create_labels, store_jobs_in_gmail, store_resume_in_gmail

try:
    from config import OUTPUT_BASE_DIR
except Exception:
    OUTPUT_BASE_DIR = Path.home() / "Desktop" / "Job_Applications"


# ── Global session state ───────────────────────────────────────────────────────
_state: dict = {
    "jobs":     [],      # fetched + filtered jobs
    "selected": None,    # currently selected job dict
    "resumes":  {},      # job_url → {bullets, ats_result, tone_result, resume_text}
    "out_dir":  None,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _divider(char: str = "─", width: int = 60):
    print(char * width)


def _header(title: str):
    _divider("═")
    print(f"  {title}")
    _divider("═")


def _pick(prompt: str, options: list, allow_zero: bool = True) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            lo = 0 if allow_zero else 1
            if lo <= val <= len(options):
                return val
        except ValueError:
            pass
        print(f"  Please enter a number between {'0' if allow_zero else '1'} and {len(options)}.")


def _output_dir() -> Path:
    if _state["out_dir"] is None:
        d = Path(OUTPUT_BASE_DIR) / datetime.now().strftime("%Y-%m-%d")
        d.mkdir(parents=True, exist_ok=True)
        _state["out_dir"] = d
    return _state["out_dir"]


def _ensure_jobs():
    if not _state["jobs"]:
        print("\n  No jobs loaded. Fetching now...")
        _cmd_fetch_jobs()


# ── Feature commands ───────────────────────────────────────────────────────────

def _cmd_fetch_jobs():
    _header("FETCH JOBS")
    print("  Sources: Indeed (Playwright), Adzuna API, RSS feeds, LinkedIn RSS")
    print("  Filters: Ontario manufacturing/supervisor/manager roles (food/dairy excluded)\n")

    raw = fetch_all()
    _state["jobs"] = filter_jobs(raw)

    print(f"\n  Found {len(_state['jobs'])} matching jobs\n")
    for i, j in enumerate(_state["jobs"][:15], 1):
        ats_str = f"[{j['ats']:3d}%]"
        print(f"  {i:2}. {ats_str} {j['company'][:22]:22} | {j['title'][:40]}")

    # Email digest + Gmail storage
    if _state["jobs"]:
        try:
            send_job_digest(_state["jobs"])
            store_jobs_in_gmail(_state["jobs"])
        except Exception:
            pass


def _cmd_search_filter():
    _ensure_jobs()
    _header("SEARCH & FILTER JOBS")
    print("  Options:")
    print("  1. Free-text keyword search")
    print("  2. Filter by industry")
    print("  3. Filter by minimum ATS score")
    print("  0. Back")
    choice = _pick("  Choice: ", [""] * 3)

    if choice == 0:
        return

    jobs = _state["jobs"]

    if choice == 1:
        kw = input("  Enter keyword: ").strip()
        results = search_jobs(jobs, kw)
        print(f"\n  {len(results)} results for '{kw}':")
        for i, j in enumerate(results[:15], 1):
            print(f"  {i:2}. [{j['ats']:3d}%] {j['company'][:22]:22} | {j['title'][:40]}")
        _state["jobs"] = results if results else jobs

    elif choice == 2:
        industries = ["Manufacturing", "Automotive", "Aerospace", "Welding"]
        for i, ind in enumerate(industries, 1):
            print(f"  {i}. {ind}")
        idx = _pick("  Select industry: ", industries)
        if idx > 0:
            ind = industries[idx - 1]
            filtered = [j for j in jobs if j.get("industry") == ind]
            print(f"\n  {len(filtered)} jobs in {ind}")
            _state["jobs"] = filtered if filtered else jobs

    elif choice == 3:
        try:
            min_ats = int(input("  Minimum ATS score (e.g. 80): ").strip())
            filtered = [j for j in jobs if j.get("ats", 0) >= min_ats]
            print(f"\n  {len(filtered)} jobs with ATS ≥ {min_ats}%")
            _state["jobs"] = filtered if filtered else jobs
        except ValueError:
            print("  Invalid number.")


def _cmd_select_job():
    _ensure_jobs()
    _header("SELECT JOB")
    for i, j in enumerate(_state["jobs"][:20], 1):
        print(f"  {i:2}. [{j['ats']:3d}%] {j['company'][:22]:22} | {j['title'][:40]}")
    idx = _pick(f"  Select job (1-{min(20, len(_state['jobs']))}): ",
                _state["jobs"][:20], allow_zero=False)
    _state["selected"] = _state["jobs"][idx - 1]
    j = _state["selected"]
    print(f"\n  Selected: {j['title']} @ {j['company']} ({j['location']})")
    print(f"  Industry: {j.get('industry','N/A')} | ATS Forecast: {j['ats']}%")
    print(f"  URL: {j['url']}")


def _cmd_generate_resume():
    if not _state["selected"]:
        _cmd_select_job()
    job = _state["selected"]
    _header(f"GENERATE RESUME — {job['title'][:40]}")

    do_para = input("  Apply paraphrasing? (y/n): ").strip().lower() == "y"
    bullets = tailor_resume(job, paraphrase=do_para)
    resume_text = full_resume_text(job, bullets)
    cover = generate_cover_letter(job["company"], job["title"], job.get("description", ""))

    # ATS scoring
    ats_result = score_resume(resume_text, job.get("description", bullets))
    print_ats_report(ats_result)

    # Tone analysis
    tone_result = analyze_tone(bullets)
    print_tone_report(tone_result)

    # Section relevance
    sec_scores = score_resume_sections(resume_text, job.get("description", ""))
    if sec_scores:
        print_section_scores(sec_scores)

    # Generate files
    out = _output_dir()
    files = []
    try:
        files.append(create_resume_pdf(job, bullets, out))
        files.append(create_resume_docx(job, bullets, out))
        files.append(create_cover_pdf(job, cover, out))
        files.append(create_cover_docx(job, cover, out))
        print(f"\n  Files saved to: {out}")
    except Exception as exc:
        print(f"  File generation error: {exc}")

    # Save to history
    resume_id = save_resume(
        job, bullets, ats_result["ats_score"],
        cover_letter=cover,
        tone_score=tone_result["overall_score"],
        file_paths=files,
    )
    print(f"  Saved to history (ID #{resume_id})")

    # Cache for comparison
    _state["resumes"][job.get("url", job["title"])] = {
        "bullets":     bullets,
        "resume_text": resume_text,
        "ats_result":  ats_result,
        "tone_result": tone_result,
        "job":         job,
    }

    # Email notification
    try:
        send_resume_ready(
            job,
            ats_result["ats_score"],
            tone_result["overall_score"],
            file_paths=files,
            suggestions=ats_result["suggestions"],
        )
        store_resume_in_gmail(job, resume_text, ats_result["ats_score"])
    except Exception:
        pass


def _cmd_batch_generate():
    _ensure_jobs()
    _header("BATCH RESUME GENERATION")
    try:
        n = int(input(f"  Generate resumes for top N jobs (1-{min(10,len(_state['jobs']))}): ").strip())
        n = max(1, min(n, 10, len(_state["jobs"])))
    except ValueError:
        n = 5

    out = _output_dir()
    print(f"\n  Generating {n} resumes → {out}\n")

    for i, job in enumerate(_state["jobs"][:n], 1):
        try:
            bullets = tailor_resume(job)
            resume_text = full_resume_text(job, bullets)
            cover   = generate_cover_letter(job["company"], job["title"], job.get("description", ""))
            ats_r   = score_resume(resume_text, job.get("description", bullets))
            tone_r  = analyze_tone(bullets)

            files = [
                create_resume_pdf(job, bullets, out),
                create_resume_docx(job, bullets, out),
                create_cover_pdf(job, cover, out),
                create_cover_docx(job, cover, out),
            ]
            save_resume(job, bullets, ats_r["ats_score"],
                        cover_letter=cover, tone_score=tone_r["overall_score"],
                        file_paths=files)

            status = f"ATS {ats_r['ats_score']:.0f}%  Tone {tone_r['overall_score']}/100"
            print(f"  {i:2}. [{status}] {job['company'][:25]:25} {job['title'][:35]}")
        except Exception as exc:
            print(f"  {i:2}. ERROR — {job.get('company','')} — {exc}")

    # Open HTML dashboard
    _cmd_open_dashboard()


def _cmd_compare_resumes():
    cached = list(_state["resumes"].items())
    if len(cached) < 2:
        print("\n  Generate at least 2 resumes first (option 5).")
        return

    _header("COMPARE RESUMES")
    for i, (url, data) in enumerate(cached[-6:], 1):
        j = data["job"]
        print(f"  {i}. {j.get('title','')} @ {j.get('company','')} "
              f"(ATS {data['ats_result']['ats_score']:.0f}%)")

    a_idx = _pick(f"  Select Resume A (1-{min(6,len(cached))}): ",
                  cached[-6:], allow_zero=False)
    b_idx = _pick(f"  Select Resume B (1-{min(6,len(cached))}): ",
                  cached[-6:], allow_zero=False)

    _, data_a = cached[-6:][a_idx - 1]
    _, data_b = cached[-6:][b_idx - 1]
    ja, jb    = data_a["job"], data_b["job"]

    report = compare_resumes(
        data_a["resume_text"], data_b["resume_text"],
        label_a=f"{ja['company'][:15]}",
        label_b=f"{jb['company'][:15]}",
        ats_score_a=data_a["ats_result"]["ats_score"],
        ats_score_b=data_b["ats_result"]["ats_score"],
    )
    print_comparison(report)

    out = _output_dir() / "resume_comparison.html"
    export_comparison_html(report, str(out))
    webbrowser.open(str(out))


def _cmd_nlp_analysis():
    if not _state["selected"]:
        _cmd_select_job()
    job = _state["selected"]
    jd  = job.get("description", "")
    _header(f"NLP ANALYSIS — {job['title'][:40]}")

    print("\n  Entities in job description:")
    for ent, label in extract_entities(jd)[:12]:
        print(f"    [{label:15}] {ent}")

    print("\n  Sentiment:")
    s = sentiment(jd)
    print(f"    Polarity: {s['polarity']}  |  Subjectivity: {s['subjectivity']}  |  {s['label']}")

    print("\n  Top TF-IDF keywords:")
    for word, score in keywords_tfidf(jd, top_n=12):
        bar = "▪" * int(score * 60)
        print(f"    {word:25} {bar}")

    # Topic modelling over all loaded job descriptions
    docs = [j.get("description", "") for j in _state["jobs"] if j.get("description")]
    if docs:
        topics = topic_model(docs, n_topics=3)
        print("\n  Topic Model (across all jobs):")
        for i, topic in enumerate(topics, 1):
            print(f"    Topic {i}: {', '.join(topic)}")


def _cmd_tone_analysis():
    _header("TONE ANALYSIS")
    if _state["resumes"]:
        cached = list(_state["resumes"].values())
        data   = cached[-1]
        text   = data["bullets"]
        job    = data["job"]
        print(f"  Analysing last generated resume: {job.get('title','')} @ {job.get('company','')}")
    else:
        text = input("  Paste resume text (or press Enter to use a sample): ").strip()
        if not text:
            text = (
                "Led a team of 45 unionized workers. Achieved zero LTIs. "
                "Implemented Lean Six Sigma. Reduced waste by 12%. "
                "Resolved 90% of labour disputes."
            )

    report  = analyze_tone(text)
    print_tone_report(report)

    if report["overall_score"] < 75:
        improved = improve_tone(text)
        print("\n  AUTO-IMPROVED VERSION:")
        print("  " + improved.replace("\n", "\n  "))


def _cmd_paraphrase():
    _header("PARAPHRASE RESUME SECTION")
    if _state["resumes"]:
        data = list(_state["resumes"].values())[-1]
        text = data["bullets"]
        jd   = data["job"].get("description", "")
    else:
        text = input("  Paste bullet points to paraphrase: ").strip()
        jd   = ""

    rewritten = paraphrase_resume_section(text, jd)
    show_diff(text, rewritten)
    print("\n  PARAPHRASED VERSION:")
    print(rewritten)


def _cmd_view_history():
    _header("RESUME HISTORY")
    print("  1. View recent history")
    print("  2. Search history")
    print("  3. Export to HTML dashboard")
    print("  4. Export to CSV")
    print("  0. Back")
    choice = _pick("  Choice: ", [""] * 4)

    if choice == 1:
        print_history(15)
    elif choice == 2:
        q = input("  Search query: ").strip()
        results = search_history(q)
        print(f"\n  {len(results)} results for '{q}':")
        for e in results[:10]:
            ts = e.get("timestamp", "")[:16].replace("T", " ")
            print(f"  #{e.get('id','?')} {ts} — {e.get('job_title','')} @ {e.get('company','')} — ATS {e.get('ats_score',0):.0f}%")
    elif choice == 3:
        out = _output_dir() / "resume_history.html"
        export_history_html(str(out))
        webbrowser.open(str(out))
    elif choice == 4:
        out = _output_dir() / "resume_history.csv"
        export_history_csv(str(out))


def _cmd_gmail_setup():
    _header("GMAIL LABEL SETUP")
    print("  Creating Gmail labels: Job-AI/All-Jobs, Job-AI/Applied, Job-AI/Generated-Resumes")
    ok = create_labels()
    if ok:
        print("  Done! Labels are now visible in your Gmail sidebar.")
    else:
        print("  Could not create labels. Ensure Gmail credentials are set in config.py.")


def _cmd_mark_applied():
    if not _state["selected"]:
        print("\n  Select a job first (option 3).")
        return
    job = _state["selected"]
    _header(f"MARK APPLIED — {job['title'][:40]}")
    confirm = input(f"  Mark '{job['title']}' @ {job['company']} as applied? (y/n): ").strip().lower()
    if confirm == "y":
        try:
            send_applied_confirmation(job)
        except Exception as exc:
            print(f"  Email error: {exc}")
        print("  Logged!")


def _cmd_open_dashboard():
    out     = _output_dir()
    jobs    = _state["jobs"][:10]
    if not jobs:
        print("  No jobs to display.")
        return

    jobs_html = ""
    for j in jobs:
        ats_color = "#27ae60" if j['ats'] >= 85 else "#f39c12" if j['ats'] >= 70 else "#e74c3c"
        jobs_html += f"""
        <div class="job">
          <span class="score" style="background:{ats_color}">{j['ats']}%</span>
          <h3>{j['title']}</h3>
          <p><strong>{j['company']}</strong> | {j['location']}</p>
          <p>Industry: {j.get('industry','Manufacturing')} | Source: {j.get('source','')}</p>
          <a href="{j['url']}" target="_blank" class="apply-btn">Apply Now</a>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Job-AI Dashboard</title>
<style>
  body{{font-family:Arial;margin:40px;background:#f0f4f8}}
  .container{{max-width:960px;margin:0 auto;background:white;padding:30px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
  h1{{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px}}
  .job{{border:1px solid #ddd;padding:20px;margin:15px 0;border-radius:5px;background:#fafafa;position:relative}}
  .score{{position:absolute;top:15px;right:15px;color:white;padding:8px 15px;border-radius:20px;font-weight:bold}}
  h3{{margin:0 0 8px;color:#2c3e50}}
  .apply-btn{{display:inline-block;background:#3498db;color:white;padding:9px 18px;text-decoration:none;border-radius:4px;margin-top:10px;font-size:.9em}}
</style></head><body>
<div class="container">
  <h1>Job-AI — Resume Optimizer Dashboard</h1>
  <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M')}</p>
  <p><strong>Matching Jobs:</strong> {len(_state['jobs'])} total | Top 10 shown</p>
  <p><strong>Output Folder:</strong> {out}</p>
  <hr>
  {jobs_html}
</div></body></html>"""

    html_file = out / "_DASHBOARD.html"
    html_file.write_text(html, encoding="utf-8")
    print(f"\n  Dashboard: {html_file}")
    webbrowser.open(str(html_file))


# ── Main menu ──────────────────────────────────────────────────────────────────

_MENU = [
    ("Fetch jobs from all platforms",         _cmd_fetch_jobs),
    ("Search / filter jobs",                  _cmd_search_filter),
    ("Select a job",                          _cmd_select_job),
    ("Generate tailored resume (single)",     _cmd_generate_resume),
    ("Batch generate top-N resumes",          _cmd_batch_generate),
    ("Compare two resumes side-by-side",      _cmd_compare_resumes),
    ("NLP analysis of job description",       _cmd_nlp_analysis),
    ("Tone analysis of resume",               _cmd_tone_analysis),
    ("Paraphrase resume section",             _cmd_paraphrase),
    ("View / export resume history",          _cmd_view_history),
    ("Set up Gmail labels",                   _cmd_gmail_setup),
    ("Mark job as applied (email log)",       _cmd_mark_applied),
    ("Open HTML dashboard",                   _cmd_open_dashboard),
]


def main():
    print("\n" + "═" * 60)
    print("  JOB-AI RESUME OPTIMIZER — Raouf Mayahi")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M')}")
    print("═" * 60)

    while True:
        print()
        _divider()
        print("  MAIN MENU")
        _divider()
        for i, (label, _) in enumerate(_MENU, 1):
            print(f"  {i:2}. {label}")
        print("   0. Exit")
        _divider()

        try:
            choice = int(input("  Choice: ").strip())
        except (ValueError, EOFError):
            continue

        if choice == 0:
            print("\n  Goodbye!\n")
            sys.exit(0)

        if 1 <= choice <= len(_MENU):
            try:
                _MENU[choice - 1][1]()
            except KeyboardInterrupt:
                print("\n  Cancelled.")
            except Exception as exc:
                print(f"\n  Error: {exc}")
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
