import requests
from bs4 import BeautifulSoup

# Ganti URL ini sesuai kebutuhan lo
url = "https://anichin.cafe/throne-of-seal-episode-169-subtitle-indonesia/"

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Cari elemen iframe
    iframe = soup.find("iframe")
    iframe_src = iframe["src"] if iframe else "Tidak ditemukan iframe"

    # Tulis hasil ke file
    with open("hasil_iframe.txt", "w", encoding="utf-8") as f:
        f.write(f"Iframe scraped: {iframe_src}\n")

    print(f"Iframe scraped: {iframe_src}")

except Exception as e:
    print(f"Terjadi error: {e}")
