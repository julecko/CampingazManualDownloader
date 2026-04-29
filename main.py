from bs4 import BeautifulSoup
import requests
from pathlib import Path
import json

DOWNLOAD_FOLDER = "files"
MAIN_URL = "https://www.campingaz.cz/en/after-sales-eu.html"
PRODUCT_LINE_URL = "https://www.campingaz.cz/on/demandware.store/Sites-campingazcz-Site/en_CZ/DocumentLookup-GetSubFolders?fdid=%s&rootFolderId=aftersales"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/145.0.3800.58",
    "Sec-GPC": "1",
}

def ensure_directory(folder_path: str) -> None:
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def extract_categories(url: str):
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

def extract_product_line(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Response is not valid JSON")
        return

    subfolders = data.get("selectedSubFolders", [])

    for item in subfolders:
        id = item.get("id")
        name = item.get("displayValue")

        if not id:
            continue

        yield {
            "id": id,
            "name": name
        }

def main():
    ensure_directory(DOWNLOAD_FOLDER)

    products = extract_categories(MAIN_URL)
    if not products:
        print("Products extraction failure")
        return 1
    
    for product in products:
        print("Processing %s" % product["name"])
        product_line_list = extract_product_line(PRODUCT_LINE_URL % product["id"])
        for product_line in product_line_list:
            print(product_line)
            break
        break

if __name__ == "__main__":
    exit(main())