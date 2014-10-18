import copy
import time
import json
import random
import pprint
import agents
import strategies
import knowledge_state
from state_manager import StateManager


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
        self.gameState = -1
        self.askAtt = True
        self.askDef = True
        self.simType = 0
        self.attSwitch = True  # For NO-OP, may not use this
        self.defSwitch = True  # FOr NO-OP, may noy use this
        token = "probe"  # Shift all these into inside the strategies
        self.debug = 1

        # Initialize the utility parameters
        self.initUtility(args)

        # Set the agent strategies in these
        self.defStrategy = None
        self.attStrategy = None
        for k, v in args["defenderList"].iteritems():
            self.defStrategy = v
        for k, v in args["attackerList"].iteritems():
            self.attStrategy = v

        # Initialize the event queue
        f = (self.params["endTime"], 0, -1)
        self.eventQueue = [f]

        # Initialize the state manager and the resources
        self.stateManager = StateManager(**{
            "resourceList": args["resourceList"], "alpha": args["alpha"]})
        self.params["resourceReports"] = self.state.resourceReportsList

        # Initialize the agents
        self.initAgents(args)

    def initUtility(self, args):
        self.utilParams = {}
        self.utilParams["dtCOst"] = args["dtCost"]
        self.utilParams["prCost"] = args["prCost"]
        self.utilParams["DEF"] = args["DEF"]
        self.utilParams["ATT"] = args["ATT"]
        self.utilParams["downTime"] = args["downTime"]

    def initAgents(self, args):
        #  We probably don't need a list of agents, since its two player
        for k, v in args["attackerList"].iteritems():
            d = {
                "name": k,
                "strategy": v,
                "resourceList": args["resourceList"],
                "time": self.params["currentTime"]
                }
            self.attacker = agents.Attacker(**d)

        for k, v in args["defenderList"].iteritems():
            d = {
                "name": k,
                "strategy": v,
                "resourceList": args["resourceList"],
                "time": self.params["currentTime"]
                }
            self.defender = agents.Defender(**d)

    def updateInformation(self):
        # Should update the ground truth information state
        self.stateManager.updateState(self.params["currentTime"])
        info = {}  # isnt required. Consider removing
        info = self.stateManager.resourceReportsList

        self.params["resourceReports"] = self.stateManager.resourceReportsList
        info["time"] = self.params["currentTime"]

    def askAttacker(self):
        # Will ask the attacker for the time of the next attack
        # The attacker will return a queue event just stating that
        # wake him when the time to act is upon us

        nextEvent = self.attacker.getActionTime(self.params["currentTime"])
        self.eventQueue.append(nextEvent)
        self.sortEventQueue()

    def askDefender(self):
        # Analogous to askAttacker. Defined as different functions
        # for convenience in later additions.

        nextEvent = self.defender.getActionTime(self.params["currentTime"])
        self.eventQueue.append(nextEvent)
        self.sortEventQueue()

    def executeAction(self):
        # The agent needs to be asked what action to execute depending on the
        # current knowledge state. Must also take care of other queue events
        # that include servers waking up, false probes, horizon end time and
        # others. The eventQueue must have tuples corresponding to
        # <time, action, id>
        # The update of state should be done right after the execution
        self.askAtt = False
        self.askDef = False

        if(self.eventQueue[0][0] > self.params["endTime"]):
            # This is never going to happen since the endtime is a queued event
            print "Game over"
            self.gameState = 0
            return
        else:
            # If one or more event is queued at the same time then shuffle them
            # randomly. There should be no bias for events in ties.
            if(len(self.eventQueue) > 2):
                if (self.eventQueue[0][0] == self.eventQueue[1][0]):
                    self.shuffleEvents()
            #  Pop the next event from the queue
            it = self.eventQueue.pop(0)
            self.params["currentTime"] = it[0]
            if(self.debug):
                print it
            #  Check who queued the event
            #  For the end of the horizon
            if(it[2] == -1):
                self.gameState = 0
                if(self.debug):
                    print "Game ending"
                return 0
            #  For a server waking up
            elif(it[2] == 2):
                if(self.debug):
                    print it[1] + " is up and running"
                #  Update the server status in the state manager
                self.stateManager.activeResources[it[1]] =\
                    self.stateManager.inactiveResources[it[1]]
                del self.stateManager.inactiveResources[it[1]]
                self.stateManager.activeResources[it[1]].isWoken(
                    self.params["currentTime"], self.params["downTime"])
                #  The defender knowledge state should be updated
                self.defender.seeServerWake(self.params["currentTime"], it[1])
                self.askDef = True
            #  For an attacker action
            elif(it[2] == 0):
                resourceName = self.attacker.getAction()
                #  In case the server went down without his knowledge
                #  is the probe wasted or not?
                while(resourceName in self.stateManager.inactiveResources):
                    #  the server went down and the attacker didn't know
                    #  Update the attackers knowledge state
                    if(self.debug):
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

                    resourceName = self.attacker.getAction
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
                                                      .previouslyReimaged)
                    #  Then update the knowledge state of the defender, since
                    #  the defender sees all the probes
                    self.defender.seeProbe(resourceName,
                                           self.params["currentTime"])
                    #  Then update the ground truth with a probe
                    self.stateManager.probe(resourceName,
                                            self.params["currentTime"])
                    #  until the fautly sensors are implemented we can use
                    #  assert here that the ks and ground truth are the same
                    #  TODO Add here
                    #  Launch the attack
                    compromise = self.stateManager.attack(resourceName)
                    if compromise:
                        #  update the attacker ks in case attack succeeds
                        self.attacker.seeCompromise(resourceName)
                    self.askDef = True
                    self.askAtt = True
                else:
                    #  In case a null action is seen do nothing. No need to ask
                    #  the defender since there's no change in his state
                    assert(resourceName is None)
                    self.askAtt = True
                    self.askDef = False
            #  For a defender action
            elif(it[2] == 1):
                resourceName = self.defender.getAction()
                #  A defender will never reimage a server that is down
                #  Change the ground truth
                if(resourceName):
                    assert (resourceName in self.stateManager.activeResources)
                    #  If the attacker loses control his state must be updated
                    if(self.stateManager.activeResources[resourceName]
                            .getControl() == "ATT"):
                        self.attacker.seeReimage(resourceName,
                                                 self.params["currentTime"])
                        self.askAtt = True
                    self.stateManager.reimage(resourceName, time)
                    #  Change from active resource to inactive
                    self.stateManager.inactiveResources[resourceName] =\
                        self.stateManager.activeResources[resourceName]
                    del self.stateManager.activeResources[resourceName]
                    assert (self.stateManager.inactiveResources[resourceName]
                            .lastReimage == self.params["currentTime"])
                    #  Make sure the defender reigsters the change in his ks
                    self.askDef = True
                    #  Queue the wake up event
                    wakeTime = self.params["currentTime"] +\
                        self.params["downTime"]
                    self.eventQueue.append((wakeTime, resourceName, 2))
                    self.sortEventQueue()
                else:
                    #  No  action can be taken by the defender
                    assert(resourceName is None)
                    self.askDef = True
                    self.askAtt = False

        #  At the end of the execution the history should be saved?
        #  ground truth is already being updateda
        self.updateInformation()
        return 0

    def simulate(self):
        # Starts the simulation
        if self.simType == 1:
            while(self.gameState):
                self.updateInformation()
                if self.askAtt:
                    self.askAttacker()
                if self.askDef:
                    self.askDefenderf()
                self.executeAction()
