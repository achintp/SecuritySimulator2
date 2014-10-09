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
        self.attackerList = []
        self.defenderList = []
        self.gameState = -1
        self.askAtt = True
        self.askDef = True
        self.simType = 0
        self.attSwitch = True  # For NO-OP, may not use this
        self.defSwitch = True  # FOr NO-OP, may noy use this
        token = "probe"  # Shift all these into inside the strategies

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

