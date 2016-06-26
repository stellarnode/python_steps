# Draft

import urllib2
import re

def compose_url(ticker):
    url = "http://finviz.com/quote.ashx?t=" + ticker.upper()
    # print(url)
    return url

def open_url(url):
    try:
        response = urllib2.urlopen(url)
        data = response.read()
    except:
        data = "not found"
    return data

def find_atr(data):
    if data != "not found":
        atr_search = data.split('ATR</td><td width="8%" class="snapshot-td2" align="left"><b>')[1]
        # print(atr_search)
        atr = re.match('\d*.?\d*', atr_search).group(0)
        atr = float(atr)
        # atr = int(atr) if float(atr) == int(atr) else float(atr)
    else:
        atr = data
    return atr

def find_current_price(data):
    if data != "not found":
        price_search = data.split('Price</td><td width="8%" class="snapshot-td2" align="left"><b>')[1]
        price = re.search('(\d*.?\d*)\<\/span\>', price_search).group(0)
        price = re.search('\d*.?\d*', price).group(0)
        price = float(price)
    else:
        price = data
    return price

def find_analyst_target_price(data):
    if data != "not found":
        price_search = data.split('Target Price</td><td width="8%" class="snapshot-td2" align="left"><b>')[1]
        # print(price_search)
        price = re.search('\d*.?\d*</span>', price_search).group(0)
        price = re.search('\d*.?\d*', price).group(0)
        price = float(price)
    else:
        price = data
    return price

def reco(ticker, current_price, atr, analyst_target_price=0):
    print("--- " + ticker.upper() + " ---")

    if current_price == "not found" or atr == "not found":
        print("Info not found. Check if TICKER spelling is correct.")
        print("-" * 10 + "\n")
    else:
        print("Current price: %.2f" % current_price)
        print("ATR: %.2f" % atr)
        print("Analyst target price: %.2f" % analyst_target_price)
        print("Stop loss for LONG position should be between: %.2f and %.2f" % (current_price - atr * 1, current_price - atr * 3))
        print("Target for LONG posistion should be between: %.2f and %.2f" % (current_price + atr * 3, current_price + atr * 3 * 3))

        if current_price + atr * 3 > analyst_target_price:
            print("RECO: Stock NOT recommended for LONG position based on analyst target price")

        print("-" * 14 + "\n")


def main():
    print("Starting...")
    tickers = raw_input("What tickers are you interested in?\n > ")
    print
    pat = re.compile("[\s\,\.]")
    tickers = re.split(pat, tickers)
    tickers = filter(lambda x: x != "", tickers)

    for ticker in tickers:
        if ticker == "":
            continue
        url = compose_url(ticker)
        data = open_url(url)
        atr = find_atr(data)

        if atr != "not found":
            current_price = find_current_price(data)
            analyst_target_price = find_analyst_target_price(data)
        else:
            current_price = "not found"
            analyst_target_price = "not found"

        reco(ticker, current_price, atr, analyst_target_price)



if __name__ == "__main__":
    main()
