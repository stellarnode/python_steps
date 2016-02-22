""" Portfolio Statistics """

# Cummulative return
# Sharpe ratio = sqrt(sample_rate, e.g. 12 for months or 252 for trading days) * mean(daily_ret - risk-free-rate) / std(daily_ret - risk-free-rate)

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

    # Initial values
    start_value = 10000
    dates = pd.date_range("2009-01-01", "2015-12-31")
    symbols = ["SPY", "XOM", "GLD", "AAPL"]
    allocations = [0.4, 0.1, 0.1, 0.4]

    # Read data
    df = get_data(symbols, dates)
    plot_data(df)

    # Basic calculations
    normalized = df / df.ix[0]
    plot_data(normalized, title="Assests Returns", ylabel="Assets Returns")
    allocated = normalized * allocations
    position_values = allocated * start_value
    portfolio_value = position_values.sum(axis=1)
    print portfolio_value.tail()
    plot_data(portfolio_value, title="Portfolio Value", ylabel="Portfolio Value")

    # Compute daily returns
    daily_returns = (portfolio_value / portfolio_value.shift(1)) - 1
    daily_returns = daily_returns.ix[1:] # Get rid of first row which is just zeros
    plot_data(daily_returns, title="Daily Returns", ylabel="Daily Returns")

    # Portfolio Statistics
    cummularive_return = portfolio_value[-1] / portfolio_value[0] - 1
    avg_daily_return = daily_returns.mean()
    std_daily_return = daily_returns.std()
    sharpe_ratio_daily = np.sqrt(252) * avg_daily_return / std_daily_return

    print "PORTFOLIO STATISTICS"
    print "Cummulative return: ", round(cummularive_return * 100, 2), "%"
    print "Average daily return: ", round(avg_daily_return * 100, 2), "%"
    print "Standard deviation of daily returns: ", round(std_daily_return * 100, 2), "%"
    print "Sharpe ratio: ", round(sharpe_ratio_daily, 2)

if __name__ == "__main__":
    main()