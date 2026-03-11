import os
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# --- НАСТРОЙКИ ---
# Веб-дизайн (ключевые слова)
WEB_KEYWORDS = ["wordpress", "elementor", "html", "css", "webdesign"]
# Офис (ключевые слова)
OFFICE_KEYWORDS = ["sachbearbeiter", "kauffrau", "kaufmann", "büro", "sekretär"]
MY_ZIP = "84453" # Мюльдорф
RADIUS = 50      # Радиус в км

def load_sent_jobs():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_sent_jobs(sent_jobs):
    with open(DB_FILE, "w") as f:
        json.dump(list(sent_jobs), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def search_arbeitnow():
    """Поиск на Arbeitnow (Web)"""
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        res = requests.get(url)
        return res.json().get("data", [])
    except: return []

def search_arbeitsagentur():
    """Поиск на Arbeitsagentur (Office)"""
    # Используем их публичный API для поиска
    # Мы ищем по ключевым словам из OFFICE_KEYWORDS в твоем регионе
    jobs = []
    base_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-API-Key": "jobboerse-api-key" # Это публичный ключ
    }
    
    for kw in OFFICE_KEYWORDS:
        params = {
            "was": kw,
            "wo": MY_ZIP,
            "umkreis": RADIUS,
            "size": 10
        }
        try:
            res = requests.get(base_url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                for j in data.get("stellenangebote", []):
                    jobs.append({
                        "id": j.get("hashId"),
                        "title": j.get("titel"),
                        "company": j.get("arbeitgeber"),
                        "location": j.get("arbeitsort", {}).get("ort"),
                        "url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{j.get('hashId')}",
                        "cat": "🏢 Office (BA)"
                    })
        except: continue
    return jobs

def main():
    sent_jobs = load_sent_jobs()
    new_jobs_found = 0
    
    # 1. Проверяем Arbeitnow
    for j in search_arbeitnow():
        job_id = j.get("slug")
        title = j.get("title", "").lower()
        if job_id not in sent_jobs and any(k in title for k in WEB_KEYWORDS):
            msg = (f"✨ <b>🌐 Web Design</b>\n"
                   f"📝 {j.get('title')}\n"
                   f"🏢 {j.get('company_name')}\n"
                   f"📍 {j.get('location')}\n\n"
                   f"🔗 <a href='{j.get('url')}'>Открыть</a>")
            send_telegram(msg)
            sent_jobs.add(job_id)
            new_jobs_found += 1

    # 2. Проверяем Arbeitsagentur
    for j in search_arbeitsagentur():
        job_id = j.get("id")
        if job_id and job_id not in sent_jobs:
            msg = (f"✨ <b>{j['cat']}</b>\n"
                   f"📝 {j['title']}\n"
                   f"🏢 {j['company']}\n"
                   f"📍 {j['location']}\n\n"
                   f"🔗 <a href='{j['url']}'>Открыть</a>")
            send_telegram(msg)
            sent_jobs.add(job_id)
            new_jobs_found += 1

    if new_jobs_found > 0:
        save_sent_jobs(sent_jobs)
    print(f"Готово. Найдено новых: {new_jobs_found}")

if __name__ == "__main__":
    main()
