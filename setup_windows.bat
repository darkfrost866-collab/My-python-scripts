@echo off
echo Setting up Job-Resume AI on Windows
python --version
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m textblob.download_corpora

echo.
echo Set your API keys (replace XXXX):
setx ADZUNA_APP_ID "XXXX"
setx ADZUNA_APP_KEY "XXXX"
setx GMAIL_USER "you@gmail.com"
setx GMAIL_APP_PASSWORD "XXXX"

echo.
echo Close and reopen terminal, then run:
echo   venv\Scripts\activate
echo   python main.py
pause
