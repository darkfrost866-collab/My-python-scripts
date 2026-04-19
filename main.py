from pathlib import Path
from datetime import datetime
import webbrowser
from job_fetcher import fetch_all, filter_jobs
from resume_tailor import tailor_resume, generate_cover_letter
from pdf_generator import create_resume_pdf, create_resume_docx, create_cover_pdf, create_cover_docx

def main():
    print("="*60)
    print("JOB AI - RAOUF MAYAHI")
    print(datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*60)
    
    # Fetch jobs
    all_jobs = fetch_all()
    jobs = filter_jobs(all_jobs)
    
    print(f"\nFound {len(jobs)} manufacturing jobs (food/dairy excluded)\n")
    
    if not jobs:
        print("No jobs found. Try again later.")
        return
    
    # Create output folder
    output_dir = Path.home() / "Desktop" / "Job_Applications" / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process top jobs
    for i, job in enumerate(jobs[:10], 1):
        print(f" {i}. [{job['ats']}%] {job['company'][:25]:25} | {job['title'][:40]}")
        
        try:
            bullets = tailor_resume(job)
            cover = generate_cover_letter(job['company'], job['title'])
            
            create_resume_pdf(job, bullets, output_dir)
            create_resume_docx(job, bullets, output_dir)
            create_cover_pdf(job, cover, output_dir)
            create_cover_docx(job, cover, output_dir)
        except Exception as e:
            print(f"    Error: {e}")
    
    # Create HTML dashboard - using .format() to avoid brace issues
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Job Applications</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .job {{ border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 5px; background: #fafafa; }}
        .score {{ float: right; background: #27ae60; color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold; }}
        h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .apply-btn {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Raouf Mayahi - Job Applications</h1>
        <p><strong>Generated:</strong> {date}</p>
        <p><strong>Jobs:</strong> {count}</p>
        <hr>
        {jobs_html}
        <p><strong>Files:</strong> {folder}</p>
    </div>
</body>
</html>"""
    
    jobs_html = ""
    for job in jobs[:10]:
        jobs_html += f"""
        <div class="job">
            <span class="score">{job['ats']}%</span>
            <h3>{job['title']}</h3>
            <p><strong>{job['company']}</strong> | {job['location']}</p>
            <p>Industry: {job.get('industry', 'Manufacturing')}</p>
            <a href="{job['url']}" target="_blank" class="apply-btn">Apply Now</a>
        </div>
"""
    
    html = html_template.format(
        date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        count=len(jobs),
        jobs_html=jobs_html,
        folder=str(output_dir)
    )
    
    html_file = output_dir / "_OPEN_ME.html"
    html_file.write_text(html, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"COMPLETE! Folder: {output_dir}")
    print(f"{'='*60}\n")
    
    webbrowser.open(str(html_file))

if __name__ == "__main__":
    main()