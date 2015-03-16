import math
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pylab


def getProb(x, y):
    return (1 - math.exp(-y*x))


def plotProbs():
    x = [i for i in range(100)]
    y = []
    for t in [0.05, 0.1, 0.2, 0.01]:
        temp = []
        for i in range(100):
            temp.append(getProb(i, t))
        y.append(temp)

    colors = ['r', 'b', 'g', 'k']

    for item in zip(y, colors):
        plt.plot(x, item[0], item[1])

    plt.show()


def expectation():
    exp = []
    for t in [0.05, 0.1, 0.2, 0.01]:
        temp = 0
        for i in range(100):
            temp += 1*getProb(i, t)
        exp.append(temp/100)
    print exp

if __name__ == '__main__':
    expectation()
    plotProbs()
