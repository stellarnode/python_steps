""" Basic stock statistics """

import pandas as pd
import numpy as np
import Quandl as q

import matplotlib.pyplot as plt
import pandas_datareader.data as web

import urllib2 as url
import openpyxl as xl
import json

from quandl_api import QUANDL_API

def get_data(ticker):
    df = web.DataReader(ticker, "yahoo")
    return df

def compute_daily_returns(df):
    daily_returns = (df["Adj Close"] / df["Adj Close"].shift(1)) - 1
    daily_returns.ix[0] = 0
    df["Daily Returns"] = daily_returns
    df = df.ix[1:] # get rid of the first row since zeros in daily returns
    return df

def compute_std(df):
    return df["Daily Returns"].std()

def compute_volatility(df):
    return df["Close"].std()

def get_rolling_std(df, window=20):
    df["Std Dev"] = pd.rolling_std(df["Adj Close"], window=window)
    return df

def compute_cumm_returns(df):
    df["Cumm Returns"] = df["Adj Close"] / df["Adj Close"].ix[0]
    return df

def historical_volatility(sym, days):
    "Return the annualized stddev of daily log returns of `sym`."
    try:
        quotes = web.DataReader(sym, 'yahoo')['Close'][-days:]
    except Exception, e:
        print "Error getting data for symbol '{}'.\n".format(sym), e
        return None, None
    logreturns = np.log(quotes / quotes.shift(1))
    return np.sqrt(252 * logreturns.var())


def main():
    ticker = raw_input("What ticker are you interested in? ")
    df = get_data(ticker)
    df = compute_daily_returns(df)
    df = compute_cumm_returns(df)
    df = get_rolling_std(df, window=20)
    print df.head()
    print df.tail()
    print "Std Dev of Daily Returns: ", compute_std(df)
    print "Rolling Std Dev, last value: ", df["Std Dev"].ix[-1]
    print "Historical_volatility, last 30 days: ", historical_volatility(ticker, 30)


if __name__ == "__main__":
    main()

