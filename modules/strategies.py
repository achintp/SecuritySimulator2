import random

debug = 0


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

    def periodic(self, knowledge, period, askTime):
        #  The strategy gets the knowledge state and takes care of not choosing
        #  down or already compromised servers.
        if debug:
            print "KS of attacker"
            print knowledge.resources
        period = float(period)
        if(askTime):
            if knowledge.time < knowledge.previousTime:
                return None
            return knowledge.time + period
        else:
            #  Return the resource that has to be probed
            choices = knowledge.getActiveControlByOthers()
            if debug:
                print "choices: ", choices
            #  Pick a random choice of server from this list
            if choices:
                return random.choice(choices)
            else:
                return None

    def No(self, knowledge, stParam, askTime):
        if(askTime):
            #  Make this bigger than the horizon, use horizon for setting
            return 1000000
        else:
            #  Should not be reached, the action should never be executed
            assert(False)


class DefenderStrategies(AgentStrategies):
    def __init__(self, params):
        super(DefenderStrategies, self).__init__(params)

    def periodic(self, knowledge, period, askTime):
        if debug:
            print knowledge.resources
        period = float(period)
        if(askTime):
            if knowledge.time < knowledge.previousTime:
                return None
            return knowledge.time + period
        else:
            #  return the resource to be reimaged
            choices = knowledge.getActiveResources()
            return random.choice(choices)

    def No(self, knowledge, stParam, askTime):
        if(askTime):
            #  Make this bigger than the horizon, use horizon for setting
            return 1000000
        else:
            #  Should not be reached, the action should never be executed
            assert(False)
