import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

# Ключи Adzuna (мы их починили)
ADZ_ID = "c6e9389e"
ADZ_KEY = "3a20349890d291936c53e0ec3e69188e"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_jooble(sent, query, loc, radius=0):
    if not JOOBLE_KEY: return []
    found = []
    try:
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        data = {"keywords": query, "location": loc, "radius": radius}
        res = requests.post(url, json=data, timeout=15).json()
        for j in res.get("jobs", []):
            j_id = f"jo-{j.get('id')}"
            if j_id not in sent:
                # Маленький фильтр, чтобы Делавэр не просочился
                if "usa" in j.get('location', '').lower(): continue
                msg = f"💼 <b>Jooble: {query}</b>\n📝 {j.get('title')}\n🏢 {j.get('company', '---')}\n📍 {j.get('location')}\n🔗 <a href='{j.get('link')}'>Link</a>"
                found.append((j_id, msg))
    except: pass
    return found

def search_adzuna(sent, query, loc):
    found = []
    try:
        url = "https://api.adzuna.com/v1/api/jobs/de/search/1"
        params = {"app_id": ADZ_ID, "app_key": ADZ_KEY, "results_per_page": 10, "what": query, "where": loc}
        res = requests.get(url, params=params, timeout=15).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                msg = f"📌 <b>Adzuna: {query}</b>\n📝 {j.get('title')}\n🏢 {j.get('company', {}).get('display_name')}\n📍 {j.get('location', {}).get('display_name')}\n🔗 <a href='{j.get('redirect_url')}'>Link</a>"
                found.append((j_id, msg))
    except: pass
    return found

def search_arbeitnow(sent):
    found = []
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in res.get("data", []):
            title = j.get("title", "").lower()
            if any(word in title for word in ["wordpress", "elementor", "sachbearbeiter"]):
                j_id = f"an-{j.get('slug')}"
                if j_id not in sent:
                    msg = f"🌐 <b>Arbeitnow (Remote)</b>\n📝 {j.get('title')}\n🏢 {j.get('company_name')}\n🔗 <a href='{j.get('url')}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. Jooble (Бавария и Мюльдорф)
    new_jobs.extend(search_jooble(sent, "WordPress", "Bayern, Germany"))
    new_jobs.extend(search_jooble(sent, "Sachbearbeiter", "84453 Mühldorf am Inn, Germany", radius=50))
    
    # 2. Adzuna (Тут ищем офис)
    new_jobs.extend(search_adzuna(sent, "Büro", "Mühldorf am Inn"))
    
    # 3. Arbeitnow (IT и Удаленка)
    new_jobs.extend(search_arbeitnow(sent))

    if new_jobs:
        for j_id, msg in new_jobs[:15]:
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
    else:
        print("Новых вакансий пока нет.")

if __name__ == "__main__":
    main()
