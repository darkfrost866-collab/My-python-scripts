"""email_bot.py — Rich HTML email notifications with Gmail label routing"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime

try:
    from config import EMAIL_USER, EMAIL_PASS, SMTP_SERVER, SMTP_PORT
except Exception:
    EMAIL_USER  = ""
    EMAIL_PASS  = ""
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT   = 587


def _build_html_wrapper(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body{{font-family:Arial,sans-serif;background:#f0f4f8;margin:0;padding:20px}}
  .wrap{{max-width:700px;margin:0 auto;background:white;border-radius:8px;
         box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden}}
  .hdr{{background:#2c3e50;color:white;padding:20px 30px}}
  .hdr h1{{margin:0;font-size:1.3em}}
  .hdr p{{margin:4px 0 0;opacity:.8;font-size:.85em}}
  .body{{padding:25px 30px}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#34495e;color:white;padding:10px;text-align:left;font-size:.85em}}
  td{{padding:9px 10px;border-bottom:1px solid #eee;font-size:.9em}}
  tr:hover{{background:#f8f9fa}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:12px;
          font-weight:bold;font-size:.85em;color:white}}
  .btn{{display:inline-block;background:#3498db;color:white;padding:8px 16px;
        text-decoration:none;border-radius:4px;font-size:.85em}}
  .footer{{background:#ecf0f1;padding:12px 30px;font-size:.78em;color:#888}}
</style>
</head>
<body><div class="wrap">
<div class="hdr"><h1>Job-AI Resume Optimizer</h1>
<p>Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}</p></div>
<div class="body">{body_html}</div>
<div class="footer">Sent by Job-AI · Raouf Mayahi · Ontario, Canada</div>
</div></body></html>"""


def _send(subject: str, html: str, label_tag: str = "", attachments: list = None):
    if not EMAIL_USER or not EMAIL_PASS:
        print("  Email credentials not configured — skipping send.")
        return False
    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_USER
    msg["To"]      = EMAIL_USER
    msg["Subject"] = f"[Job-AI] {label_tag + ' — ' if label_tag else ''}{subject}"

    msg.attach(MIMEText("Please view this email in an HTML-capable client.", "plain"))
    msg.attach(MIMEText(html, "html"))

    if attachments:
        outer = MIMEMultipart("mixed")
        outer["From"]    = msg["From"]
        outer["To"]      = msg["To"]
        outer["Subject"] = msg["Subject"]
        outer.attach(msg)
        for path in attachments:
            p = Path(path)
            if p.exists():
                with open(p, "rb") as f:
                    part = MIMEApplication(f.read(), Name=p.name)
                    part["Content-Disposition"] = f'attachment; filename="{p.name}"'
                    outer.attach(part)
        msg = outer

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as srv:
            srv.starttls()
            srv.login(EMAIL_USER, EMAIL_PASS)
            srv.send_message(msg)
        print(f"  Email sent → {EMAIL_USER}")
        return True
    except Exception as exc:
        print(f"  Email failed: {exc}")
        print("  Check: Gmail App Password enabled, 2-Step Verification on.")
        return False


# ── Public notification functions ─────────────────────────────────────────────

def send_job_digest(jobs: list):
    """Send a formatted job digest email."""
    if not jobs:
        return
    rows = ""
    for j in jobs[:20]:
        ats = j.get("ats", 0) or 0
        color = "#27ae60" if ats >= 85 else "#f39c12" if ats >= 70 else "#e74c3c"
        rows += f"""
        <tr>
          <td><strong>{j.get('title','')}</strong></td>
          <td>{j.get('company','')}</td>
          <td>{j.get('location','')}</td>
          <td><span class="badge" style="background:{color}">{ats}%</span></td>
          <td>{j.get('industry','')}</td>
          <td><a class="btn" href="{j.get('url','#')}" target="_blank">Apply</a></td>
        </tr>"""

    body = f"""
    <h2>New Job Matches Found</h2>
    <p><strong>{len(jobs)}</strong> manufacturing/supervisory roles matched your profile today.</p>
    <table>
      <tr><th>Title</th><th>Company</th><th>Location</th><th>ATS</th><th>Industry</th><th></th></tr>
      {rows}
    </table>"""

    html = _build_html_wrapper(f"Job Digest — {len(jobs)} new matches", body)
    _send(f"Job Digest — {len(jobs)} matches ({datetime.now().strftime('%Y-%m-%d')})",
          html, label_tag="Jobs")


def send_resume_ready(job: dict, ats_score: float, tone_score: int,
                      file_paths: list = None, suggestions: list = None):
    """Notify that a tailored resume is ready, with ATS + tone scores."""
    ats_color  = "#27ae60" if ats_score >= 80 else "#f39c12" if ats_score >= 65 else "#e74c3c"
    tone_color = "#27ae60" if (tone_score or 0) >= 70 else "#f39c12"

    sugg_html = ""
    if suggestions:
        items = "".join(f"<li>{s}</li>" for s in suggestions[:6])
        sugg_html = f"<h3>Improvement Suggestions</h3><ul>{items}</ul>"

    body = f"""
    <h2>Resume Ready — {job.get('title','')} @ {job.get('company','')}</h2>
    <table>
      <tr><th>Field</th><th>Value</th></tr>
      <tr><td>ATS Score</td>
          <td><span class="badge" style="background:{ats_color}">{ats_score}%</span></td></tr>
      <tr><td>Tone Score</td>
          <td><span class="badge" style="background:{tone_color}">{tone_score or 'N/A'}/100</span></td></tr>
      <tr><td>Location</td><td>{job.get('location','')}</td></tr>
      <tr><td>Industry</td><td>{job.get('industry','')}</td></tr>
      <tr><td>Source</td><td>{job.get('source','')}</td></tr>
      <tr><td>Job Link</td><td><a class="btn" href="{job.get('url','#')}">View Posting</a></td></tr>
    </table>
    {sugg_html}
    <p style="color:#888;font-size:.85em">Files attached if generated.</p>"""

    html = _build_html_wrapper(f"Resume: {job.get('title','')} @ {job.get('company','')}", body)
    _send(
        f"Resume Ready — {job.get('title','')} @ {job.get('company','')} — ATS {ats_score}%",
        html,
        label_tag="Generated",
        attachments=file_paths or [],
    )


def send_notification(subject: str, body: str, attachments: list = None):
    """Generic plain-text notification (backwards-compatible)."""
    html = _build_html_wrapper(subject, f"<pre style='font-family:Arial'>{body}</pre>")
    _send(subject, html, attachments=attachments)


def send_applied_confirmation(job: dict):
    """Send an 'Applied' confirmation email."""
    body = f"""
    <h2 style="color:#27ae60">Application Logged!</h2>
    <table>
      <tr><th>Field</th><th>Value</th></tr>
      <tr><td>Position</td><td><strong>{job.get('title','')}</strong></td></tr>
      <tr><td>Company</td><td>{job.get('company','')}</td></tr>
      <tr><td>Location</td><td>{job.get('location','')}</td></tr>
      <tr><td>Date Applied</td><td>{datetime.now().strftime('%B %d, %Y')}</td></tr>
      <tr><td>ATS Score</td><td>{job.get('ats','N/A')}%</td></tr>
      <tr><td>Job Link</td><td><a class="btn" href="{job.get('url','#')}">View Posting</a></td></tr>
    </table>"""
    html = _build_html_wrapper(f"Applied: {job.get('title','')} @ {job.get('company','')}", body)
    _send(f"Applied: {job.get('title','')} @ {job.get('company','')}", html, label_tag="Applied")
