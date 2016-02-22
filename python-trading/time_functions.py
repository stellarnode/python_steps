""" Using time functions """

import time
import numpy as np

def main():

    t1 = time.time()
    print "Something..."
    t2 = time.time()
    print "It took ", t2 - t1, " ms to print the previous statement."

    nd1 = np.random.random((1000, 10000))


if __name__ == "__main__":
    main()