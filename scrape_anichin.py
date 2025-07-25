import json
import time
import base64
import binascii
import random
import os
from bs4 import BeautifulSoup

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver(proxy_url):
    """Setup driver dengan satu proxy spesifik."""
    selenium_wire_options = {
        'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'}
    }
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options, seleniumwire_options=selenium_wire_options)
    driver.set_page_load_timeout(45) # Timeout halaman yang lebih lama
    return driver

# Fungsi-fungsi helper seperti get_episode_links, get_video_iframe, dll.
# bisa dicopy dari jawaban sebelumnya, tidak ada yang berubah.
def get_episode_links(driver, series_url):
    print(f"  Mencari episode di: {series_url.split('/')[-2]}")
    try:
        driver.get(series_url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".episodelist ul li a")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        episodes = [{'title': a.select_one('h4').text.strip(), 'url': a['href']} for a in soup.select(".episodelist ul li a")]
        episodes.reverse()
        print(f"  > Ditemukan {len(episodes)} episode.")
        return episodes
    except Exception as e:
        print(f"  > Gagal mendapatkan list episode: {type(e).__name__}")
        return []

def get_video_iframe(driver, episode_url):
    try:
        driver.get(episode_url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "select.mirror, #pembed iframe")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        iframe = soup.select_one('#embed_holder .player-embed iframe, #pembed iframe')
        main_video = iframe['src'] if iframe and iframe.has_attr('src') else None
        mirrors = []
        mirror_select = soup.find('select', class_='mirror')
        if mirror_select:
            for option in mirror_select.find_all('option'):
                encoded_value = option.get('value')
                if encoded_value:
                    try:
                        decoded = base64.b64decode(encoded_value).decode('utf-8')
                        iframe_soup = BeautifulSoup(decoded, 'html.parser')
                        iframe_tag = iframe_soup.find('iframe')
                        if iframe_tag and iframe_tag.get('src'):
                            mirrors.append({'server': option.text.strip(), 'iframe': iframe_tag['src']})
                    except: continue
        return {'main_video': main_video, 'mirrors': mirrors}
    except:
        return {'main_video': None, 'mirrors': []}

# --- MAIN LOGIC DENGAN ROTASI ---
if __name__ == "__main__":
    try:
        with open('live_proxies.txt', 'r') as f:
            live_proxies = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("[ERROR] File 'live_proxies.txt' tidak ditemukan. Jalankan checker dulu.")
        live_proxies = []

    if not live_proxies:
        print("[SELESAI] Tidak ada proxy yang hidup, tidak bisa melanjutkan scraping.")
        # Buat file hasil kosong agar workflow tidak error
        with open('scraped_result.json', 'w') as f:
            json.dump([], f)
        exit()

    print(f"--- Memulai Scraper Utama dengan {len(live_proxies)} Proxy Aktif ---")
    
    with open('anime_list.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)

    full_result = []
    
    # Loop utama untuk setiap anime
    for i, anime in enumerate(anime_data['anime_list']):
        # --- INI DIA LOGIKA ROTASI IP-MU ---
        proxy_index = i % len(live_proxies)
        proxy_to_use = live_proxies[proxy_index]
        # ------------------------------------

        print(f"\n{'='*10} Scraping: {anime['title']} {'='*10}")
        print(f"  Menggunakan Proxy ke-{proxy_index + 1}: {proxy_to_use}")

        driver = None
        try:
            driver = setup_driver(proxy_to_use)
            episodes = get_episode_links(driver, anime['url'])
            
            episode_results = []
            if episodes:
                # Batasi 1 episode per anime untuk testing
                for ep in episodes[:1]:
                    print(f"    Processing Episode: {ep['title']}")
                    video_data = get_video_iframe(driver, ep['url'])
                    episode_results.append({
                        'episode_title': ep['title'],
                        'episode_url': ep['url'],
                        'main_video_iframe': video_data['main_video'],
                        'mirror_servers': video_data['mirrors']
                    })
                    time.sleep(random.uniform(2, 4)) # Jeda antar episode
            
            full_result.append({'title': anime['title'], 'url': anime['url'], 'episodes': episode_results})

        except Exception as e:
            print(f"  [ERROR BESAR] Gagal total saat memproses {anime['title']}: {e}")
            full_result.append({'title': anime['title'], 'url': anime['url'], 'episodes': []}) # Catat sebagai gagal
        
        finally:
            if driver:
                driver.quit() # Selalu tutup driver setelah selesai satu anime
    
    # Simpan hasil akhir
    with open('scraped_result.json', 'w', encoding='utf-8') as f:
        json.dump(full_result, f, indent=4, ensure_ascii=False)
    
    print("\n--- Scraping Selesai ---")
