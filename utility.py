import random
import pprint
import math


def logistic(x, slope=1, shift=0):
    return (1.0 / (1 + math.exp(-slope*(x - shift))))


class Utility(object):
    """
        Has the utility functions that will be used for
        generating the payoffs
    """

    def __init__(self, params):
        """
            Pass in a dict of params having:
            dtCost: cost of unit downtime
            prCost: cost of unit probe
            DEF: [List of 4 payoff states for control of 0, 1, 2, 3]
            ATT: [List of 4 payoff states for control of 0, 1, 2, 3]
        """
        self.params = {}
        self.cparams = params

    def getUtility(self, utility):
        if hasattr(self, utility):
            return getattr(self, utility)
        else:
            print "Unrecognized utility function: " + utility

    def simpleCIA(self, data):
        """
            Simple CIA type utility. Pass in the history of
            state dict. Cost is not associated with reimage
            act, but with the amount of downtime for the
            server. Probes have associated cost.
        """

        #pprint.pprint(data)

        # Actions costs - downtime and probe costs
        dtCost = self.cparams['dtCost']
        prCost = self.cparams['prCost']
        downTime = self.cparams['downTime']

        # Status payoffs - server control costs
        controlPayoffs = {}
        controlPayoffs['DEF'] = self.cparams['DEF']
        controlPayoffs['ATT'] = self.cparams['ATT']

        self.params['DEF'] = 0
        self.params['ATT'] = 0
        self.params['totalDowntimeCost'] = 0
        self.params['totalProbeCost'] = 0
        self.params['totalDowntime'] = 0
        previousTime = 0
        currentTime = 0
        prevC = {}
        # Tracks the servers under each agents control
        sCount = {
                'DEF': 0,
                'ATT': 0
                }
        # Tracks the previous controller of each server
        prevC['Server0'] = 'DEF'
        prevC['Server1'] = 'DEF'
        prevC['Server2'] = 'DEF'

        for it in sorted(data.items()):
            # sCount['DEF'] = 0
            # sCount['ATT'] = 0
            # print "------------------>>"+str(it[0])+"\n"
            time = it[0]
            hist = it[1]
            currentTime = time
            timeFactor = currentTime - previousTime
            pTime = previousTime
            previousTime = currentTime
            # Might need to correct this
            # for res, rep in hist['inactiveResources'].iteritems():
                # self.params['totalDowntimeCost'] += timeFactor*dtCost
                # # print "-------->" + res
                # self.params['totalDowntime'] += timeFactor
            # print hist['activeResources']	
            # for res, rep in hist['activeResources'].iteritems():
            # 	sCount[prevC[res]] += 1
            # 	prevC[res] = rep['Control']
            for k, v in sCount.iteritems():
                # print k,v, time
                # print "Do [" + str(currentTime) + "-" + str(pTime) + "] " + "* " +str((controlPayoffs[k])[v])
                # print ']]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]\n'
                # Accrues utility for time period (t-1) to t
                self.params[k] += timeFactor*(controlPayoffs[k])[v]
                sCount[k] = 0
            # print self.params
            # Count servers for each agent at time t
            for res, rep in hist['activeResources'].iteritems():
                sCount[rep['Control']] += 1
            for res, rep in hist['inactiveResources'].iteritems():
                sCount[rep['Control']] += 1

        lastItem = data[max(data.keys(), key=int)]
        for k, v in lastItem.iteritems():
            for s, r in v.iteritems():
                self.params['totalProbeCost'] += r['Total Probes till now']
                self.params['totalDowntime'] += r['Reimage Count']
                # print self.params

        self.params['totalDowntime'] *= downTime
        self.params['totalDowntimeCost'] = self.params['totalDowntime']*dtCost
        payoff = {}
        payoff["totalProbes"] = self.params['totalProbeCost']

        self.params['totalProbeCost'] *= prCost
        payoff["DEF"] = self.params['totalDowntimeCost'] + self.params['DEF']
        payoff["ATT"] = self.params['totalProbeCost'] + self.params['ATT']
        payoff["totalDownTime"] = self.params['totalDowntime']

        # print "---------------------------------------------\n"
        # print payoff
        return payoff

    def Logistic2P(self, data):
        """
            Uses the two parameter logistic function. Given the params slope
            and shift, described by f(x) = 1/(1 -e^(-slope)*(x- shift))
        """

        #  Actions costs - downtime and probe costs
        dtCost = self.cparams["dtCost"]
        prCost = self.cparams["prCost"]
        resources = self.cparams["resources"]
        downTime = self.cparams["downTime"]

        self.params['DEF'] = 0
        self.params['ATT'] = 0
        self.params['totalDowntimeCost'] = 0
        self.params['totalProbeCost'] = 0
        self.params['totalDowntime'] = 0

        #  First element is slope and second is shift
        attParam = []
        defParam = []

        attParam.append(self.cparams["attControlSlope"])
        attParam.append(self.cparams["attControlShift"])
        attParam.append(self.cparams["attDownSlope"])
        attParam.append(self.cparams["attDownShift"])
        defParam.append(self.cparams["defControlSlope"])
        defParam.append(self.cparams["defControlShift"])
        defParam.append(self.cparams["defDownSlope"])
        defParam.append(self.cparams["defDownShift"])

        #  Weights for the function
        attParam.append(self.cparams["attControlWeight"])
        attParam.append(1 - self.cparams["attControlWeight"])
        defParam.append(self.cparams["defControlWeight"])
        defParam.append(1 - self.cparams["defControlWeight"])

        # print "Utility params"
        # print attParam
        # print defParam

        attControlUtil = lambda(x): logistic(x, attParam[0], attParam[1])
        attDownUtil = lambda(x): logistic(x, attParam[2], attParam[3])
        defControlUtil = lambda(x): logistic(x, defParam[0], defParam[1])
        defDownUtil = lambda(x): logistic(x, defParam[2], defParam[3])

        previousTime = 0
        currentTime = 0

        #  We will track the attacker and defender down/control
        attServers = [0, 0]
        defServers = [resources, 0]

        for item in sorted(data.items()):
            currentTime = item[0]
            info = item[1]

            timeDiff = currentTime - previousTime
            previousTime = currentTime
            #  Calculate the increment to utility since last time period
            self.params["ATT"] += timeDiff*(attParam[4] *
                                            attControlUtil(attServers[0]) +
                                            attParam[5] *
                                            attDownUtil(
                                                attServers[0] + defServers[1]))

            self.params["DEF"] += timeDiff*(defParam[4] *
                                            defControlUtil(defServers[0]) +
                                            defParam[5] *
                                            defDownUtil(
                                                defServers[0] + defServers[1]))

            #  Find the server distribution
            attServers = [0, 0]
            defServers = [0, 0]
            for k, v in info["activeResources"].iteritems():
                if v["Control"] == "ATT":
                    attServers[0] += 1
                else:
                    defServers[0] += 1
            for k, v in info["inactiveResources"].iteritems():
                # It's important to remember that in the case of the general
                # utility fucntion the down servers are not really under any
                # control
                if v["Control"] == "DEF":
                    defServers[1] += 1
                else:
                    attServers[1] += 1
                    assert(False)

        lastItem = data[max(data.keys(), key=int)]
        for k, v in lastItem.iteritems():
            for s, r in v.iteritems():
                self.params["totalProbeCost"] += r["Total Probes till now"]
                self.params["totalDowntime"] += r["Reimage Count"]

        self.params["totalDowntime"] *= downTime
        self.params["totalDowntimeCost"] = self.params["totalDowntime"]*dtCost
        payoff = {}
        payoff["totalProbes"] = self.params["totalProbeCost"]
        self.params["totalProbeCost"] *= prCost
        payoff["ATT"] = self.params["ATT"] + self.params["totalProbeCost"]
        payoff["DEF"] = self.params["DEF"]
        payoff["totalDowntime"] = self.params["totalDowntime"]
        return payoff


class instUtility(object):
    """
    Gives the utility between two time periods
    """

    def __init__(self, cparams):
        self.prCost = cparams["prCost"]
        self.downTime = cparams["downTime"]

        self.cumulativeDef = 0
        self.cumulativeAtt = 0
        self.lastDef = 0
        self.lastAtt = 0
        self.totalProbeCost = 0
        self.totalDowntime = 0

        #  First element is slope and second is shift
        self.attParam = []
        self.defParam = []

        self.attParam.append(cparams["attControlSlope"])
        self.attParam.append(cparams["attControlShift"])
        self.attParam.append(cparams["attDownSlope"])
        self.attParam.append(cparams["attDownShift"])
        self.defParam.append(cparams["defControlSlope"])
        self.defParam.append(cparams["defControlShift"])
        self.defParam.append(cparams["defDownSlope"])
        self.defParam.append(cparams["defDownShift"])

        #  Weights for the function
        self.attParam.append(cparams["attControlWeight"])
        self.attParam.append(1 - cparams["attControlWeight"])
        self.defParam.append(cparams["defControlWeight"])
        self.defParam.append(1 - cparams["defControlWeight"])

        # print "Utility params"
        # print attParam
        # print defParam

        self.attControlUtil = lambda(x): logistic(x, self.attParam[0],
                                                  self.attParam[1])
        self.attDownUtil = lambda(x): logistic(x, self.attParam[2],
                                               self.attParam[3])
        self.defControlUtil = lambda(x): logistic(x, self.defParam[0],
                                                  self.defParam[1])
        self.defDownUtil = lambda(x): logistic(x, self.defParam[2],
                                               self.defParam[3])

    def L2P(self, state, currentTime, lastAction):
        """
        state - (servers in control of att,
                 servers in control of def,
                 servers down)
        currentTime - current time
        lastAction -(time, player)
        """

        delta = currentTime - lastAction[0]
        attResources = state[0]
        defResources = state[1]
        dwnResources = state[2]

        # Increment cumulative defender utility
        utilDefNow = delta*(
                            self.defParam[4] *
                            self.defControlUtil(defResources) +
                            self.defParam[5] *
                            self.defDownUtil(defResources + dwnResources))

        # if the last action was not the defender it's most recent utility
        # becomes for this + previous time interval
        if lastAction[1] != "DEF":
            self.lastDef += utilDefNow
        # if the last action is defender it's most recent utility becomes for
        # this time interval
        else:
            self.lastDef = utilDefNow

        # Increment the cumulative utility
        self.cumulativeDef += utilDefNow

        utilAttNow = delta*(
                            self.attParam[4] *
                            self.attControlUtil(attResources) +
                            self.attParam[5] *
                            self.attDownUtil(attResources + dwnResources))

        # if the previous action was not attacker then don't subtract the probe
        # cost from the latest util
        if lastAction[1] != "ATT":
            self.lastAtt += utilAttNow
            self.cumulativeAtt += utilAttNow
        else:
            self.lastAtt = utilAttNow + self.prCost
            self.cumulativeAtt += utilAttNow + self.prCost

    def getCumulativeAttUtility(self):
        return self.cumulativeAtt

    def getCumulativeDefUtility(self):
        return self.cumulativeDef

    def getPreviousDefUtility(self):
        return self.lastDef

    def getPreviousAttUtility(self):
        return self.lastAtt

    def getPayoff(self):
        payoff = {
            "ATT": self.cumulativeAtt,
            "DEF": self.cumulativeDef,
            "totalProbes": -1,
            "totalDowntime": -1
        }

        return payoff
