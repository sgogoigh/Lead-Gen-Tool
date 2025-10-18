import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
from concurrent.futures import ThreadPoolExecutor
import functools

DEFAULT_HEADERS = {
    "User-Agent": "LeadGenDemoBot/1.0 (+https://example.com)"
}

async def fetch(session, url, timeout=15):
    try:
        async with session.get(url, timeout=timeout) as resp:
            text = await resp.text()
            return url, resp.status, text
    except Exception as e:
        return url, getattr(e, "status", None), None

async def _scrape_async(urls, workers=5):
    results = []
    connector = aiohttp.TCPConnector(limit_per_host=workers)
    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS, connector=connector) as session:
        tasks = [fetch(session, u) for u in urls]
        for fut in asyncio.as_completed(tasks):
            res = await fut
            results.append(res)
    return results

def parse_html(url, status, html):
    rec = {
        "source_url": url,
        "http_status": status,
        "title": None,
        "meta_description": None,
        "company_name": None,
        "domain": None,
        "emails_found": [],
        "phone_found": None,
    }
    if not html:
        return rec
    soup = BeautifulSoup(html, "html.parser")
    t = soup.title.string.strip() if soup.title and soup.title.string else None
    rec["title"] = t
    desc = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", attrs={"property":"og:description"})
    if desc and desc.get("content"):
        rec["meta_description"] = desc.get("content").strip()
    # Heuristics for company name
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        rec["company_name"] = h1.get_text(strip=True)
    # fallback: domain
    parsed = tldextract.extract(url)
    domain = ".".join([d for d in [parsed.domain, parsed.suffix] if d])
    rec["domain"] = domain
    # find mailto links
    mails = set()
    for a in soup.select("a[href^=mailto]"):
        href = a.get("href")
        if href:
            mail = href.split(":",1)[1].split("?")[0]
            mails.add(mail)
    # quick pattern find
    text = soup.get_text(" ", strip=True)
    import re
    possible_emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
    mails |= possible_emails
    rec["emails_found"] = list(mails)
    phones = re.findall(r"(\+\d{1,3}[\s-]?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4})", text)
    if phones:
        rec["phone_found"] = phones[0]
    return rec

def scrape_urls(urls, workers=5):
    """Public function — returns list of record dicts."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(_scrape_async(urls, workers=workers))
    parsed = [parse_html(url, status, html) for (url,status,html) in results]
    return parsed