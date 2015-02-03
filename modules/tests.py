import unittest
import random
import numpy as np
from softmax import Softmax


class SoftMaxFunctions(unittest.TestCase):
    def setUp(self):
        random.seed()
        self.features = np.array([[0, 0], [0, 0]])

        for row, item in enumerate(self.features):
            for col, _ in enumerate(item):
                self.features[row][col] = random.randint(0, 10)

    def test_softMax(self):
        params = {}
        params["temp"] = 1
        softmax = Softmax(params)
        print self.features
        res = softmax.softMax(self.features)
        print res
        self.assertTrue(np.sum(res) < 1 + 0.0005 and
                        np.sum(res) > 1 - 0.0005)

if __name__ == '__main__':
    unittest.main()
