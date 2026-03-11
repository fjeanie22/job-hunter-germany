import os
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY") # Получи на jooble.org/api-key
DB_FILE = "sent_jobs.json"

# Ключевые слова
WEB_KEYWORDS = ["wordpress", "elementor", "webdesign", "website", "frontend", "дизайн", "cms"]
OFFICE_KEYWORDS = ["sachbearbeiter", "kauffrau", "kaufmann", "büro", "sekretär", "empfang", "assistenz", "office"]

def load_sent_jobs():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def save_sent_jobs(sent_jobs):
    with open(DB_FILE, "w") as f: json.dump(list(sent_jobs), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def get_ba_token():
    # Улучшенный метод получения токена BA
    url = "https://rest.arbeitsagentur.de/oauth/get_token_clientid"
    headers = {
        "X-API-Key": "jobboerse-api-key",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json().get("access_token")
    except: return None

def search_jooble():
    if not JOOBLE_KEY: return []
    print("Проверка Jooble...")
    jobs = []
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    
    # Ищем офис в Мюльдорфе (84453)
    payload = {"keywords": "sachbearbeiter kauffrau", "location": "84453", "radius": "25"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        for j in res.json().get("jobs", []):
            jobs.append({
                "id": str(j.get("id")),
                "title": j.get("title"),
                "company": j.get("company"),
                "location": j.get("location"),
                "url": j.get("link"),
                "cat": "🔍 Jooble Office"
            })
    except: pass
    return jobs

def main():
    sent_jobs = load_sent_jobs()
    new_jobs_found = 0
    
    # 1. Jooble (Самый надежный для Мюльдорфа)
    for j in search_jooble():
        if j["id"] not in sent_jobs:
            msg = (f"✨ <b>{j['cat']}</b>\n"
                   f"📝 {j['title']}\n"
                   f"🏢 {j.get('company', '---')}\n"
                   f"📍 {j['location']}\n\n"
                   f"🔗 <a href='{j['url']}'>Открыть</a>")
            send_telegram(msg)
            sent_jobs.add(j["id"])
            new_jobs_found += 1

    # 2. Arbeitnow (Web)
    print("Проверка Arbeitnow...")
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        for j in res.json().get("data", []):
            job_id = j.get("slug")
            title_lower = j.get("title", "").lower()
            if job_id not in sent_jobs and any(k in title_lower for k in WEB_KEYWORDS):
                msg = (f"✨ <b>🌐 Web Design</b>\n"
                       f"📝 {j.get('title')}\n"
                       f"🏢 {j.get('company_name')}\n\n"
                       f"🔗 <a href='{j.get('url')}'>Открыть</a>")
                send_telegram(msg)
                sent_jobs.add(job_id)
                new_jobs_found += 1
    except: pass

    if new_jobs_found > 0:
        save_sent_jobs(sent_jobs)
    print(f"Итог: отправлено {new_jobs_found}")

if __name__ == "__main__":
    main()
