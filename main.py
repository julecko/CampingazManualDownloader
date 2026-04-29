from bs4 import BeautifulSoup
import requests
from pathlib import Path
import urllib3
from urllib.parse import urlparse
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOWNLOAD_FOLDER = "files"
MAIN_URL = "https://www.campingaz.cz/en/after-sales-eu.html"
PRODUCT_LINE_URL = "https://www.campingaz.cz/on/demandware.store/Sites-campingazcz-Site/en_CZ/DocumentLookup-GetSubFolders?fdid=%s&rootFolderId=aftersales"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-GPC": "1",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0"
}

BURP_PROXY = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}

import re

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)

    name = re.sub(r'\s+', "_", name)

    return name[:150]

def make_request(url: str, extra_headers: dict = None) -> requests.Response | None:
    parsed = urlparse(url)

    headers = {
        **HEADERS,
        "Host": parsed.netloc,
        **(extra_headers or {})
    }
    try:
        response = requests.get(
            url,
            headers=headers,
            proxies=BURP_PROXY,
            verify=False,  # Burp Suite uses a self-signed cert
            timeout=60
        )
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"[ERROR] Request failed for {url}: {e}")
        return None


def ensure_directory(folder_path: str) -> None:
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def extract_categories(url: str):
    response = make_request(url)
    if not response:
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
        yield {"id": value, "name": name}


def extract_product_line(url: str):
    response = make_request(url)
    if not response:
        return

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Response is not valid JSON")
        return

    for item in data.get("selectedSubFolders", []):
        id_ = item.get("id")
        name = item.get("displayValue")
        if not id_:
            continue
        yield {"id": id_, "name": name}


def extract_products(url: str):
    response = make_request(url, extra_headers={"Cookie": ""})
    if not response:
        return

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Response is not valid JSON")
        return

    for item in data.get("selectedSubFolders", []):
        id_ = item.get("id")
        name = item.get("displayValue")
        if not id_:
            continue
        yield {"id": id_, "name": name}

def extract_documents(url: str):
    response = make_request(url, extra_headers={"Cookie": ""})
    if not response:
        return

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Response is not valid JSON")
        return
    for item in data.get("documentDashMetadata", []):
        url = item.get("url")
        name = item.get("displayText")
        if not url or not name:
            continue
        yield {"url": url, "name": name}

def download_document(url: str, filename):
    content = make_request(url)
    if not content:
        return
    with open(DOWNLOAD_FOLDER + "\\" + filename, "wb") as file:
        file.write(content.content)

def format_name(name: str):
    return name.replace(" ", "_")

def main():
    ensure_directory(DOWNLOAD_FOLDER)

    products = extract_categories(MAIN_URL)
    if not products:
        print("Products extraction failure")
        return 1
    counter = 1
    for product in products:
        product_line_list = extract_product_line(PRODUCT_LINE_URL % product["id"])
        for product_line in product_line_list:
            products = extract_products(PRODUCT_LINE_URL % product_line["id"])
            for product in products:
                print(f"Product {counter}: {product["name"]}")
                documents = extract_documents(PRODUCT_LINE_URL % product["id"])
                for document in documents:
                    download_document(document["url"], sanitize_filename(format_name(product["name"] + "-" + document["name"])))
                    counter += 1


if __name__ == "__main__":
    exit(main())