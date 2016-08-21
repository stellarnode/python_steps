from bs4 import BeautifulSoup
import requests
import pandas as pd

url = "http://finviz.com/quote.ashx?t=fb"

response = requests.get(url)
content = response.content
soup = BeautifulSoup(content)
snapshot_table = soup.find_all("table", {"class": "snapshot-table2"})

data = []

rows = snapshot_table[0].findAll("tr")

for tr in rows:
    cols = tr.findAll("td")

    for td in cols:
        text = td.find(text=True)
        data.append(text)

stock_info = {}

for x in range(0, len(data)):
    if x % 2 == 0:
        stock_info[data[x]] = ""
    else:
        stock_info[data[x-1]] = data[x]

print(stock_info)
print("Volume: ", stock_info['Volume'])
