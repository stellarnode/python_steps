# Using numpy statistics

import numpy as np
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt

def get_data(tickers, start, end):
    dates = pd.date_range(start, end)
    df = pd.DataFrame(index=dates)
    for ticker in tickers:
        dftemp = web.DataReader(ticker, "yahoo", start, end)
        dftemp = pd.DataFrame(dftemp, columns=["Adj Close"])
        dftemp = dftemp.rename(columns={"Adj Close": ticker})
        df = df.join(dftemp, how="inner")
    return df

def plot_data(df, title="Stock Prices"):
    # Normalize so that all graphs start at one point
    # df = df/df.ix[0]
    ax = df.plot(title=title, fontsize=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    for item in (ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(10)
    plt.show()

def main():
    tickers = ["SPY", "XOM", "AAPL", "GLD", "IEF"]
    start_date = "2010-01-01"
    end_date = "2015-12-31"
    df = get_data(tickers, start_date, end_date)
    # plot_data(df)

    # Statistics
    print "Mean: \n", df.mean(), "\n"
    print "Median: \n", df.median(), "\n"
    print "Standard deviation: \n", df.std(), "\n" # standard deviation

    # Computing rolling statistics
    ax = df["SPY"].plot(title="SPY Rolling Mean", label="SPY")

    # Rolling mean with 20-day window
    rm_SPY = pd.rolling_mean(df["SPY"], window=20)
    rstd_SPY = pd.rolling_std(df["SPY"], window=20) # rolling standar deviation

    # Add rolling mean to the same plot
    rm_SPY.plot(label="Rolling mean", ax=ax)
    rstd_SPY.plot(label="Rolling STD", ax=ax)

    plt.show()


if __name__ == "__main__":
    main()