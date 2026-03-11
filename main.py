async def search_indeed():
    jobs = []
    async with async_playwright() as p:
        # Запускаем браузер с расширенными настройками
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Переходим сначала на главную, чтобы "набить" куки
        await page.goto("https://de.indeed.com/", wait_until="networkidle")
        await asyncio.sleep(2) 
        
        url = "https://de.indeed.com/jobs?q=wordpress&l=Bayern&sort=date"
        print(f"Перехожу к поиску: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            # Ждем чуть дольше
            await asyncio.sleep(5) 
            
            # Проверяем, нет ли на странице слова "Captcha" или "Forbidden"
            content = await page.content()
            if "hCaptcha" in content or "Access Denied" in content:
                print("Упс! Нас засекли (капча или блок).")
                return []

            cards = await page.query_selector_all(".job_seen_beacon")
            # Если классический селектор не сработал, попробуем альтернативный
            if not cards:
                cards = await page.query_selector_all("li .cardOutline")

            print(f"Найдено карточек: {len(cards)}")

            for card in cards[:5]:
                # Внутренние селекторы Indeed часто меняются
                title_el = await card.query_selector("h2.jobTitle span")
                company_el = await card.query_selector("[data-testid='company-name']")
                link_el = await card.query_selector("h2.jobTitle a")
                
                if title_el and link_el:
                    title = await title_el.inner_text()
                    company = await company_el.inner_text() if company_el else "Unknown"
                    href = await link_el.get_attribute("href")
                    link = f"https://de.indeed.com{href}"
                    jobs.append({"title": title, "company": company, "link": link})
        except Exception as e:
            print(f"Ошибка: {e}")
        
        await browser.close()
    return jobs
