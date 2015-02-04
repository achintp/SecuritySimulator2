import sys
import math
import matplotlib.pyplot as plt
import pylab as pl
import numpy as np


def logistic(x, slope=1, shift=0):
    a = []
    for item in x:
        a.append((1.0 / (1 + math.exp(-slope*(item - shift)))))
    return a


def plot(p, q, r, s, w1, w2):
    x = np.arange(0, 10, 0.1)
    sig1 = logistic(x, p, q)
    sig2 = logistic(x, r, s)
    res = []
    for item in zip(sig1, sig2):
        res.append(w1*item[0] + w2*item[1])
    plt.plot(x, res)
    plt.show()

if __name__ == '__main__':
    plot(float(sys.argv[1]),
         float(sys.argv[2]),
         float(sys.argv[3]),
         float(sys.argv[4]),
         float(sys.argv[5]),
         float(sys.argv[6]))
