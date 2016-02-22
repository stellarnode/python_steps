""" Minimize an objective function using SciPy. """

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize as spo

def f(x):
    # find a min value of x for the function to return the min value of y
    # suppose you have the following function:
    y = (x - 1.5)**2 + 0.5
    print "x = {}, y = {}".format(x, y) # for tracing
    return y

def main():
    xguess = 2.0 # give some value to start with
    min_result = spo.minimize(f, xguess, method="SLSQP", options={ "disp": True })
    print "Minina found at: "
    print "x = {}, y = {}".format(min_result.x, min_result.fun)


if __name__ == "__main__":
    main()