import os
import asyncio
from playwright.async_api import async_playwright
import requests

# Загрузка переменных из секретов GitHub
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(text):
    if not TOKEN or not CHAT_ID:
        print("Ошибка: Токен или ID чата не найдены в переменных окружения!")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")

async def search_indeed():
    jobs = []
    # Indeed часто блокирует простые запросы, используем Playwright (Chromium)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Маскируемся под обычного пользователя
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://de.indeed.com/jobs?q=wordpress&l=Bayern&sort=date"
        print(f"Открываю страницу: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Ждем появления карточек вакансий
            await page.wait_for_selector(".job_seen_beacon", timeout=10000)
            
            cards = await page.query_selector_all(".job_seen_beacon")
            print(f"Найдено карточек на странице: {len(cards)}")

            for card in cards[:5]: # Берем первые 5 для теста
                title_el = await card.query_selector("h2 span")
                company_el = await card.query_selector("[data-testid='company-name']")
                link_el = await card.query_selector("a")
                
                if title_el and link_el:
                    title = await title_el.inner_text()
                    company = await company_el.inner_text() if company_el else "Не указана"
                    href = await link_el.get_attribute("href")
                    link = f"https://de.indeed.com{href}"
                    
                    jobs.append({"title": title, "company": company, "link": link})
        except Exception as e:
            print(f"Произошла ошибка при парсинге: {e}")
        
        await browser.close()
    return jobs

async def main():
    print("Запуск поиска вакансий...")
    jobs = await search_indeed()
    
    if not jobs:
        print("Вакансий не найдено или доступ заблокирован.")
        return

    for job in jobs:
        message = (
            f"💻 <b>{job['title']}</b>\n"
            f"🏢 {job['company']}\n\n"
            f"🔗 <a href='{job['link']}'>Открыть вакансию</a>"
        )
        send_telegram_message(message)
        print(f"Отправлено: {job['title']}")

if __name__ == "__main__":
    asyncio.run(main())
