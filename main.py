from bs4 import BeautifulSoup
import requests


MAIN_URL = "https://www.campingaz.cz/en/after-sales-eu.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/145.0.3800.58",
    "Sec-GPC": "1",
}


def extract_categories(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    select = soup.find("select", {"id": "productCategory"})
    if not select:
        return

    for option in select.find_all("option"):
        value = option.get("value")
        name = option.get_text(strip=True)

        if not value:
            continue

        yield {
            "id": value,
            "name": name
        }


def main():
    products = extract_categories(MAIN_URL)
    if not products:
        print("Products extraction failure")
        return 1
    
    for product in products:
        ...

if __name__ == "__main__":
    exit(main())