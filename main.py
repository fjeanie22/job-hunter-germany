import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Константы для Adzuna (это публичные ключи для тестов, они работают стабильно)
ADZUNA_APP_ID = "c6e9389e"
ADZUNA_APP_KEY = "3a20349890d291936c53e0ec3e69188e"

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

def search_adzuna(sent, query, location, distance=50):
    print(f"📡 Adzuna: ищу {query} в {location} (+{distance}км)...")
    new_count = 0
    # Страница 1, страна de (Германия)
    url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 10,
        "what": query,
        "where": location,
        "distance": distance,
        "content-type": "application/json"
    }
    
    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
        results = data.get("results", [])
        print(f"✅ Найдено {len(results)} вакансий")
        
        for j in results:
            j_id = str(j.get("id"))
            if j_id not in sent:
                title = j.get("title", "Без названия")
                company = j.get("company", {}).get("display_name", "Не указана")
                loc = j.get("location", {}).get("display_name", location)
                link = j.get("redirect_url")
                
                msg = (f"📍 <b>{location} | {query}</b>\n"
                       f"📝 {title}\n"
                       f"🏢 {company}\n"
                       f"📍 {loc}\n\n"
                       f"🔗 <a href='{link}'>Открыть вакансию</a>")
                
                send_tg(msg)
                sent.add(j_id)
                new_count += 1
    except Exception as e:
        print(f"❌ Ошибка Adzuna: {e}")
    return new_count

def main():
    sent = load_sent()
    total = 0
    
    # 1. Поиск ОФИСА (Мюльдорф + 50км)
    # Ищем широкими категориями по очереди
    for q in ["Finanzen", "Buchhaltung", "Sachbearbeiter"]:
        total += search_adzuna(sent, q, "84453", 50)
        
    # 2. Поиск WEB (Вся Бавария)
    for q in ["WordPress", "Elementor"]:
        total += search_adzuna(sent, q, "Bayern", 0)
    
    if total > 0:
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
            
    print(f"🏁 Завершено. Отправлено новых: {total}")

if __name__ == "__main__":
    main()
