import json
import time
import base64
import binascii
import random
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver():
    """Menyiapkan driver Selenium baru untuk setiap 'sesi'."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Kita tetap pakai user-agent yang wajar
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
    
    print("  [Manusia Baru Diciptakan] Membuka browser baru...")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5) # Waktu tunggu implisit yang lebih pendek, kita akan lebih mengandalkan jeda eksplisit
    return driver

def human_like_pause(min_seconds=1.5, max_seconds=4.0):
    """Memberikan jeda acak seperti manusia yang sedang berpikir/membaca."""
    waktu_tunggu = random.uniform(min_seconds, max_seconds)
    # print(f"    (Berpikir sejenak selama {waktu_tunggu:.2f} detik...)")
    time.sleep(waktu_tunggu)

def human_like_scroll(driver):
    """Mensimulasikan gerakan scrolling manusia."""
    print("    (Melihat-lihat halaman dengan scroll...)")
    try:
        # Scroll ke bawah perlahan
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        human_like_pause(0.5, 1.5)
        # Scroll sampai paling bawah
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception:
        pass # Abaikan jika ada error saat scroll

def initial_warmup(driver):
    """
    Pemanasan: Bertingkah seperti manusia yang baru buka website.
    Tidak langsung ke tujuan, tapi 'muter-muter' dulu.
    """
    print("  [Pemanasan] Mencoba berkelakuan seperti manusia...")
    try:
        # 1. Kunjungi halaman utama
        print("    > Mengunjungi Halaman Utama...")
        driver.get("https://anichin.cafe/")
        human_like_pause()
        
        # 2. Scroll sedikit
        human_like_scroll(driver)
        
        # 3. Pura-pura klik link jadwal (jika ada)
        print("    > Pura-pura penasaran dengan Jadwal Rilis...")
        schedule_link = driver.find_elements(By.XPATH, "//a[contains(text(), 'Schedule')]")
        if schedule_link:
            driver.get(schedule_link[0].get_attribute('href'))
            human_like_pause()
            human_like_scroll(driver)

        print("  [Pemanasan Selesai] Bot sekarang lebih 'hangat'.")
        return True
    except Exception as e:
        print(f"  Gagal melakukan pemanasan: {e}")
        return False

def get_episode_links(driver, series_url):
    print(f"  Mencari episode di: {series_url.split('/')[-2]}")
    try:
        driver.get(series_url)
        human_like_pause()
        human_like_scroll(driver) # Scroll dulu sebelum mencari
        
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".episodelist ul li a"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        episodelist_tags = soup.select(".episodelist ul li a")
        
        episodes = [{'title': a.select_one('h4').text.strip(), 'url': a['href']} for a in episodelist_tags]
        episodes.reverse()
        print(f"  > Ditemukan {len(episodes)} episode.")
        return episodes

    except TimeoutException:
        print("  > Gagal (Timeout): Daftar episode tidak muncul. Mungkin halaman ini benar-benar kosong.")
        driver.save_screenshot(f"debug_timeout_{series_url.split('/')[-2]}.png")
        return []

def get_video_iframe(driver, episode_url):
    """Mengambil iframe, logika decode Base64 masih sama."""
    try:
        driver.get(episode_url)
        human_like_pause(0.8, 2.0)
        
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.mirror, #pembed iframe"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Logika ini sudah benar dari awal, jadi kita pertahankan
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
                    except:
                        continue
        return {'main_video': main_video, 'mirrors': mirrors}
    except Exception:
        print(f"    > Gagal mengambil video dari halaman episode: {episode_url.split('/')[-2]}")
        return {'main_video': None, 'mirrors': []}

# --- MAIN LOGIC YANG DIUBAH TOTAL ---

try:
    with open('anime_list.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
except FileNotFoundError:
    print("Error: File 'anime_list.json' tidak ditemukan.")
    exit()

full_result = []

for anime in anime_data['anime_list']:
    driver = None # Pastikan driver kosong di awal loop
    try:
        # --- TAHAP 1: Buat Sesi Browser Baru untuk setiap Anime ---
        driver = setup_driver()
        initial_warmup(driver) # Lakukan ritual pemanasan
        
        print(f"\n{'='*10} Scraping: {anime['title']} {'='*10}")
        episodes = get_episode_links(driver, anime['url'])
        
        if not episodes:
             print(f"  Tidak ada episode ditemukan untuk {anime['title']}, lanjut ke anime berikutnya.")
             # Tetap simpan hasilnya meski kosong
             full_result.append({'title': anime['title'], 'url': anime['url'], 'episodes': []})
             continue

        episode_results = []
        for ep in episodes[:2]: # Batasi 2 episode per anime untuk testing cepat
            print(f"   Processing Episode: {ep['title']}")
            video_data = get_video_iframe(driver, ep['url'])
            episode_results.append({
                'episode_title': ep['title'],
                'episode_url': ep['url'],
                'main_video_iframe': video_data['main_video'],
                'mirror_servers': video_data['mirrors']
            })
            human_like_pause(2.0, 5.0) # Jeda panjang antar episode

        full_result.append({
            'title': anime['title'],
            'url': anime['url'],
            'episodes': episode_results
        })

    except Exception as e:
        print(f"Error besar terjadi saat memproses {anime['title']}: {e}")
        if driver:
            driver.save_screenshot(f"debug_fatal_error_{anime['title']}.png")

    finally:
        # --- TAHAP AKHIR: Tutup Browser, Hapus Jejak ---
        if driver:
            print("  [Sesi Selesai] Menutup browser untuk anime ini.")
            driver.quit()

# Simpan hasil akhir
with open('scraped_result.json', 'w', encoding='utf-8') as f:
    json.dump(full_result, f, indent=4, ensure_ascii=False)

print("\nScraping selesai. Hasil disimpan di 'scraped_result.json'.")
