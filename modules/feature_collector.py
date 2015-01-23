import pprint

class FeatureExtrctor(object):
    """
    Extracts the features to be used in the policy search implementation.
    """

    def timeSinceLastProbe(self, activeResources, time):
        f = {}
        for item in activeResources:
            previous = item.lastReimage if\
                       item.lastReimage > item.probeHistory[-1] else\
                       item.probeHistory[-1]


