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

    def periodicMax(self, knowledge, period, askTime):
        if askTime:
            return self.periodic(knowledge, period, askTime)
        else:
            choices = knowledge.getActiveControlByOthers()
            if choices:
                server = knowledge.getMaxProbed(choices)
                if server:
                    return server
                else:
                    assert(False)

    def No(self, knowledge, stParam, askTime):
        if(askTime):
            # Make this bigger than the horizon, should use horizon for setting
            return 1000000
        else:
            # Should not be reached, the action should never be executed
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
            if choices:
                return random.choice(choices)
            else:
                return None

    def periodicMax(self, knowledge, period, askTime):
        if askTime:
            return self.periodic(knowledge, period, askTime)
        else:
            choices = knowledge.getActiveResources()
            if choices:
                server = knowledge.getMaxProbed(choices)
                if server:
                    return server
                else:
                    assert(False)

    def probeCountTime(self, knowledge, params, askTime):
        if askTime:
            # Initiate the action at this time
            return knowledge.time
        else:
            # Get the params
            params = params.split('_')
            probeLimit = float(params[0])
            timeLimit = float(params[1])

            # if number of probes has crossed the threshold
            activeList = knowledge.getActiveResources()
            if activeList:
                maxProbed = knowledge.getMaxProbed(activeList)
                if maxProbed is not None:
                    if (knowledge.resources[maxProbed][
                       "probes since last reimage"] >= probeLimit):
                        return maxProbed

                    # if the threshold has been crossed by anyone
                    lastProbed = knowledge.getLastProbed()
                    if lastProbed[0] is not None:
                        if knowledge.time - lastProbed[1] >= timeLimit:
                            return lastProbed[0]
                        else:
                            return (-1, timeLimit + float(lastProbed[1]))
        return None

    def No(self, knowledge, stParam, askTime):
        if(askTime):
            #  Make this bigger than the horizon, use horizon for setting
            return 1000000
        else:
            #  Should not be reached, the action should never be executed
            assert(False)
