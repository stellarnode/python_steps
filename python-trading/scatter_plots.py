""" Scatter plots, Correlations, Beta and Alpha """

# Beta is a slope of the line. The steeper it is, the steeper the growth compared to market (SPY in this context).
# e.g. If market goes 1% up, with Beta 2 the stock would go up 2%.
# Beta shows how REACTIVE stock/asset is compared to the market.
# Alpha is how much higher the line is above central cross. It means how much the stock outperforms the market.
# Higher Alpha - better performance.

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from daily_returns import get_data, plot_data

def compute_daily_returns(df):
    daily_returns = df.copy()
    daily_returns[1:] = (df[1:] / df[:-1].values) - 1
    daily_returns.ix[0, :] = 0
    return daily_returns

def main():
    # Read data
    dates = pd.date_range("2009-01-01", "2012-12-31")
    symbols = ["SPY", "XOM", "GLD"]
    df = get_data(symbols, dates)
    plot_data(df)

    # Compute daily returns
    daily_returns = compute_daily_returns(df)
    plot_data(daily_returns, title="Daily Returns", ylabel="Daily Returns")

    # Scatter plot SPY vs XOM
    daily_returns.plot(kind="scatter", x="SPY", y="XOM")
    beta_XOM, alpha_XOM = np.polyfit(daily_returns["SPY"], daily_returns["XOM"], 1)
    plt.plot(daily_returns["SPY"], beta_XOM * daily_returns["SPY"] + alpha_XOM, "-", color="r")
    print "XOM"
    print "Beta XOM: ", beta_XOM
    print "Alpha XOM: ", alpha_XOM
    print "\n"
    plt.show()

    # Scatter plot SPY vs GLD
    daily_returns.plot(kind="scatter", x="SPY", y="GLD")
    beta_GLD, alpha_GLD = np.polyfit(daily_returns["SPY"], daily_returns["GLD"], 1)
    plt.plot(daily_returns["SPY"], beta_GLD * daily_returns["SPY"] + alpha_GLD, "-", color="y")
    print "GLD"
    print "Beta GLD: ", beta_GLD
    print "Alpha GLD: ", alpha_GLD
    print "\n"
    plt.show()

    # Calculate correlation coefficient
    print daily_returns.corr(method="pearson")



if __name__ == "__main__":
    main()