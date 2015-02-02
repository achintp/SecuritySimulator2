import numpy as np


class Softmax(object):
    def __init__(self, params):
        self.getWeights(1)
        self.temp = params["temp"]

    def getFeatures(self, features):
        self.features = features

    def getWeights(self, selector):
        if(selector == 1):
            self.weights = np.loadtxt(open("weights.csv", "rb")
                                      delimiter=",", skiprows=1)

    def softMax(self, features):
        self.getFeatures(features)
        # Decide the format of the features and the weights
        # Features should be 1xm and weights should be mx(k+1)
        # Result should be 1x(k+1)

        mult = np.dot(self.features, self.weights)
        num = np.exp(mult)
        denom = np.sum(num)
        result = num/denom
        return result
