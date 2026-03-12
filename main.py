import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Публичные ключи Adzuna
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

def search_adzuna(sent, query, loc, dist, is_remote=False):
    print(f"📡 Adzuna: {query} ({'Remote' if is_remote else loc})...")
    url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
    
    # Если ищем удаленку, добавляем слово 'home office' или 'remote' в запрос
    search_query = f"{query} remote" if is_remote else query
    
    params = {
        "app_id": ADZ_ID, 
        "app_key": ADZ_KEY, 
        "results_per_page": 10, 
        "what": search_query, 
        "where": loc, 
        "distance": dist
    }
    
    found = []
    try:
        res = requests.get(url, params=params, timeout=10).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                title = j.get("title", "Без названия")
                company = j.get("company", {}).get("display_name", "---")
                location = j.get("location", {}).get("display_name", loc)
                link = j.get("redirect_url")
                
                tag = "🌐 REMOTE" if is_remote else "📍 OFFICE"
                msg = (f"{tag} <b>{query}</b>\n"
                       f"📝 {title}\n"
                       f"🏢 {company}\n"
                       f"📍 {location}\n\n"
                       f"🔗 <a href='{link}'>Открыть вакансию</a>")
                found.append((j_id, msg))
    except: pass
    return found

def search_ovb(sent):
    print("📡 Проверка OVB Stellen (Регион)...")
    found = []
    url = "https://www.ovbstellen.de/jobs-landkreis-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all('a', href=True)
        for item in items:
            href = item['href']
            if "/stellenangebot/" in href:
                if not href.startswith('http'): href = "https://www.ovbstellen.de" + href
                title = item.get_text(strip=True)
                if len(title) < 10: continue
                
                j_id = f"ovb-{href}"
                if j_id not in sent:
                    msg = (f"🏠 <b>OVB Local (Mühldorf)</b>\n"
                           f"📝 {title}\n\n"
                           f"🔗 <a href='{href}'>Открыть вакансию</a>")
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. WordPress / Elementor — ищем REMOTE по всей Германии
    for q in ["WordPress", "Elementor"]:
        new_jobs.extend(search_adzuna(sent, q, "Deutschland", 0, is_remote=True))
    
    # 2. Офис (Sachbearbeiter / Finanzen) — ищем в радиусе 50км от Мюльдорфа
    for q in ["Sachbearbeiter", "Finanzen", "Buchhaltung"]:
        new_jobs.extend(search_adzuna(sent, q, "84453", 50))
    
    # 3. Местный поиск OVB (Ландкрайс Мюльдорф)
    new_jobs.extend(search_ovb(sent))

    if new_jobs:
        # Отправляем максимум 15 новых, чтобы не заспамить
        for j_id, msg in new_jobs[:50]: 
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"✅ Успех! Найдено и отправлено: {len(new_jobs)}")
    else:
        # Контрольное сообщение, что бот работает
        send_tg("🤖 Проверка выполнена. Новых вакансий (Remote/Local) пока нет. Продолжаю дежурство!")
        print("Новых вакансий не обнаружено.")

if __name__ == "__main__":
    main()
