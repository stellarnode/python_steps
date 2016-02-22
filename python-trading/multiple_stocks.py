""" Build a dataframe with Pandas """

import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import numpy

def test_run():

    tickers = ["SPY", "IBM", "AAPL", "GLD"]

    # Define date range
    start_date = "2010-01-01"
    end_date = "2010-12-31"
    dates = pd.date_range(start_date, end_date)
    # print dates[0]

    # Create empty dataframe
    df1 = pd.DataFrame(index=dates)
    # print df1

    # Read SPY data into temporary dataframe from Yahoo
    dfSPY = web.DataReader(tickers[0], "yahoo", start_date, end_date)
    # If reading manually, use the following:
    # dfSPY = pd.read_csv("data/SPY.scv", index_col="Date", parse_dates=True)
    dfSPY = pd.DataFrame(dfSPY, columns=["Adj Close"])
    # print "raw dfSPY: "
    # print dfSPY

    # Join two dataframes
    # df1 = df1.join(dfSPY, how="inner")
    # print "df1 after join: "
    # print df1

    # Drop NaN values if option how="inner" is not used above
    # df1 = df1.dropna()
    # print "After dropping NaN:"
    # print df1

    for ticker in tickers:
        dftemp = web.DataReader(ticker, "yahoo", start_date, end_date)
        dftemp = pd.DataFrame(dftemp, columns=["Adj Close"])
        dftemp = dftemp.rename(columns={"Adj Close": ticker})
        df1 = df1.join(dftemp, how="inner")

    # print df1

    # Slice by rows
    # print df1.ix["2010-01-01":"2010-01-31"]

    # Slice by columns
    # print df1["AAPL"]
    # print df1[["AAPL", "GLD"]]

    # Slice by rows and columns
    print df1.ix["2010-03-10":"2010-03-15", ["AAPL", "GLD"]]

    plot_data(df1)

def plot_data(df, title="Stock Prices"):
    # Normalize so that all graphs start at one point
    df = df/df.ix[0]
    ax = df.plot(title=title, fontsize=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    plt.show()



if __name__ == "__main__":
    test_run()