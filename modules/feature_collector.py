import pprint


class FeatureExtrctor(object):
    """
    Extracts the features to be used in the policy search implementation.
    """

    def __init__(self, params):
        self.bias = params["bias"]

    def timeSinceLastProbeSinceLastReimage(self, knowledge, time):
        f = {}
        for name, info in knowledge.iteritems():
            previous = 0 if\
                info['last reimage'] > info['last probe'] else\
                info['last probe']
            f[name] = time - previous
        return f

    def numberOfProbesSinceLastReimage(self, knowledge):
        f = {}

        for name, info in knowledge.iteritems():
            number = info['probes since last reimage']
            f[name] = number
        return f

    def maxProbeBool(self, knowledge):
        res = {}
        f = []
        for name, info in knowledge.iteritems():
            res[name] = False
            f.append((name, info['probes since last reimage']))
        f = f.sort(f, key=lambda x: x[1])
        res[f[0][0]] = True
        return res

    def maxProbesUncompromised(self, knowledge):
        res = {}
        f = []
        for name, info in knowledge.iteritems():
            if(info["control"]) != "ATT":
                res[name] = False
                f.append((name, info["probes since last reimage"]))
        f = f.sort(f, key=lambda x: x[1])
        res[f[0][0]] = True
        return res

    def controlIndices(self, knowledge):
        res = {}
        for name, info in knowledge.ieritems():
            if(info["control"] == "DEF"):
                res[name] = 1
            else:
                res[name] = 0
        return res

    def timeSinceLastReimage(self, knowledge, time):
        res = {}
        for name, info in knowlege.iteritems():
            res[name] = time - info["last reimage"]
        return res

    def timeSinceLastNoOp(self, knowledge):
        return 0

    def lastProbedBool(self, knowledge):
        res = {}
        f = []
        for name, info in knowledge.iteritems():
            res[name] = False
            f.append((name, info["last probe"]))
        f = f.sort(f, key=lambda x: x[1])
        res[f[0][0]] = True
        return res

    def bias(self):
        return self.bias
