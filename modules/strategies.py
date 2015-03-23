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

    def periodicDecept(self, knowledge, period, askTime):
        # TODO
        # After a fixed time will consider compromised servers
        # as probe targets. Implement by 03/25/2015
        return 0

    def No(self, knowledge, stParam, askTime):
        if(askTime):
            # Make this bigger than the horizon, should use horizon for setting
            return 1000000
        else:
            # Should not be reached, the action should never be executed
            assert(False)

    def renewal(self, knowledge, mean, askTime):
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            else:
                diff = random.expovariate(1.0/float(mean))
                return knowledge.time + diff
        else:
            return self.periodicMax(knowledge, None, False)

    def refactoryRenewal(self, knowledge, params, askTime):
        # TODO
        # Waits for a refactory recovery period before assigning period
        # for next move. Implement by 03/22/2015
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            else:
                params = params.split('_')
                refactorTime = float(params[0])
                mean = float(params[1])
                diff = random.expovariate(1.0/mean)
                return knowledge.time + diff + refactorTime
        else:
            return self.periodicMax(knowledge, None, False)
        return 0

    def controlN(self, knowledge, params, askTime):
        # Will probe fast if less than N under control
        # Implement by 03/22/2015
        if askTime:
            # Keep polling at every time interval
            # Will increase running times a lot
            if knowledge.time < knowledge.previousTime:
                return None
            params = params.split('_')
            interval = float(params[0])
            return knowledge.time + interval
        else:
            controlList = knowledge.getActiveControlByMe()

            params = params.split('_')
            N = int(params[1])
            # print len(controlList)
            if len(controlList) < N:
                # print "Attack"
                return self.periodicMax(knowledge, None, False)
        return None


class DefenderStrategies(AgentStrategies):

    refactor = False

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

    def renewal(self, knowledge, mean, askTime):
        """
        Follows a stochastic periodic process in taking action
        """
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            else:
                diff = random.expovariate(1.0/float(mean))
                return knowledge.time + diff
        else:
            # Use periodicMax to get the servers
            return self.periodicMax(knowledge, None, False)

    def stochasticProbecount(self, knowledge, params, askTime):
        """
        Simulates attacks on the max probed server, reimags on success
        """
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            else:
                return knowledge.time + float(params)
        else:
            choices = knowledge.getActiveResources()
            print choices
            if choices:
                server = knowledge.getMaxProbed(choices)
                if server:
                    prob = knowledge._computeProb(server)
                    random.seed()
                    rand = random.random()
                    if rand < prob:
                        return server
            return None

    def refactoryRenewal(self, knowledge, params, askTime):
        # TODO
        # Same as attackers refactory
        # Implement by 03/22/2015
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            else:
                params = params.split('_')
                refactorTime = float(params[0])
                mean = float(params[1])
                diff = random.expovariate(1.0/mean)
                return knowledge.time + diff + refactorTime
        else:
            return self.periodicMax(knowledge, None, False)
        return 0

    def controlN(self, knowledge, params, askTime):
        # TODO
        # Looks at the health of the system. If below, then get it back
        # Define assumptions appropriately
        # Implement by - 03/22/2015
        # Assumptions -
        # 1. Defender has full knowledge of the probability distribution
        #    governing the growth of the attack vector
        # 2. Defender has full view of the probes that have happened on the
        #    servers at any point of time
        # 3. Health of the system is defined as the probability that the
        #    defender has control of at least N servers at any point of time
        # params - (N, threshold, refactorTime)
        if askTime:
            if knowledge.time < knowledge.previousTime:
                return None
            if DefenderStrategies.refactor:
                params = params.split('_')
                refactorTime = float(params[2])
                DefenderStrategies.refactor = False
                return knowledge.time + refactorTime
            else:
                return knowledge.time
        else:
            params = params.split('_')
            N = int(params[0])
            threshold = float(params[1])
            health = knowledge.calculateHealth(N)
            # print "Health is " + str(health)
            if health > threshold:
                # print "Fixing health"
                server = self.periodicMax(knowledge, None, False)
                if server is not None:
                    DefenderStrategies.refactor = True
                return server
        return None

    def greedy(self):
        # Maximizes the local benefit
        # High priority
        # Frame optimization problem and solver
        # Implement ASAP
        return 0
