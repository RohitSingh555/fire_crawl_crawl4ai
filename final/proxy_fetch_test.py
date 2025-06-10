import requests
from bs4 import BeautifulSoup

def fetch_proxies():
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    proxy_table = soup.find("table", id="proxylisttable")

    proxies = []
    for row in proxy_table.tbody.find_all("tr"):
        cols = row.find_all("td")
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        https = cols[6].text.strip()

        if https == "yes":
            proxies.append(f"{ip}:{port}")
    return proxies

if __name__ == "__main__":
    proxy_list = fetch_proxies()
    print("Fetched HTTPS Proxies:")
    for proxy in proxy_list[:20]:  # Limit output to first 20
        print(proxy)
