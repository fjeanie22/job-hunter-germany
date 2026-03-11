import os
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

def load_sent_jobs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_jobs(sent_jobs):
    with open(DB_FILE, "w") as f:
        json.dump(list(sent_jobs), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def search_jobs():
    print("Запрос к API Arbeitnow...")
    # Поиск WordPress вакансий в Германии
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {"search": "wordpress", "location": "germany"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Ошибка API: {e}")
        return []

def main():
    sent_jobs = load_sent_jobs()
    jobs = search_jobs()
    
    new_jobs_found = 0
    for job in jobs[:10]: # Проверяем последние 10 вакансий
        job_id = job.get("slug") # Уникальный ID вакансии
        
        if job_id not in sent_jobs:
            title = job.get("title")
            company = job.get("company_name")
            url = job.get("url")
            location = job.get("location")
            
            msg = (
                f"🆕 <b>Новая вакансия!</b>\n"
                f"📝 {title}\n"
                f"🏢 {company}\n"
                f"📍 {location}\n\n"
                f"🔗 <a href='{url}'>Откликнуться</a>"
            )
            
            send_telegram(msg)
            sent_jobs.add(job_id)
            new_jobs_found += 1
    
    if new_jobs_found > 0:
        save_sent_jobs(sent_jobs)
        print(f"Отправлено новых вакансий: {new_jobs_found}")
    else:
        print("Новых вакансий пока нет.")

if __name__ == "__main__":
    main()
