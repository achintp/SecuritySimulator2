import random
import pprint
import math


def logistic(x, slope=1, shift=0):
    return (1 / (1 - math.exp(-slope*(x - shift))))


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

        #Actions costs - downtime and probe costs
        dtCost = self.cparams['dtCost']
        prCost = self.cparams['prCost']
        downTime = self.cparams['downTime']

        #Status payoffs - server control costs
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
        #Tracks the servers under each agents control
        sCount = {
                'DEF':0,
                'ATT':0
                }
        #Tracks the previous controller of each server
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
            #Might need to correct this
            # for res, rep in hist['inactiveResources'].iteritems():
                # self.params['totalDowntimeCost'] += timeFactor*dtCost
                # # print "-------->" + res
                # self.params['totalDowntime'] += timeFactor
            # print hist['activeResources']	
            # for res, rep in hist['activeResources'].iteritems():
            # 	sCount[prevC[res]] += 1
            # 	prevC[res] = rep['Control']
            for k,v in sCount.iteritems():
                # print k,v, time
                # print "Do [" + str(currentTime) + "-" + str(pTime) + "] " + "*" +str((controlPayoffs[k])[v])
                # print ']]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]\n'
                #Accrues utility for time period (t-1) to t
                self.params[k] += timeFactor*(controlPayoffs[k])[v]
                sCount[k] = 0
            # print self.params
            #Count servers for each agent at time t
            for res, rep in hist['activeResources'].iteritems():
                sCount[rep['Control']] += 1
            for res, rep in hist['inactiveResources'].iteritems():
                sCount[rep['Control']] += 1


        lastItem = data[max(data.keys(), key=int)]
        for k,v in lastItem.iteritems():
            for s,r in v.iteritems():
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
        attParam.append(self.cparams["attDownWeight"])
        defParam.append(self.cparams["defControlWeight"])
        defParam.append(self.cparams["defDownWeight"])

        print "Utility params"
        print attParam
        print defParam

        attControlUtil = lambda(x): logistic(x, attParam[0], attParam[1])
        attDownUtil = lambda(x): logistic(x, attParam[2], attParam[3])
        defControlUtil = lambda(x): logistic(x, defParam[0], defParam[1])
        defDownUtil = lambda(x): logistic(x, defParam[2], defParam[3])

        previousTime = 0
        currentTime = 0

        #  We will track the attacker and defender down/control
        attServers = [0, 0]
        defServers = [3, 0]

        for item in sorted(data.items()):
            currentTime = item[0]
            info = item[1]

            timeDiff = currentTime - previousTime
            previousTime = currentTime
            #  Calculate the increment to utility since last time period
            self.params["ATT"] += timeDiff*(attParam[4]*attControlUtil(attServers[0]))

            self.params["DEF"] += timeDiff*(defParam[4]*defControlUtil(defServers[0]) +
                                            defParam[5]*defDownUtil(defServers[1]))

            #  Find the server distribution
            attServers = [0, 0]
            defServers = [0, 0]
            for k, v in info["activeResources"].iteritems():
                if v["Control"] == "ATT":
                    attServers[0] += 1
                else:
                    defServers[0] += 1
            for k, v in v["inactiveResources"].iteritems():
                if v["Control"] == "DEF":
                    defServers[1] += 1
                else:
                    attServers[1] += 1
                    assert(False)

        lastItem = data[max(data.keys(), key=int)]
        for k, v in lastItem.iteritems():
            for s, r in v.iteritems():
                self.params["totalProbeCost"] += r["Total Probes Till Now"]
                self.params["totalDowntime"] += r["Reimage Count"]
        self.params["TotalDowntime"] *= downTime
        self.params["totalDowntimeCost"] = self.params["totalDowntime"]*dtCost
        payoff = {}
        payoff["totalProbes"] = self.params["totalProbeCost"]
        self.params["totalProbeCost"] *= prCost
        payoff["ATT"] = self.params["ATT"] + self.params["totalProbeCost"]
        payoff["DEF"] = self.params["DEF"] + self.params["totalDowntimeCost"]
        payoff["totalDowntime"] = self.params["TotalDowntime"]
        return payoff
