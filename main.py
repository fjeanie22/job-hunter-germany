import os
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# --- НАСТРОЙКИ ---
WEB_KEYWORDS = ["wordpress", "elementor", "html", "css", "webdesign", "website", "frontend"]
OFFICE_KEYWORDS = ["sachbearbeiter", "kauffrau", "kaufmann", "büro", "sekretär", "empfang", "verwaltung", "assistenz"]
MY_ZIP = "84453"
RADIUS = 50 

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
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")

def get_ba_token():
    """Получаем временный токен для доступа к API Arbeitsagentur"""
    url = "https://rest.arbeitsagentur.de/oauth/get_token_clientid"
    headers = {"X-API-Key": "jobboerse-api-key"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json().get("access_token")
    except:
        return None

def search_arbeitnow():
    print("Проверка Arbeitnow...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        res = requests.get(url, timeout=10)
        data = res.json().get("data", [])
        print(f"Arbeitnow вернул {len(data)} вакансий")
        return data
    except: return []

def search_arbeitsagentur():
    print("Проверка Arbeitsagentur...")
    token = get_ba_token()
    if not token:
        print("Не удалось получить токен BA")
        return []
    
    jobs = []
    base_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ищем по всем офисным словам сразу через запятую
    params = {
        "was": ",".join(OFFICE_KEYWORDS),
        "wo": MY_ZIP,
        "umkreis": RADIUS,
        "size": 20
    }
    try:
        res = requests.get(base_url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("stellenangebote", [])
            print(f"BA нашел {len(items)} вакансий в радиусе {RADIUS}км")
            for j in items:
                jobs.append({
                    "id": j.get("hashId"),
                    "title": j.get("titel"),
                    "company": j.get("arbeitgeber"),
                    "location": j.get("arbeitsort", {}).get("ort"),
                    "url": f"https://www.arbeitsagentur.de/jobboerse/jobdetail/{j.get('hashId')}",
                    "cat": "🏢 Office (BA)"
                })
    except Exception as e:
        print(f"Ошибка поиска BA: {e}")
    return jobs

def main():
    sent_jobs = load_sent_jobs()
    new_jobs_found = 0
    
    # 1. Arbeitnow
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

    # 2. Arbeitsagentur
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
    
    print(f"Итог: отправлено {new_jobs_found} новых вакансий")

if __name__ == "__main__":
    main()
