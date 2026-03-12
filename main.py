import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
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

def search_ovb(sent):
    print("📡 Проверка OVB Stellen...")
    found = []
    # Берем общую страницу региона, там вакансий всегда больше
    url = "https://www.ovbstellen.de/jobs-landkreis-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # На OVB вакансии часто лежат в тегах <h3> или <h2> внутри ссылок
        items = soup.find_all('a', href=True)
        for item in items:
            href = item['href']
            # Ищем ссылки, которые ведут на конкретные предложения
            if "/stellenangebot/" in href:
                if not href.startswith('http'):
                    href = "https://www.ovbstellen.de" + href
                
                # Извлекаем текст (название вакансии)
                title = item.get_text(strip=True)
                if not title or len(title) < 10: continue # Пропускаем короткие обрывки
                
                j_id = f"ovb-{href}"
                if j_id not in sent:
                    msg = f"🏠 <b>OVB (Регион)</b>\n📝 {title}\n🔗 <a href='{href}'>Открыть</a>"
                    found.append((j_id, msg))
    except Exception as e:
        print(f"❌ Ошибка OVB: {e}")
    return found

def search_adzuna(sent, query, loc, dist):
    url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = {"app_id": ADZ_ID, "app_key": ADZ_KEY, "results_per_page": 5, "what": query, "where": loc, "distance": dist}
    found = []
    try:
        res = requests.get(url, params=params, timeout=10).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                msg = f"📌 <b>{query}</b> (Adzuna)\n🏢 {j.get('company', {}).get('display_name')}\n📍 {j.get('location', {}).get('display_name')}\n🔗 <a href='{j.get('redirect_url')}'>Открыть</a>"
                found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. Проверяем местный сайт OVB
    new_jobs.extend(search_ovb(sent))
    
    # 2. Проверяем Adzuna (для примера возьмем главные слова)
    for q in ["Sachbearbeiter", "WordPress"]:
        new_jobs.extend(search_adzuna(sent, q, "84453", 50))

    if new_jobs:
        # Отправляем только первые 10, чтобы не спамить
        for j_id, msg in new_jobs[:10]:
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"✅ Отправлено вакансий: {len(new_jobs)}")
    else:
        send_tg("🤖 Проверка выполнена: новых вакансий на OVB и Adzuna пока нет. Жду следующий запуск!")

if __name__ == "__main__":
    main()
