import os, imaplib

user = os.getenv("GMAIL_USER")
pwd = os.getenv("GMAIL_APP_PASSWORD")

print("Trying login for:", user)
print("Password length:", len(pwd) if pwd else 0)

try:
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(user, pwd)
    print("SUCCESS - login worked")
    imap.logout()
except Exception as e:
    print("FAILED:", e)