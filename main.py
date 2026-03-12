import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

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

def search_adzuna_local(sent, query, loc, dist=40):
    print(f"📡 Поиск {query}...")
    found = []
    try:
        url = "https://api.adzuna.com/v1/api/jobs/de/search/1"
        params = {
            "app_id": ADZ_ID, "app_key": ADZ_KEY, 
            "results_per_page": 15, "what": query, 
            "where": loc, "distance": dist
        }
        res = requests.get(url, params=params, timeout=15).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                msg = (f"💎 <b>{query}</b>\n"
                       f"📝 {j.get('title')}\n"
                       f"🏢 {j.get('company', {}).get('display_name', '---')}\n"
                       f"📍 {j.get('location', {}).get('display_name')}\n"
                       f"🔗 <a href='{j.get('redirect_url')}'>Link</a>")
                found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # КВАЛИФИЦИРОВАННЫЙ ОФИС (Back-office, минимум общения)
    for q in ["Sachbearbeiter", "Buchhaltung", "Datenerfassung", "Verwaltung"]:
        new_jobs.extend(search_adzuna_local(sent, q, "84453", dist=45))
    
    # IT / WEB (Для смены параграфа — идеально)
    for q in ["WordPress", "Elementor", "Webdesigner"]:
        new_jobs.extend(search_adzuna_local(sent, q, "Bayern", dist=0)) # По всей Баварии

    if new_jobs:
        for j_id, msg in new_jobs[:15]:
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
    else:
        print("Новых квалифицированных вакансий пока нет.")

if __name__ == "__main__":
    main()
