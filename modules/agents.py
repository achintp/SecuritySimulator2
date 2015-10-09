import strategies
import numpy as np
from knowledge_state import KnowledgeState

debug = 0


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
        self.strategy = st[0]
        self.stParam = st[1]
        self.extraParams = {}  # Can't quite remember what this is
        # Initialize the knowledge model
        # self.knowledge = KnowledgeState(kwargs)

    def seeProbe(self, resource, time):
        """Called by simulator"""
        # Will update the time and then knowledge state when probe is seen
        self.knowledge.updateTime(time)
        self.knowledge.sawProbe(resource)

    def seeReimage(self, resource, time):
        """Called by simulator"""
        # Will update time then knowledge state when reimage is seen
        self.knowledge.updateTime(time)
        self.knowledge.sawReimage(resource)

    def changeStatus(self, resource, status):
        """Called by simulator"""

    def getActionTime():
        """Defined seperately in every agent. Gets time of next action"""

    def getAction():
        """Defined separately in every agent. Gets next action."""


class Attacker(Agent):
    """Defines the attacker agent. Derives from agent"""
    def __init__(self, **params):
        super(Attacker, self).__init__(**params)
        self.owner = "ATT"
        self.setStrategy()
        self.knowledge = KnowledgeState(self.owner, params)

    def setStrategy(self):
        """Assigns the specific strategy to the agent"""
        if hasattr(self, "strategy"):
            if(debug):
                print "Found strategy"
            a = strategies.AttackerStrategies({})
            self.decideAction = a.getStrategy(self.strategy)

    def getAction(self):
        #  It's important that the knowledge be updated before calling
        resourceName = self.decideAction(self.knowledge, self.stParam, False)
        #  self.extraParams["previousAction"] = action[0]
        return resourceName

    def checkKnowledgeState(self, resource, prevReimage, time):
        # The attacker on probe will also check ks mismatch
        # This is to detect whether a reimage happened in the interim
        # The attacker will then update it's ks accordingly
        if((self.knowledge.getProbesSinceLastReimage(resource) != 0) and
                prevReimage):
            # In this case, a reimage happened and the attacker doesn't know
            # about it. This can happen if the attacker had previously
            # probed a machine and it went down and came up before his
            # next probe on it. In this case the attacker registers a
            # reimage and then a probe
            # print "prevImage: " + str(prevReimage) + " time: " + str(time)
            self.seeReimage(resource, time)
            self.seeProbe(resource, time)
        else:
            self.seeProbe(resource, time)

    def loseControl(self, time):
        #  The attacker sees a server he owns get reimaged
        #  However the assumption is its immediately active
        return 0

    def getActionTime(self, time):
        self.knowledge.updateTime(time)
        actionTime = self.decideAction(self.knowledge, self.stParam, True)
        if actionTime is None:
            return actionTime
        self.knowledge.previousTime = actionTime
        return (actionTime, None, 0)

    def seeCompromise(self, resource):
        self.knowledge.setResourceControl(resource, "ATT")


class Defender(Agent):
    """Defines the defender agent. Derives from agent"""
    def __init__(self, **params):
        super(Defender, self).__init__(**params)
        self.owner = "DEF"
        self.setStrategy()
        self.knowledge = KnowledgeState(self.owner, params)

    def setStrategy(self):
        """Assigns the specific strategy to the agent"""
        if hasattr(self, "strategy"):
            a = strategies.DefenderStrategies({})
            self.decideAction = a.getStrategy(self.strategy)

    def getAction(self, reward=None):
        # I know that both the agents are the same. Maybe rethink design
        # print "Before defender action"
        # print self.knowledge.resources
        return self.decideAction(self.knowledge, self.stParam, False)

    def seeServerWake(self, time, resource):
        self.knowledge.updateTime(time)
        self.knowledge.changeStatus(resource, 1)

    def getActionTime(self, time):
        self.knowledge.updateTime(time)
        self.knowledge.calculateAllResourceFeaturesMatrix(1)
        actionTime = self.decideAction(self.knowledge, self.stParam, True)
        if actionTime is None:
            return actionTime
        self.knowledge.previousTime = actionTime
        # print actionTime
        return (actionTime, None, 1)

    def debugKnowledge(self):
        print "Defender knowledge state"
        print self.knowledge.resources

class Learner(Agent):
    def __init__(self, **params):        
        self.weights = params["weights"];

        self.Grad = None;
        self.Z = None;

        self.step = 0;
        self.cumulativePayoff = 0

    def setStrategy(self):
#        print "setting strategy to learning";
        if hasattr(self, "strategy"):
            self.decideAction = getattr(self, "learnerAction")

    def getAction(self, reward=None):
	return self.decideAction(self.knowledge, self.stParam, False, reward)

    def learnerAction(self, knowledge, params, askTime, newPayoff = None):
        params = params.split("_");
        period = float(params[0]);
        beta = float(params[1]);

        if(askTime):
            if knowledge.time < knowledge.previousTime:
                return None
            return knowledge.time + period
        else:
            assert(newPayoff is not None);
            (features, map) = knowledge.calculateAllResourceFeaturesMatrix(period);
            numActions = features.shape[0];
            numFeatures = features.shape[1];
            if self.weights is None:
                self.weights = self.initWeights(numFeatures)
            if self.Z is None:
                self.Z = self.initWeights(numFeatures);
                self.Grad = self.initWeights(numFeatures);
            rawvalue = np.dot(features, self.weights);
            probabilities = self.softmax(rawvalue);
            # A lot of untupling going on here...
            # pick is simply the result of a random draw according
            # to probabilites. 
            pick = np.nonzero(np.random.multinomial(\
                    1,probabilities.transpose().tolist()[0]))[0][0];

            name = map[pick];
            if name in knowledge.getActiveResources():
                action = name;
            else:
#                if name is not None:
#                    print "Selected ", name, "but:", knowledge.resources[name]
                action = None;
            
            reward = newPayoff - self.cumulativePayoff;
            self.cumulativePayoff = newPayoff;
            # Update gradient estimate
            
            self.Grad = self.Grad + (1/float(self.step+1))* \
                (reward*self.Z - self.Grad);
            self.step += 1;
            
            averageFeatures = np.zeros((1,numFeatures));

            for i in range(numActions):
                averageFeatures += probabilities[i,0]*features[i,:];

            score = features[pick,:] - averageFeatures;
            self.Z = beta*self.Z + score.transpose();

            return action

    def initWeights(self, k):
        return np.zeros((k,1));

    def softmax(self, scores):
        max = np.amax(scores);
        unnormalized = np.exp(scores - max);
        z = np.sum(unnormalized);
        return unnormalized/z;

    def getGradient(self):
        return self.Grad;


class LearnerDefender(Learner, Defender):
    def __init__(self, **params):
        Defender.__init__(self, **params);
        Learner.__init__(self, **params);


class LearnerAttacker(Learner, Attacker):
    def __init__(self, **params):
        Attacker.__init__(self, **params);
        Learner.__init__(self, **params);


class LearnerDefenderOld(Defender):
    def __init__(self, **params):
        super(LearnerDefender, self).__init__(**params)
        
        self.weights = params["weights"];

        self.Grad = None;
        self.Z = None;

        self.step = 0;
        self.cumulativePayoff = 0;

    def setStrategy(self):
#        print "setting strategy to learning";
        if hasattr(self, "strategy"):
            self.decideAction = getattr(self, "learnerAction")

    def getAction(self, reward=None):
	return self.decideAction(self.knowledge, self.stParam, False, reward)

    def learnerAction(self, knowledge, params, askTime, newPayoff = None):
        params = params.split("_");
        period = float(params[0]);
        beta = float(params[1]);

        if(askTime):
            if knowledge.time < knowledge.previousTime:
                return None
            return knowledge.time + period
        else:
            assert(newPayoff is not None);
            (features, map) = knowledge.calculateAllResourceFeaturesMatrix(period);
            numActions = features.shape[0];
            numFeatures = features.shape[1];
            if self.weights is None:
                self.weights = self.initWeights(numFeatures)
            if self.Z is None:
                self.Z = self.initWeights(numFeatures);
                self.Grad = self.initWeights(numFeatures);
            rawvalue = np.dot(features, self.weights);
            probabilities = self.softmax(rawvalue);
            # A lot of untupling going on here...
            # pick is simply the result of a random draw according
            # to probabilites. 
            pick = np.nonzero(np.random.multinomial(\
                    1,probabilities.transpose().tolist()[0]))[0][0];

            name = map[pick];
            if name in knowledge.getActiveResources():
                action = name;
            else:
#                if name is not None:
#                    print "Selected ", name, "but:", knowledge.resources[name]
                action = None;
            
            reward = newPayoff - self.cumulativePayoff;
            self.cumulativePayoff = newPayoff;
            # Update gradient estimate
            
            self.Grad = self.Grad + (1/float(self.step+1))* \
                (reward*self.Z - self.Grad);
            self.step += 1;
            
            averageFeatures = np.zeros((1,numFeatures));

            for i in range(numActions):
                averageFeatures += probabilities[i,0]*features[i,:];

            score = features[pick,:] - averageFeatures;
#            print str(features[pick, :])
            self.Z = beta*self.Z + score.transpose();

            return action

    def initWeights(self, k):
        return np.zeros((k,1));


    def softmax(self, scores):
        max = np.amax(scores);
        unnormalized = np.exp(scores - max);
        z = np.sum(unnormalized);
        return unnormalized/z;

    def getGradient(self):
        return self.Grad;
