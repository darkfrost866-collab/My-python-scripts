import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from config import EMAIL_USER, EMAIL_PASS

def send_notification(subject, body, attachments=None):
    """
    Send email via Gmail using App Password
    attachments: list of Path objects or strings to files
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER  # sends to yourself
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                path = Path(file_path)
                if path.exists():
                    with open(path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                        part['Content-Disposition'] = f'attachment; filename="{path.name}"'
                        msg.attach(part)

        # Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print(f"✓ Email sent to {EMAIL_USER}")

    except Exception as e:
        print(f"✗ Email failed: {e}")
        print("Check: 1) Gmail App Password is correct, 2) 2FA enabled")