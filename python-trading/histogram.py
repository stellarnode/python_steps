""" Plot a histogram """

import pandas as pd
import matplotlib.pyplot as plt

from daily_returns import get_data, plot_data

def compute_daily_returns(df):
    daily_returns = df.copy()
    daily_returns[1:] = (df[1:] / df[:-1].values) - 1
    daily_returns.ix[0, :] = 0
    return daily_returns

def main():
    # Read data
    dates = pd.date_range("2009-01-01", "2012-12-31")
    symbols = ["SPY"]
    df = get_data(symbols, dates)
    plot_data(df)

    # Compute daily returns
    daily_returns = compute_daily_returns(df)
    plot_data(daily_returns, title="Daily Returns", ylabel="Daily Returns")

    # Plot a histogram
    daily_returns.hist(bins=20)


    # Get the mean and standard deviation
    mean = daily_returns["SPY"].mean()
    print "mean: ", mean
    std = daily_returns["SPY"].std()
    print "standard deviation: ", mean

    plt.axvline(mean, color="w", linestyle="dashed", linewidth=2)
    plt.axvline(std, color="r", linestyle="dashed", linewidth=2)
    plt.axvline(-std, color="r", linestyle="dashed", linewidth=2)
    plt.show()

    # Compute Kurtosis
    print "kurtosis: ", daily_returns["SPY"].kurtosis()


if __name__ == "__main__":
    main()
