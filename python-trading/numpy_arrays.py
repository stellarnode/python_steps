# Work with numpy arrays

import numpy as np

def main():
    # List to 1D array
    print np.array([2, 3, 4])

    # List of tuples to 2D array
    print np.array([(2, 3, 4), (5, 6, 7)])

    # Create empty
    print np.empty(5) # 1D
    print np.empty((5, 4)) # 2D
    print np.empty((5, 4, 3)) # 3D

    print np.ones((5, 4)) # ones which are default time of floats
    print np.ones((5, 4), dtype=np.int64) # 2D filled with ones which are integers of 64 bits
    print np.zeros((3, 7), dtype=np.int_)

    # Random ndarrays
    print np.random.random((5, 3))
    print np.random.rand(5, 4)
    print np.random.normal(size=(2, 3)) # "standard normal" with mean == 0 and standard deviation == 1
    print np.random.normal(50, 10, size=(2, 3)) # "standard normal" with mean == 50 and standard deviation == 10

    # Random integers
    print np.random.randint(10) # single int in [0, 10]
    print np.random.randint(1, 10) # single int in [1, 10]
    print np.random.randint(2, 20, size=6) # 1D array with int in [2, 20]
    print np.random.randint(1, 10, size=(3, 4)) # 2D array with int in [1, 10]

    # Ndarray attributes
    a = np.random.normal(100, 10, size=(3, 4))
    print a.shape
    print len(a.shape) # Shows the number of dimensions
    print a.size # Total number of elements in ndarray
    print a.dtype

    # Operations on ndarrays
    np.random.seed(693)
    a = np.random.randint(0, 10, size=(5, 4))
    print "Array: \n", a

    # Sum elements
    print "Sum of all elements: ", a.sum()
    print "Sum of elements in columns: ", a.sum(axis=0)
    print "Sum of elements in rows: ", a.sum(axis=1)

    #Statistics: min, max, mean (across rows, cols, and overall)
    print "Min value of each column: ", a.min(axis=0)
    print "Max value of each row: ", a.max(axis=1)
    print "Mean of all elements: ", a.mean()
    print "Indeces of max elements in columns: ", a.argmax(axis=0)




if __name__ == "__main__":
    main()
