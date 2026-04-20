"""resume_history.py — Track, retrieve, and export generated resumes"""
import json
import os
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "data" / "resume_history.json"


def _load() -> list:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(history: list):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def save_resume(job: dict, bullets: str, ats_score: float,
                cover_letter: str = "", tone_score: int = None,
                file_paths: list = None):
    """Append a generated resume entry to the history file."""
    history = _load()
    entry = {
        "id":           len(history) + 1,
        "timestamp":    datetime.now().isoformat(),
        "job_title":    job.get("title", ""),
        "company":      job.get("company", ""),
        "location":     job.get("location", ""),
        "job_url":      job.get("url", ""),
        "industry":     job.get("industry", ""),
        "source":       job.get("source", ""),
        "ats_score":    ats_score,
        "tone_score":   tone_score,
        "bullets":      bullets,
        "cover_letter": cover_letter,
        "file_paths":   [str(p) for p in (file_paths or [])],
    }
    history.append(entry)
    _save(history)
    return entry["id"]


def list_history(limit: int = 20) -> list:
    """Return the most recent `limit` resume entries."""
    history = _load()
    return history[-limit:][::-1]  # newest first


def get_by_id(resume_id: int) -> dict | None:
    history = _load()
    for entry in history:
        if entry.get("id") == resume_id:
            return entry
    return None


def search_history(query: str) -> list:
    """Search history by company, title, or keyword."""
    q = query.lower()
    return [
        e for e in _load()
        if q in e.get("job_title", "").lower()
        or q in e.get("company", "").lower()
        or q in e.get("industry", "").lower()
        or q in e.get("bullets", "").lower()
    ]


def export_history_csv(output_path: str):
    """Export history to a CSV file."""
    import csv
    history = _load()
    if not history:
        print("  No history to export.")
        return
    fields = ["id", "timestamp", "job_title", "company", "location",
              "ats_score", "tone_score", "industry", "source", "job_url"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(history)
    print(f"  History exported → {output_path}")


def export_history_html(output_path: str):
    """Export history as a browsable HTML dashboard."""
    history = _load()
    if not history:
        print("  No history to export.")
        return

    rows = ""
    for e in reversed(history):
        ats = e.get("ats_score", 0) or 0
        tone = e.get("tone_score", "N/A")
        color = "#27ae60" if ats >= 85 else "#f39c12" if ats >= 70 else "#e74c3c"
        ts = e.get("timestamp", "")[:16].replace("T", " ")
        rows += f"""
        <tr>
          <td>{e.get('id','')}</td>
          <td>{ts}</td>
          <td>{e.get('job_title','')}</td>
          <td>{e.get('company','')}</td>
          <td>{e.get('location','')}</td>
          <td style="font-weight:bold;color:{color}">{ats}%</td>
          <td>{tone}</td>
          <td><a href="{e.get('job_url','#')}" target="_blank">Link</a></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Resume History — Job-AI</title>
<style>
  body{{font-family:Arial,sans-serif;max-width:1100px;margin:40px auto;color:#333}}
  h1{{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#2c3e50;color:white;padding:10px;text-align:left}}
  td{{padding:9px;border-bottom:1px solid #eee}}
  tr:hover{{background:#f5f9ff}}
</style>
</head><body>
<h1>Resume Generation History</h1>
<p>Total resumes generated: <strong>{len(history)}</strong></p>
<table>
  <tr>
    <th>#</th><th>Date</th><th>Job Title</th><th>Company</th>
    <th>Location</th><th>ATS</th><th>Tone</th><th>Link</th>
  </tr>
  {rows}
</table>
</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  History dashboard saved → {output_path}")


def print_history(limit: int = 10):
    entries = list_history(limit)
    if not entries:
        print("  No resume history found.")
        return
    print("\n" + "="*70)
    print("  RESUME GENERATION HISTORY (most recent first)")
    print("="*70)
    print(f"  {'#':3}  {'Date':16}  {'ATS':5}  {'Company':22}  Title")
    print("  " + "-"*66)
    for e in entries:
        ts   = e.get("timestamp", "")[:16].replace("T", " ")
        ats  = f"{e.get('ats_score', 0):.0f}%"
        co   = e.get("company", "")[:20]
        title = e.get("job_title", "")[:35]
        print(f"  {e.get('id','?'):3}  {ts:16}  {ats:5}  {co:22}  {title}")
    print("="*70)
