import pprint


class FeatureExtrctor(object):
    """
    Extracts the features to be used in the policy search implementation.
    """

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
            number = info['ptobes since last reimage']
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
        for name in 
