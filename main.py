import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY") # Убедись, что ключ в Secrets
DB_FILE = "sent_jobs.json"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_jooble(sent, query, loc):
    """Jooble обычно дает много результатов по Германии"""
    if not JOOBLE_KEY: return []
    print(f"📡 Jooble: {query}...")
    found = []
    try:
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        data = {"keywords": query, "location": loc}
        res = requests.post(url, json=data, timeout=15).json()
        for j in res.get("jobs", []):
            j_id = f"jo-{j.get('id')}"
            if j_id not in sent:
                msg = f"💼 <b>Jooble: {query}</b>\n📝 {j.get('title')}\n🏢 {j.get('company', '---')}\n📍 {j.get('location')}\n🔗 <a href='{j.get('link')}'>Link</a>"
                found.append((j_id, msg))
    except: pass
    return found

def search_arbeitnow(sent):
    print("📡 Arbeitnow...")
    found = []
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in res.get("data", []):
            title = j.get("title", "").lower()
            if any(word in title for word in ["wordpress", "elementor", "remote", "sachbearbeiter"]):
                j_id = f"an-{j.get('slug')}"
                if j_id not in sent:
                    msg = f"🌐 <b>Arbeitnow</b>\n📝 {j.get('title')}\n🏢 {j.get('company_name')}\n🔗 <a href='{j.get('url')}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. Jooble - СТРОГО ГЕРМАНИЯ
    # Офис в Мюльдорфе (используем индекс и город для надежности)
    new_jobs.extend(search_jooble(sent, "Sachbearbeiter", "Mühldorf am Inn, Deutschland"))
    new_jobs.extend(search_jooble(sent, "Finanzen", "Mühldorf am Inn, Deutschland"))
    
    # WordPress удаленно - ТЕПЕРЬ С ПОМЕТКОЙ DE
    new_jobs.extend(search_jooble(sent, "WordPress", "Remote, Deutschland"))
    new_jobs.extend(search_jooble(sent, "Elementor", "Remote, Deutschland"))
    
    # 2. Arbeitnow (он и так немецкий, там все ок)
    new_jobs.extend(search_arbeitnow(sent))

    if new_jobs:
        # Фильтруем на всякий случай, чтобы в заголовок не пролезла Америка
        # (если в локации есть USA или United States - пропускаем)
        for j_id, msg in new_jobs[:15]:
            if "USA" in msg or "Chicago" in msg or "NY" in msg: 
                continue
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
    else:
        print("Новых вакансий в Германии не найдено.")

if __name__ == "__main__":
    main()
