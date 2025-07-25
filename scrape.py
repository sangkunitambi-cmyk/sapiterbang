import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://anichin.click/?id=v6udn7o"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

try:
    # Bypass SSL verification
    response = requests.get(url, headers=headers, allow_redirects=True, verify=False)
    print("Final URL:", response.url)

    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe")
    iframe_src = iframe["src"] if iframe else "Tidak ditemukan iframe dalam redirect"

    with open("hasil_okru.txt", "w", encoding="utf-8") as f:
        f.write(f"Final URL: {response.url}\n")
        f.write(f"OK.ru Embed: {iframe_src}\n")
        f.write(f"Scraped at: {datetime.now()}\n")

    print("OK.ru Embed:", iframe_src)

except Exception as e:
    print("Terjadi error:", e)
