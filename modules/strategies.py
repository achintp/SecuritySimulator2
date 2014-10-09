import random


class AgentStrategies(object):
    """Base class for strategies."""
    def __init__(self, params):
        self.params = params

    def getStrategy(self, strategy):
        if hasattr(self, strategy):
            return getattr(self, strategy)


class AttackerStrategies(AgentStrategies):
    def __init__(self, params):
        super(AttackerStrategies, self).__init__(params)

    def purePeriodic(self, info, period):
        timePeriod = float(period)
        nextAttack = -1
