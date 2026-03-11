import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

ADZ_ID = "c6e9389e"
ADZ_KEY = "3a20349890d291936c53e0ec3e69188e"

# --- РАСШИРЕННЫЕ КЛЮЧЕВЫЕ СЛОВА ---
# Для твоего диплома (Финансы/Офис)
OFFICE_QUERIES = [
    "Sachbearbeiter", 
    "Finanzbuchhaltung", 
    "Buchhaltung", 
    "Rechnungswesen",
    "Kauffrau",
    "Büromanagement",
    "Finanzen",
    "Mitarbeiter Verwaltung"
]

# Для души (IT/Web)
WEB_QUERIES = ["WordPress", "Elementor", "Webdesign"]

LOC_OFFICE = "84453"
LOC_WEB = "Bayern"
RADIUS = "100"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_adzuna(sent, query, loc, dist):
    print(f"📡 Adzuna: {query}...")
    url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = {"app_id": ADZ_ID, "app_key": ADZ_KEY, "results_per_page": 10, "what": query, "where": loc, "distance": dist}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                msg = f"📌 <b>Adzuna: {query}</b>\n📝 {j.get('title')}\n🏢 {j.get('company', {}).get('display_name')}\n📍 {j.get('location', {}).get('display_name')}\n🔗 <a href='{j.get('redirect_url')}'>Открыть</a>"
                send_tg(msg)
                sent.add(j_id)
    except: pass

def search_jooble(sent, query, loc, dist):
    if not JOOBLE_KEY: return
    print(f"📡 Jooble: {query}...")
    try:
        res = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", 
                            json={"keywords": query, "location": loc, "radius": dist}, timeout=10).json()
        for j in res.get("jobs", []):
            j_id = f"jo-{j.get('id')}"
            if j_id not in sent:
                msg = f"💼 <b>Jooble: {query}</b>\n📝 {j.get('title')}\n🏢 {j.get('company')}\n📍 {j.get('location')}\n🔗 <a href='{j.get('link')}'>Открыть</a>"
                send_tg(msg)
                sent.add(j_id)
    except: pass

def main():
    sent = load_sent()
    
    # 1. Поиск WEB по Баварии
    for q in WEB_QUERIES:
        search_adzuna(sent, q, LOC_WEB, "0")
        search_jooble(sent, q, LOC_WEB, "0")
    
    # 2. Поиск ОФИСА/ФИНАНСОВ вокруг тебя
    for q in OFFICE_QUERIES:
        search_adzuna(sent, q, LOC_OFFICE, RADIUS)
        search_jooble(sent, q, LOC_OFFICE, RADIUS)
    
    with open(DB_FILE, "w") as f:
        json.dump(list(sent), f)
    print("🏁 Всё проверено!")

if __name__ == "__main__":
    main()
