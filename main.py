import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

# --- НАСТРОЙКИ ПОИСКА ---
# 1. Веб-дизайн (Вся Бавария)
WEB_QUERIES = ["WordPress", "Elementor", "Webdesign"]
WEB_LOCATION = "Bayern"

# 2. Офис/Финансы (Мюльдорф + 100км)
OFFICE_QUERIES = [
    "Sachbearbeiter Finanzen", 
    "Finanzbuchhaltung", 
    "Kauffrau Büromanagement", 
    "Buchhalter",
    "Steuerfachangestellte"
]
MY_LOCATION = "84453"
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

def search_jooble(sent, queries, location, radius="0"):
    if not JOOBLE_KEY: return 0
    new_count = 0
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    
    for q in queries:
        print(f"🔍 Jooble: {q} в {location}...")
        payload = {"keywords": q, "location": location, "radius": radius}
        try:
            res = requests.post(url, json=payload, timeout=10)
            jobs = res.json().get("jobs", [])
            for j in jobs:
                j_id = str(j.get("id"))
                if j_id not in sent:
                    msg = (f"✨ <b>{q}</b>\n"
                           f"🏢 {j.get('company', '---')}\n"
                           f"📍 {j.get('location')}\n\n"
                           f"🔗 <a href='{j.get('link')}'>Открыть вакансию</a>")
                    send_tg(msg)
                    sent.add(j_id)
                    new_count += 1
        except: pass
    return new_count

def search_arbeitnow(sent):
    print("🔍 Проверка Arbeitnow (IT/Web)...")
    count = 0
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        for j in res.json().get("data", []):
            j_id = j.get("slug")
            title = j.get("title", "").lower()
            loc = j.get("location", "").lower()
            # Ищем вордпресс по всей Германии/Баварии в Arbeitnow
            if j_id not in sent and ("wordpress" in title or "elementor" in title):
                msg = (f"🌐 <b>Arbeitnow Web</b>\n"
                       f"📝 {j.get('title')}\n"
                       f"🏢 {j.get('company_name')}\n"
                       f"📍 {j.get('location')}\n\n"
                       f"🔗 <a href='{j.get('url')}'>Открыть</a>")
                send_tg(msg)
                sent.add(j_id)
                count += 1
    except: pass
    return count

def main():
    sent = load_sent()
    # Ищем офис рядом
    c1 = search_jooble(sent, OFFICE_QUERIES, MY_LOCATION, RADIUS)
    # Ищем веб в Баварии
    c2 = search_jooble(sent, WEB_QUERIES, WEB_LOCATION, "0")
    # Доп. проверка IT
    c3 = search_arbeitnow(sent)
    
    total = c1 + c2 + c3
    if total > 0:
        with open(DB_FILE, "w") as f: json.dump(list(sent), f)
    print(f"🏁 Итог: отправлено {total}")

if __name__ == "__main__":
    main()
