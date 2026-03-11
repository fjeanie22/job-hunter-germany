import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

# Упрощаем до предела для теста
OFFICE_QUERIES = ["Finanzen", "Buchhaltung", "Büro", "Kauffrau"]
WEB_QUERIES = ["WordPress", "Elementor"]

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_jooble(sent, queries, location, radius="50"):
    if not JOOBLE_KEY: return 0
    new_count = 0
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    
    for q in queries:
        print(f"📡 Запрос Jooble: {q} в {location}...")
        payload = {"keywords": q, "location": location, "radius": radius}
        try:
            res = requests.post(url, json=payload, timeout=15)
            data = res.json()
            
            # Отладка: что пришло?
            if "jobs" not in data:
                print(f"⚠️ Ответ Jooble для {q}: {data}")
                continue
                
            jobs = data.get("jobs", [])
            print(f"✅ Найдено {len(jobs)} вакансий по запросу {q}")
            
            for j in jobs:
                j_id = str(j.get("id"))
                if j_id not in sent:
                    msg = (f"🏢 <b>{q}</b>\n"
                           f"📝 {j.get('title')}\n"
                           f"🏢 {j.get('company', '---')}\n"
                           f"📍 {j.get('location')}\n\n"
                           f"🔗 <a href='{j.get('link')}'>Открыть</a>")
                    send_tg(msg)
                    sent.add(j_id)
                    new_count += 1
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
    return new_count

def main():
    sent = load_sent()
    
    # Ищем офис (Мюльдорф и окрестности)
    print("--- ПОИСК ОФИС ---")
    c1 = search_jooble(sent, OFFICE_QUERIES, "84453", "50")
    
    # Ищем Web (Бавария)
    print("--- ПОИСК WEB ---")
    c2 = search_jooble(sent, WEB_QUERIES, "Bayern", "0")
    
    total = c1 + c2
    if total > 0:
        with open(DB_FILE, "w") as f: json.dump(list(sent), f)
    
    print(f"🏁 Завершено. Отправлено: {total}")

if __name__ == "__main__":
    main()
