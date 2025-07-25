import requests
from bs4 import BeautifulSoup
import json

# Ganti dengan URL episode yang ingin diuji
url = "https://anichin.cafe/throne-of-seal-episode-169-subtitle-indonesia/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

iframe = soup.find("iframe")
iframe_src = iframe["src"] if iframe else "NOT FOUND"

data = {
    "url": url,
    "iframe_src": iframe_src
}

with open("result.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ Iframe scraped:", iframe_src)
