import re
import requests
import time
import os
import sys
import logging
from urllib.parse import unquote, urlparse, parse_qs

# Suppress unwanted selenium logs
sys.stderr = open(os.devnull, 'w')
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)
logging.getLogger('seleniumwire').setLevel(logging.ERROR)

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def validate_links(links):
    valid_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    for link in links:
        try:
            resp = requests.head(link, headers=headers, timeout=10)
            if resp.status_code == 200:
                valid_links.append(link)
            else:
                print(f"❌ Fehler {resp.status_code}: {link}")
        except Exception as e:
            print(f"⚠️ Fehler bei Validierung: {link} -> {e}")
    return valid_links

def extract_title_from_url(url):
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if "t" in query:
            return unquote(query["t"][0])
    except:
        pass
    return "Unbekannter Titel"

def select_primary_m3u8(links):
    for l in links:
        if "master.m3u8" in l:
            return l
    for l in links:
        if "index" in l and ".m3u8" in l:
            return l
    if links:
        return links[0]
    return None

def scrape_voe_m3u8(voe_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])

    driver = webdriver.Chrome(options=options)
    driver.scopes = ['.*\\.m3u8.*']

    try:
        driver.get(voe_url)

        try:
            spin = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.spin"))
            )
            spin.click()
        except:
            print("⚠️ Kein Play-Button gefunden (evtl. Auto-Play)")

        time.sleep(7)

        m3u8_links = set()
        for request in driver.requests:
            try:
                if request.response and request.url and ".m3u8" in request.url:
                    m3u8_links.add(request.url)
            except Exception as e:
                print(f"⚠️ Fehler bei request: {e}")
                continue

        return list(m3u8_links), voe_url

    finally:
        driver.quit()

def get_best_m3u8_from_voe(voe_url):
    try:
        results, source_url = scrape_voe_m3u8(voe_url)
        if not results:
            print("❌ Keine .m3u8 Ergebnisse.")
            return None

        valid = validate_links(results)
        best = select_primary_m3u8(valid)
        return best

    except Exception as e:
        print(f"🔥 Fehler beim Verarbeiten: {e}")
        return None
