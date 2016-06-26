""" playing with the moon """

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandas_datareader.data as web


def symbol_to_path(symbol, base_dir="data"):
    """Return CSV file path given ticker symbol."""
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))

def get_data(tickers, start, end):
    dates = pd.date_range(start, end)
    df = pd.DataFrame(index=dates)
    for ticker in tickers:
        dftemp = web.DataReader(ticker, "yahoo", start, end)
        dftemp = pd.DataFrame(dftemp, columns=["Adj Close"])
        dftemp = dftemp.rename(columns={"Adj Close": ticker})
        df = df.join(dftemp)
    dftemp = pd.read_csv(symbol_to_path("moon"), index_col='date',
                parse_dates=True, usecols=['date', 'phaseid'], na_values=['nan'])
    print dftemp.head()
    df = df.join(dftemp * 2 + 10)
    df = df.fillna(method="ffill")
    return df


def main():
    df = get_data(["SLV"], '2015-01-01', '2016-02-29')
    print df.head(10)
    print df.tail(10)
    df.plot()
    plt.show()



if __name__ == "__main__":
    main()
