import strategies
from knowledge_state import KnowledgeState


class Agent(object):
    """Base class for all agents"""
    def __init__(self, **kwargs):
        """takes dict as argument. Must contain
        strategy - strategy seperating name and param by -
        time - current time. Should be 0 at init
        resourceList -  list of resource names
        alpha - alpha value for prob calc
        """
        # Initialization of the strategy params
        st = kwargs["strategy"].split("-")
        self.stName = st[0]
        self.stParam = st[1]
        self.extraParams = {}
        # Initialize the knowledge model
        self.knowledge = KnowledgeState(kwargs)

    def seeProbe(self, resource, time):
        """Called by simulator"""
        # Will update the time and then knowledge state when probe is seen
        self.knowledge.updateTime(time)
        self.knowledge.sawProbe(resource)

    def seeReimage(self, resource):
        """Called by simulator"""
        # Will update time and then knowledge state when reimage is seen
        self.knowledge.updateTime(time)
        self.knowledge.sawReimage(resource)

    def changeStatus(self, resource, status):
        """Called by simulator"""


class Attacker(Agent):
    """Defines the attacker agent. Derives from agent"""
    def __init__(self, **params):
        super(Attacker, self).__init__(**params)
        self.type = "ATT"
        self.setStrategy()

    def setStrategy(self):
        """Assigns the specific strategy to the agent"""
        if hasattr(self, "strategy"):
            a = strategies.AttackerStrategies({})
            self.decideAction = a.getStrategy(self.strategy)

    def getAction(self):
        # It's important that the knowledge be updated before calling
        action = self.decideAction(self.knowledge, self.stParam)
        self.extraParams["previousAction"] = action[0]
        return action
        
    def checkKnowledgeState(self, resource, prevReimage):
        # The attacker on probe will also check ks mismatch
        # This is to detect whether a reimage happened in the interim
        # The attacker will then update it's ks accordingly
        if(prevReimage):
            self.seeReimage(resource)
            self.seeProbe(resource)


class Defender(Agent):
    """Defines the defender agent. Derives from agent"""
    def __init__(self, **params):
        super(Defender, self).__init__(**params)
        self.type = "DEF"
        self.setStrategy()

    def setStrategy(self):
        """Assigns the specific strategy to the agent"""
        if hasattr(self, "strategy"):
            a = strategies.DefenderStrategies({})
            self.decideAction = a.getStrategy(self.strategy)

    def getAction(self):
        # I know that both the agents are the same. Maybe rethink design
        return self.decideAction(self.knowledge, self.stParam)
