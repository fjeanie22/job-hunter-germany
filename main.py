import os
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Настройки поиска
# 1. Веб-дизайн (Бавария)
WEB_KEYWORDS = ["wordpress", "elementor", "html", "css", "webdesign"]
BAVARIA_CITIES = ["munich", "münchen", "nuremberg", "nürnberg", "augsburg", "regensburg", "ingolstadt", "landshut", "mühldorf", "rosenheim"]

# 2. Офис (Мюльдорф + радиус)
OFFICE_KEYWORDS = ["sachbearbeiter", "kauffrau", "kaufmann", "sekretär", "büro", "assistant"]
NEAR_MY_TOWN = ["mühldorf", "altoetting", "altötting", "burghausen", "waldkraiburg", "ampfing", "neumarkt-sankt veit"]

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
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    requests.post(url, json=payload)

def is_relevant(job):
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()
    
    # Проверка Категории 1: Web + Бавария
    is_web = any(word in title for word in WEB_KEYWORDS)
    in_bavaria = any(city in location for city in BAVARIA_CITIES)
    if is_web and in_bavaria:
        return True, "🌐 Web & Design"

    # Проверка Категории 2: Офис + Мюльдорф и окрестности
    is_office = any(word in title for word in OFFICE_KEYWORDS)
    is_near = any(city in location for city in NEAR_MY_TOWN)
    if is_office and is_near:
        return True, "🏢 Office & Admin"
        
    return False, None

def main():
    sent_jobs = load_sent_jobs()
    url = "https://www.arbeitnow.com/api/job-board-api"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_jobs = response.json().get("data", [])
    except Exception as e:
        print(f"Ошибка API: {e}")
        return

    new_jobs_count = 0
    for job in all_jobs:
        job_id = job.get("slug")
        if job_id in sent_jobs:
            continue
            
        relevant, category = is_relevant(job)
        if relevant:
            msg = (
                f"✨ <b>{category}</b>\n"
                f"📝 <b>{job.get('title')}</b>\n"
                f"🏢 {job.get('company_name')}\n"
                f"📍 {job.get('location')}\n\n"
                f"🔗 <a href='{job.get('url')}'>Открыть вакансию</a>"
            )
            send_telegram(msg)
            sent_jobs.add(job_id)
            new_jobs_count += 1
            if new_jobs_count >= 10: break # Не больше 10 за раз

    save_sent_jobs(sent_jobs)
    print(f"Найдено подходящих: {new_jobs_count}")

if __name__ == "__main__":
    main()
