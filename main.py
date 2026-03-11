import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

# Список запросов для Jooble (будем искать по очереди)
QUERIES = ["Sachbearbeiter", "Kauffrau", "Büro", "WordPress", "Webdesign"]
LOCATION = "Mühldorf am Inn"
RADIUS = "50" # в км

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def search_jooble(sent):
    if not JOOBLE_KEY:
        print("❌ JOOBLE_KEY не найден")
        return 0
    
    new_count = 0
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    
    for q in QUERIES:
        print(f"🔍 Ищу в Jooble: {q}...")
        payload = {"keywords": q, "location": LOCATION, "radius": RADIUS}
        try:
            res = requests.post(url, json=payload, timeout=10)
            data = res.json()
            jobs = data.get("jobs", [])
            
            for j in jobs:
                j_id = str(j.get("id"))
                if j_id not in sent:
                    # Формируем сообщение
                    company = j.get("company", "Не указана")
                    msg = (f"✨ <b>Найдено: {q}</b>\n"
                           f"📝 {j.get('title')}\n"
                           f"🏢 {company}\n"
                           f"📍 {j.get('location')}\n\n"
                           f"🔗 <a href='{j.get('link')}'>Открыть вакансию</a>")
                    
                    send_tg(msg)
                    sent.add(j_id)
                    new_count += 1
        except Exception as e:
            print(f"❌ Ошибка на запросе {q}: {e}")
            
    return new_count

def main():
    sent = load_sent()
    total_new = search_jooble(sent)
    
    if total_new > 0:
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
            
    print(f"🏁 Итог: отправлено {total_new} вакансий")

if __name__ == "__main__":
    main()
