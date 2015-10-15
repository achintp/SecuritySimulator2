import random
import pprint
import agents
import types
import debugging
import numpy as np
import os
import json
from state_manager import StateManager
from utility import Utility
from utility import instUtility



class Simulator(object):
    """Main simulator class"""
    def __init__(self, args):
        """Pass in args as dict. Include:
        startTime
        endTime
        resourceList
        attackerList
        defenderList
        dtCost
        prCost
        DEF - []
        ATT - []
        """
        # Initialize state variables
        self.params = {}
        self.params["startTime"] = args["startTime"]
        self.params["endTime"] = args["endTime"]
        self.params["currentTime"] = 0
        self.params["downTime"] = args["downTime"]
        self.params["resourceReports"] = {}
        self.params["downTime"] = args["downTime"]
        self.attackerList = []
        self.defenderList = []
        self.gameState = 1
        self.askAtt = True
        self.askDef = True
        self.simType = 1
        self.utilType = 'Logistic2P'
        self.attSwitch = True  # For NO-OP, may not use this
        self.defSwitch = True  # FOr NO-OP, may noy use this
        self.probeToken = False
        self.periodToken = False
        # token = "probe"  # Shift all these into inside the strategies
        self.debug = 0
        # Initialize the utility parameters
        self.initUtility(args)
        # Remove this before pushing to prod
        # debugging.refreshLog()

        # Initialize environment settings
        if(args["missRate"] != 0):
            self.missRate = args["missRate"]
            self.probeCountdown = -1
            # debugging.log("miss rate set as " + str(self.missRate))
        else:
            self.missRate = None
            # debugging.log("miss rate is None")

        if(args["falseRate"] != 0):
            self.falseRate = args["falseRate"]
            # debugging.log("Lambda is " + str(self.falseRate))
        else:
            self.falseRate = None
            # debugging.log("Lambda is None")

        # Set the agent strategies in these
        self.defStrategy = None
        self.attStrategy = None
        for k, v in args["defenderList"].iteritems():
            self.defStrategy = v
        for k, v in args["attackerList"].iteritems():
            self.attStrategy = v

        if 'probe' in self.defStrategy:
            self.probeToken = True
        if 'periodic' in self.defStrategy:
            self.periodToken = True
            # print "ProbeToken"

        # Initialize the state manager and the resources
        self.stateManager = StateManager(**{
            "resourceList": args["ResourceList"], "alpha": args["alpha"]})
        self.params["resourceReports"] = self.stateManager.resourceReportList

        #  Give the state manager the utility object
        utilObj = instUtility(self.utilParams)
        self.stateManager.setUtility(utilObj)

        # Initialize the agents
        self.initAgents(args)

        # Initialize the event queue
        f = (self.params["endTime"], 0, -1)
        self.eventQueue = [f]

        if self.falseRate is not None:
            self.getFakeProbe()

    def initUtility(self, args):
        self.utilParams = {}
        self.utilParams["dtCost"] = args["dtCost"]
        self.utilParams["prCost"] = args["prCost"]
        #  self.utilParams["DEF"] = args["DEF"]
        #  self.utilParams["ATT"] = args["ATT"]
        self.utilParams["downTime"] = args["downTime"]

        self.utilParams["attControlSlope"] = args["attControlSlope"]
        self.utilParams["attControlShift"] = args["attControlShift"]
        self.utilParams["attDownSlope"] = args["attDownSlope"]
        self.utilParams["attDownShift"] = args["attDownShift"]
        self.utilParams["defControlSlope"] = args["defControlSlope"]
        self.utilParams["defControlShift"] = args["defControlShift"]
        self.utilParams["defDownSlope"] = args["defDownSlope"]
        self.utilParams["defDownShift"] = args["defDownShift"]

        #  Weights for the function
        self.utilParams["attControlWeight"] = args["attControlWeight"]
        self.utilParams["defControlWeight"] = args["defControlWeight"]
        self.utilParams["resources"] = args["resources"]

    def readWeightsFile(self, weightsPath):
	#weightsFolder = "./working/"
	#weightsFolder = "/nfs/wellman_ls/SecurityGame/weights/"
	#weightsPath = weightsFolder + weightsFile + ".json"
	if os.path.isfile(weightsPath):
		with open(weightsPath) as f:
			weights = json.load(f)
			weights = np.asarray(weights)
			weights = weights.transpose()
	else:
		print "warning:specified weights file ",
		print weightsPath,
		print "not found, proceeding without..."

    def initAgents(self, args):
        #  We probably don't need a list of agents, since its two player
        for k, v in args["attackerList"].iteritems():			
	    # if its a learner strategy then read the weights from the file
	    parts = v.split("-")
	    strategyName = parts[0]
	    weightsFile = ""
	    weights = None
	    if strategyName == "learner":
	        #weightsFile = (parts[1].split("_"))[-1]
		weightsFile = args["attackerWeightFile"]
	        weights = self.readWeightsFile(weightsFile)
	        #print "Read weights file: " + weightsFile

            d = {
                "name": k,
                "strategy": v,
                "resourceList": args["ResourceList"],
                "time": self.params["currentTime"],
                "alpha": args["alpha"],
                #"weights" : args["weights"]
		"weights": weights
                }

            #strategyName = v.split("-")[0];
            if strategyName == "learner":
                self.attacker = agents.LearnerAttacker(**d)
                self.attackerIsLearner = True
            else:
                self.attacker = agents.Attacker(**d)
                self.attackerIsLearner = False

        for k, v in args["defenderList"].iteritems():
	    # if its a learner strategy then read the weights from the file
	    parts = v.split("-")
	    strategyName = parts[0]
	    weightsFile = ""
	    weights = None
	    if strategyName == "learner":
	    	#weightsFile = (parts[1].split("_"))[-1]
		weightsFile = args["defenderWeightFile"]
	    	weights = self.readWeightsFile(weightsFile)
	    	#print "Read weights file: " + weightsFile

            d = {
                "name": k,
                "strategy": v,
                "resourceList": args["ResourceList"],
                "time": self.params["currentTime"],
                "alpha": args["alpha"],
                "miss" : 0 if self.missRate is None else self.missRate,
                #"weights" : args["weights"]
		"weights": weights
                }

            #strategyName = v.split("-")[0];
            if strategyName == "learner":
                self.defender = agents.LearnerDefender(**d)
                self.defenderIsLearner = True
            else:
                self.defender = agents.Defender(**d)
                self.defenderIsLearner = False

    def updateInformation(self):
        # Should update the ground truth information state
        # print "Updating information - " + str(self.params["currentTime"])
        # print "Queue is ",
        # print self.eventQueue
        self.stateManager.updateState(self.params["currentTime"])
        info = {}  # isnt required. Consider removing
        info = self.stateManager.resourceReportList

        self.params["resourceReports"] = self.stateManager.resourceReportList
        info["time"] = self.params["currentTime"]

    def askAttacker(self):
        # Will ask the attacker for the time of the next attack
        # The attacker will return a queue event just stating that
        # wake him when the time to act is upon us

        nextEvent = self.attacker.getActionTime(self.params["currentTime"])
        if(nextEvent is None):
            # print "next event is", nextEvent
            return
        self.eventQueue.append(nextEvent)
        self.sortEventQueue()
        if self.debug:
            print self.eventQueue

    def askDefender(self):
        # Analogous to askAttacker. Defined as different functions
        # for convenience in later additions.

        nextEvent = self.defender.getActionTime(self.params["currentTime"])
        if(nextEvent is None):
            # print "nextevent is ", nextEvent
            return
        self.eventQueue.append(nextEvent)
        self.sortEventQueue()
        if self.debug:
            print self.eventQueuea

    def getFakeProbe(self):
        #  Gets the next fake probe to be put
        nextTime = self.fakeProbe()
        resource = random.choice(self.stateManager.activeResources.keys())
        event = (self.params["currentTime"] + nextTime, resource, 3)
        self.eventQueue.append(event)
        self.sortEventQueue()
        # print self.eventQueue

    def sortEventQueue(self):
        self.eventQueue = sorted(self.eventQueue)

    def shuffleEvents(self):
        #  Is there the possibility of three things queued for the same time?
        #  Consider shuffling more things, there may be a bias
        if(self.eventQueue[1][0] == self.eventQueue[2][0]):
            temp = self.eventQueue[:3]
            random.shuffle(temp)
            self.eventQueue = temp + self.eventQueue[3:]
        else:
            temp = self.eventQueue[:2]
            random.shuffle(temp)
            self.eventQueue = temp + self.eventQueue[2:]
        # print self.eventQueue

    def executeAction(self):
        # The agent needs to be asked what action to execute depending on the
        # current knowledge state. Must also take care of other queue events
        # that include servers waking up, false probes, horizon end time and
        # others. The eventQueue must have tuples corresponding to
        # <time, action, id>
        # The update of state should be done right after the execution
        self.askAtt = False
        self.askDef = False

        #  Both the attacker and defender knowledge states should have the
        #  latest time accessible.
        # print self.eventQueue
        if(self.eventQueue[0][0] > self.params["endTime"]):
            # This is never going to happen since the endtime is a queued event
            assert(False)
        else:
            # If one or more event is queued at the same time then shuffle them
            # randomly. There should be no bias for events in ties.
            if(len(self.eventQueue) > 2):
                if (self.eventQueue[0][0] == self.eventQueue[1][0]):
                    # print "Shuffling happening"
                    self.shuffleEvents()
            #  Pop the next event from the queue
            it = self.eventQueue.pop(0)
            self.params["currentTime"] = it[0]
            if(self.debug):
                print it
            #  Check who queued the event
            #  For the end of the horizon
            #  Both the attacker and defender knowledge states should have the
            #  latest time accessible.
            self.attacker.knowledge.updateTime(self.params["currentTime"])
            self.defender.knowledge.updateTime(self.params["currentTime"])
            if(it[2] == -1):
                self.gameState = 0
                # debugging.eventLog(it)
                if(self.debug):
                    print "Game ending"
                return 0
            #  For a server waking up
            elif(it[2] == 2):
                if(self.debug):
                    print it[1] + " is up and running"

                #  Get the utility for the last time period
                self.stateManager.updateUtility(self.params["currentTime"])
                #  Update the server status in the state manager
                self.stateManager.activeResources[it[1]] =\
                    self.stateManager.inactiveResources[it[1]]
                del self.stateManager.inactiveResources[it[1]]
                self.stateManager.activeResources[it[1]].isWoken(
                    self.params["currentTime"], self.params["downTime"])
                #  The defender knowledge state should be updated
                self.defender.seeServerWake(self.params["currentTime"], it[1])
                self.askDef = True
                #  Update this action as last action that took place
                self.stateManager.updateLastAction(
                                    2, self.params["currentTime"])
                # debugging.eventLog(it, it[1])
            #  For an attacker action
            elif(it[2] == 0):
                if self.attackerIsLearner:
                    payoff = self.stateManager.util.getPayoff()["ATT"]                    
                    resourceName = self.attacker.getAction(payoff)
                else:
                    resourceName = self.attacker.getAction()

                #  In case the server went down without his knowledge
                #  is the probe wasted or not?
                if self.debug:
                    print "Ground truth before probe: "
                    print self.stateManager.activeResources
                while(resourceName in self.stateManager.inactiveResources):
                    #  TODO: This might forever loop, make changes
                    #  the server went down and the attacker didn't know
                    #  Update the attackers knowledge state
                    if(self.debug):
                        print resourceName,
                        print "This resource has been reimaged"
                    #  If the attacker knew from before  that this server
                    #  has been reimaged then dont see the reimage again
                    #  However, for now we assume that the attacker has no
                    #  knowledge about the downtime, hence he asumes that
                    #  the reimage happened now
                    self.attacker.seeReimage(resourceName,
                                             self.params["currentTime"])
                    self.askAtt = True
                    self.askDef = False  # No point asking the defender

		    if self.attackerIsLearner:
		        payoff = self.stateManager.util.getPayoff()["ATT"]
			resourceName = self.attacker.getAction(payoff)
		    else:
                    	resourceName = self.attacker.getAction()
                #  The attacker belief about all the resources should be
                #  set to active since he assuemes nothng about downtime
                self.attacker.knowledge.setActive()
                if(resourceName in self.stateManager.activeResources):
                    #  Check if an interim reimage happened before executing
                    #  the probe on the resource. First update the knowledge
                    #  state of the attacker
                    self.attacker.checkKnowledgeState(resourceName,
                                                      self.stateManager
                                                      .activeResources
                                                      [resourceName]
                                                      .previouslyReimaged(),
                                                      self.params[
                                                          "currentTime"])
                    #  Then update the knowledge state of the defender, if
                    #  the defender sees the probes
                    if((self.missRate is None) or not (self.missProbe())):
                        # print "Defender seeing probe"
                        self.defender.seeProbe(resourceName,
                                               self.params["currentTime"])

                    #  Update the utility
                    self.stateManager.updateUtility(self.params["currentTime"])

                    #  Then update the ground truth with a probe
                    self.stateManager.probe(resourceName,
                                            self.params["currentTime"])
                    #  until the fautly sensors are implemented we can use
                    #  assert here that the ks and ground truth are the same
                    #  Launch the attack
                    compromise = self.stateManager.attack(resourceName)
                    if compromise:
                        #  update the attacker ks in case attack succeeds
                        self.attacker.seeCompromise(resourceName)
                        # debugging.logCompromise(resourceName,
                        #                        self.params["currentTime"])
                    self.askDef = True
                    self.askAtt = True
                    # Update this action as last action that took place
                    self.stateManager.updateLastAction(
                                                0, self.params["currentTime"])
                    self.attacker.knowledge.actionTaken();
                else:
                    #  In case a null action is seen do nothing. No need to ask
                    #  the defender since there's no change in his state
                    assert(resourceName is None)
                    self.askAtt = True
                    self.askDef = False
                # debugging.eventLog(it, resourceName)
            #  For a defender action
            elif(it[2] == 1):
                # print "Here"
                if self.defenderIsLearner:
                    payoff = self.stateManager.util.getPayoff()["DEF"]                    
                    resourceName = self.defender.getAction(payoff)
                else:
                    resourceName = self.defender.getAction()
                #  A defender will never reimage a server that is down
                #  Change the ground truth
                if(resourceName):
                    # print resourceName
                    if(type(resourceName) is tuple):
                        # print resourceName
                        wakeTime = resourceName[1]
                        self.eventQueue.append((wakeTime, None, 1))
                        self.sortEventQueue()
                    else:
                        # print resourceName
                        assert (resourceName in
                                self.stateManager.activeResources)
                        # If the attacker loses control his state
                        # must be updated

                        #  Update the utility
                        self.stateManager.updateUtility(
                                                    self.params["currentTime"])

                        if(self.stateManager.activeResources[resourceName]
                                .getControl() == "ATT"):
                            self.attacker.seeReimage(
                                resourceName,
                                self.params["currentTime"])
                            self.askAtt = True
                        self.defender.seeReimage(resourceName,
                                                 self.params["currentTime"])
                        self.stateManager.reimage(resourceName,
                                                  self.params["currentTime"])
                        #  Change from active resource to inactive
                        self.stateManager.inactiveResources[resourceName] =\
                            self.stateManager.activeResources[resourceName]
                        del self.stateManager.activeResources[resourceName]
                        assert (self
                                .stateManager
                                .inactiveResources[resourceName]
                                .lastReimage == self.params["currentTime"])
                        # Make sure the defender reigsters the change
                        # in his ks
                        self.askDef = True
                        #  Queue the wake up event
                        wakeTime = self.params["currentTime"] +\
                            self.params["downTime"]
                        self.eventQueue.append((wakeTime, resourceName, 2))
                        self.sortEventQueue()
                        #  Update this action as last action that took place
                        self.stateManager.updateLastAction(
                                                1, self.params["currentTime"])
                        self.defender.knowledge.actionTaken()
                else:
                    #  No  action can be taken by the defender
                    assert(resourceName is None)
                    if self.probeToken:
                        self.askDef = False
                    else:
                        # This should not be true. You want the defender to take
                        # another action only when it's state changes, there's no
                        # point in queuing up another action if the state is the
                        # same.
                        # But this is going to lead to potential points where
                        # the state doesn't change for either and the game ends
                        # quickly
                        self.askDef = False
                    self.askAtt = False
            elif(it[2] == 3):
                #  Fake probe to be detected by the defender
                # debugging.log("Fake probe on " + it[1])
                resourceName = "Fake on" + it[1]
                self.defender.seeProbe(it[1], self.params["currentTime"])
                self.getFakeProbe()
                self.askDef = True
            # debugging.eventLog(it, resourceName)
        #  At the end of the execution the history should be saved?
        #  ground truth is already being updateda
        self.updateInformation()
        return 0

    def missProbe(self):
        #  Uniform sampling at the moment
        random.seed()
        rand = random.random()
        if rand < self.missRate:
            # debugging.log("Defender is missing this probe")
            return True
        else:
            # debugging.log("Defender will see this probe")
            return False

    def fakeProbe(self):
        # Should only be called when no fake probes queued
        for item in self.eventQueue:
            assert(item[2] != 3)

        nextTime = random.expovariate(self.falseRate)
        return nextTime

    def getDefenderGradient(self):
        if hasattr(self.defender, "Grad"):
            return self.defender.Grad;
        else:
            return None;

    def simulate(self):
        # Starts the simulation
        if self.simType == 1:
            while(self.gameState):
                self.updateInformation()
                # self.defender.debugKnowledge()
                # print self.params["currentTime"]
                if self.askAtt:
                    self.askAttacker()
                if self.askDef:
                    self.askDefender()
                self.executeAction()
                # debugging.printAgentKS(self.attacker, self.defender)
                # debugging.printTruth(self.stateManager.activeResources,
                #                       self.stateManager.inactiveResources)

        #  Use the recorded history to get the utility
        self.stateManager.updateUtility(self.params["currentTime"])
        self.updateInformation()

        #  Set up the utility function
        # u = Utility(self.utilParams)
        # utilFunc = u.getUtility(self.utilType)
        # payoff = utilFunc(self.stateManager.stateHistory)
        # print payoff
        payoff = self.stateManager.util.getPayoff()
        # print payoff
        #  if self.debug:
        # pprint.pprint(self.stateManager.stateHistory)

        return payoff
