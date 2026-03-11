import requests
from bs4 import BeautifulSoup

def search_indeed(keyword, location):
    
    jobs = []

    url = f"https://de.indeed.com/jobs?q={keyword}&l={location}&sort=date"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.select(".job_seen_beacon")

    for job in cards[:10]:

        title = job.select_one("h2 span")
        company = job.select_one(".companyName")
        link = job.select_one("a")

        if title and link:

            jobs.append({
                "title": title.text.strip(),
                "company": company.text.strip() if company else "",
                "link": "https://de.indeed.com" + link["href"]
            })

    return jobs
