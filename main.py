import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

# Ключевые слова
WEB_KW = ["wordpress", "elementor", "webdesign", "frontend", "html", "css"]
OFFICE_KW = ["sachbearbeiter", "kauffrau", "büro", "sekretär", "assistenz", "office"]

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_jooble(sent):
    if not JOOBLE_KEY:
        print("❌ JOOBLE_KEY не найден в env")
        return 0
    print("🔍 Проверка Jooble (Мюльдорф + 25км)...")
    count = 0
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    # Собираем ключевые слова для поиска
    query = " ".join(OFFICE_KW)
    payload = {"keywords": query, "location": "84453", "radius": "25"}
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        jobs = res.json().get("jobs", [])
        print(f"✅ Jooble нашел всего: {len(jobs)}")
        for j in jobs:
            j_id = str(j.get("id"))
            if j_id not in sent:
                msg = f"🔍 <b>Jooble Office</b>\n📝 {j.get('title')}\n🏢 {j.get('company')}\n📍 {j.get('location')}\n\n🔗 <a href='{j.get('link')}'>Открыть</a>"
                send_tg(msg)
                sent.add(j_id)
                count += 1
    except Exception as e: print(f"❌ Ошибка Jooble: {e}")
    return count

def search_arbeitnow(sent):
    print("🔍 Проверка Arbeitnow (Web)...")
    count = 0
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        jobs = res.json().get("data", [])
        for j in jobs:
            j_id = j.get("slug")
            title = j.get("title", "").lower()
            if j_id not in sent and any(k in title for k in WEB_KW):
                msg = f"🌐 <b>Web Design</b>\n📝 {j.get('title')}\n🏢 {j.get('company_name')}\n📍 {j.get('location')}\n\n🔗 <a href='{j.get('url')}'>Открыть</a>"
                send_tg(msg)
                sent.add(j_id)
                count += 1
    except Exception as e: print(f"❌ Ошибка Arbeitnow: {e}")
    return count

def main():
    sent = load_sent()
    found_jooble = search_jooble(sent)
    found_web = search_arbeitnow(sent)
    
    total = found_jooble + found_web
    if total > 0:
        with open(DB_FILE, "w") as f: json.dump(list(sent), f)
    print(f"🏁 Итог: отправлено {total} новых вакансий")

if __name__ == "__main__":
    main()
