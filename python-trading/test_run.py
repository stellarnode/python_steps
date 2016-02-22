# import sys
# print "\n".join(sys.path)
# sys.path.append("/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages")

import pandas as pd
import matplotlib.pyplot as plt

def get_max_close(symbol):
    df = pd.read_csv("data/{}.csv".format(symbol))
    return df["Close"].max()

def get_mean_volume(symbol):
    df = pd.read_csv("data/{}.csv".format(symbol))
    return df["Volume"].mean()

def test_run():
    df = pd.read_csv("data/AAPL.csv")
    print df.head(5)
    print df.tail(5)

    for symbol in ["AAPL", "HCP"]:
        print "Max close: ", symbol, get_max_close(symbol)

    for symbol in ["AAPL", "HCP"]:
        print "Mean volume: ", symbol, get_mean_volume(symbol)

    print "Adj Close"
    df["Adj Close"].plot()
    plt.show()

    print "High"
    df["High"].plot()
    plt.title("High prices, AAPL")
    plt.xlabel("Time")
    plt.ylabel("High")
    plt.show()

    print "Close, ", "Adj Close"
    df[["Close", "Adj Close"]].plot()
    plt.show()


if __name__ == "__main__":
    test_run()

