from playwright.sync_api import sync_playwright
import time

def fetch_indeed_playwright():
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        urls = [
            "https://ca.indeed.com/jobs?q=production+supervisor&l=Ontario&fromage=14",
            "https://ca.indeed.com/jobs?q=welding+supervisor&l=Ontario",
        ]
        
        for url in urls:
            page.goto(url, timeout=30000)
            time.sleep(3)
            cards = page.query_selector_all('div.job_seen_beacon')
            for card in cards[:10]:
                title = card.query_selector('h2').inner_text() if card.query_selector('h2') else ''
                company = card.query_selector('span[data-testid="company-name"]').inner_text() if card.query_selector('span[data-testid="company-name"]') else ''
                link = card.query_selector('a').get_attribute('href')
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': 'Ontario',
                    'url': 'https://ca.indeed.com' + link,
                    'description': title,
                    'source': 'Indeed-Playwright'
                })
        browser.close()
    return jobs