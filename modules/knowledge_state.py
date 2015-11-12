import math
import itertools
import numpy as np
from copy import deepcopy

debug = 0


class KnowledgeState(object):
    """Stores the knowledge state of the agent."""

    def __init__(self, owner, args):
        """Takes a dict containing
        resourceList: list of resource names
        time: current time
        alpha: alpha value for incrementing prob
        """
        resourceInfo = {
            "total no of probes": 0,
            "probes since last reimage": 0,
            "last probe": 0,
            "last reimage": 0,
            "probability of compromise": 0,
            "control": "DEF",
            "status": "HEALTHY",
            "Reimage Count": 0
            }

        self.resources = {}

        for item in args["resourceList"]:
            self.resources[item] = deepcopy(resourceInfo)
        self.time = args["time"]
        self.owner = owner
        self.alpha = args["alpha"]
        self.downtime = args["downtime"];

        if "miss" in args:
            self.miss = args["miss"];
        else:
            self.miss = 0;

        self.actionHistory = {}
        self.previousAction = 0
        self.previousTime = 0  # Unused for now
        
        self.lastActionTime = 0;

        if debug:
            print self.owner

    def updateTime(self, time):
        self.time = time

    def changeStatus(self, resource, status):
        if(status == -1):
            self.resources[resource]["status"] = "COMPR"
        elif(status == 0):
            self.resources[resource]["status"] = "PROBED"
        elif(status == 1):
            self.resources[resource]["status"] = "HEALTHY"
        else:
            self.resources[resource]["status"] = "DOWN"

    def sawProbe(self, resource):
        # Make sure that time is updated before calling this
        if debug:
            print "In Probe KS " + resource
            print self.resources
        self.resources[resource]["total no of probes"] += 1
        self.resources[resource]["probes since last reimage"] += 1
        self.resources[resource]["last probe"] = self.time
        # self.resources[resource]["probability of compromise"] \
        self.computeProb(resource)
        # if debug:
        # print "Before status change"
        # print self.resources
        self.changeStatus(resource, 0)
        # if debug:
        # print "Afte probe: "
        # print self.resources

    def sawReimage(self, resource):
        # Make sure time is updated before calling this
        self.resources[resource]["last reimage"] = self.time
        self.resources[resource]["probes since last reimage"] = 0
        self.resources[resource]["probability of compromise"] = 0
        self.resources[resource]["control"] = "DEF"
        self.resources[resource]["Reimage Count"] += 1
        self.changeStatus(resource, 2)
        # print self.resources

    def sawServerWake(self, resource):
        # Only the defender sees this
        self.changeStatus(resource, 1)

    def sawServerDown(self, resource):
        # On seeing that a server is down changes the status of that
        # server to reflect this
        self.resources[resource]["status"] = "DOWN"

    def setActive(self):
        # Should set all the resources to active...may not be used
        for name, info in self.resources.iteritems():
            if info["status"] == "DOWN":
                self.changeStatus(name, 1)
        return 0

    def setResourceControl(self, resource, control):
        self.resources[resource]["control"] = control

    def getTotalProbes(self, resource):
        return self.resources[resource]["total no of probes"]

    def getProbesSinceLastReimage(self, resource):
        return self.resources[resource]["probes since last reimage"]

    def getLastProbe(self, resource):
        return self.resources[resource]["last probe"]

    def getLastReimage(self, resource):
        return self.resources[resource]["last reimage"]

    def getProbability(self, resource):
        return self.resources[resource]["probability of compromise"]

    def getControlByMe(self):
        return [k for k, v in self.resources.iteritems()
                if v["control"] == self.owner]

    def getControlByOther(self):
        return [k for k, v in self.resources.iteritems()
                if v["control"] != self.owner]

    def getActiveResources(self):
        # print "In active resources"
        # print self.resources
        return [k for k, v in self.resources.iteritems()
                if v["status"] != "DOWN"]

    def getActiveControlByMe(self):
        return list(set(self.getActiveResources()).
                    intersection(self.getControlByMe()))

    def getActiveControlByOthers(self):
        return list(set(self.getActiveResources()).
                    intersection(self.getControlByOther()))

    def _computeProb(self, resource):
        """Increment probability of compromise depending on curve used"""
        # print "Computing probability of of compromise"
        if(self.resources[resource]["probes since last reimage"] == 0):
            return 0
        else:
            # print "Getting probability - computing"
            return (1 - math.exp(-self.alpha * self.resources[resource][
                    "probes since last reimage"]/float(1 - self.miss)))
            # print self.resources[resource]["probability of compromise"]

    def computeProb(self, resource):
        self.resources[resource]["probability of compromise"] =\
            self._computeProb(resource)

    def getMaxProbed(self, resourceList):
        if resourceList:
            maxServer = None
            maxCount = -1
            for item in resourceList:
                if (self.resources[item]["probes since last reimage"] >
                   maxCount):
                    maxServer = item
                    maxCount = self.resources[item][
                        "probes since last reimage"]
            assert(maxServer is not None)
            return (maxServer, maxCount);
        else:
            return (None, None);

    def getLastProbed(self, klist):
        #activeList = self.getActiveResources()
        #if activeList:
        if klist:
            lastProbed = None
            lastTime = -1
            for name in klist:
                if self.resources[name]["probes since last reimage"] > 0\
                   and self.resources[name]["last probe"] > lastTime:
                    lastProbed = name
            return (lastProbed, lastTime)
        else:
            return (None, -1)

    def calculateHealth(self, N):
        activeList = self.getActiveResources()
        if activeList:
            probMatrix = []
            for server in activeList:
                prob = self._computeProb(server)
                probMatrix.append(prob)
            # print probMatrix

            serverIter = itertools.combinations(
                [i for i in range(len(probMatrix))], N)

            health = 0

            for comb in serverIter:
                temp = 1
                for ind, prob in enumerate(probMatrix):
                    if ind in comb:
                        temp *= probMatrix[ind]
                    else:
                        temp *= 1 - probMatrix[ind]
                health += temp
            return health
        else:
            return 0

    def calculateExpectation(self):
        activeList = self.getActiveResources()
        expectation = 0
        if activeList:
            for server in activeList:
                prob = self._computeProb(server)
                expectation += prob
            N = len(activeList)
            expectation /= N
        # print "expected number of servers is: " + str(expectation)
        return expectation

    def actionTaken(self):
        self.lastActionTime = self.time;

    def periodsElapsed(self, eventTime, period):
        return (self.time - eventTime)/period;


    # This function computes all the features that might be used by
    # a learning algorithm. These are features that are ``machine
    # independent.''
    def calculateDefenderInvariantFeatures(self, period):
        totalProbed = 0;
        
        #(P)eriods (E)lapsed (S)ince Post-Reimage (P)robe
        averagePESPIfProbed = 0; 
        maxPESPIfProbed = 0;
        minPESPIfProbed = float("inf");

        #(P)eriods (E)lapsed (S)ince (R)eimage
        averagePESR = 0;
        averagePESRIfProbed = 0;
        maxPESR = 0;
        maxPESRIfProbed = 0;
        
        averageProbeCount = 0; 
        averageProbeCountIfProbed = 0;
        maxProbe = 0; 
        maxCompromiseProb = 0;

        upEstimate = self.calculateExpectation();

        for name, info in self.resources.iteritems():
            periodsElapsedSinceProbed = \
                self.periodsElapsed(self.getLastProbe(name), period);
            
            periodsElapsedSinceReimage = \
                self.periodsElapsed(self.getLastReimage(name), period);
            averagePESR += periodsElapsedSinceReimage;

            probeCount = self.getProbesSinceLastReimage(name);

            compromiseProbability = self.getProbability(name);

            if probeCount > maxProbe:
                maxProbe = probeCount;
            if periodsElapsedSinceReimage > maxPESR:
                maxPESR = periodsElapsedSinceReimage;
            if compromiseProbability > maxCompromiseProb:
                maxCompromiseProb = compromiseProbability;
                    
            if info["status"] == "PROBED":
                totalProbed += 1;
                averagePESPIfProbed += periodsElapsedSinceProbed;
                averagePESRIfProbed += periodsElapsedSinceReimage;
                averageProbeCountIfProbed += probeCount;
                if periodsElapsedSinceReimage > maxPESRIfProbed:
                    maxPESRIfProbed = periodsElapsedSinceReimage
                if periodsElapsedSinceProbed > maxPESPIfProbed:
                    maxPESPIfProbed = periodsElapsedSinceProbed

        numResources = len(self.resources);
        fracProbed = totalProbed/numResources;
        averageProbeCount = averageProbeCount/numResources;
        averagePESR = averagePESR/numResources;

        if totalProbed > 0:
            averagePESPIfProbed = averagePESPIfProbed/totalProbed;
            averagePESRIfProbed = averagePESRIfProbed/totalProbed;
            averageProbeCountIfProbed = averageProbeCountIfProbed/totalProbed;
                    

        periodsSinceAction = self.periodsElapsed(self.lastActionTime, period);

        invariantFeatures = {"constant" : 1, "fracProbed": fracProbed, \
                                 "periodsSinceAction" : periodsSinceAction, \
                                 "averagePESR" : averagePESR, \
                                 "averagePESRIfProbed" : averagePESRIfProbed, \
                                 "maxPESR" : maxPESR, \
                                 "maxPESRIfProbed": maxPESRIfProbed, \
                                 "averagePESPIfProbed" : averagePESPIfProbed, \
                                 "maxPESPIfProbed" : maxPESPIfProbed, \
                                 "averageProbeCount" : averageProbeCount, \
                                 "averageProbeCountIfProbed" : averageProbeCountIfProbed, \
                                 "maxProbe" : maxProbe, \
                                 "maxCompromiseProb" : maxCompromiseProb, \
                                 "upEstimate" : upEstimate };

        return invariantFeatures;

    def calculateLastTwoResources(self):
        activeList = self.getActiveResources();
        lastProbed = self.getLastProbed(activeList)[0];
        if lastProbed is None:
            return (None, None);    

        newList = list(activeList);
        newList.remove(lastProbed);
        penultimateProbed = self.getLastProbed(newList)[0];
        if penultimateProbed is None:
            return (lastProbed, None);

        return (lastProbed, penultimateProbed);

    def calculateFeaturesMatrix(self, period):
        if self.owner == "ATT":
            return self.calculateAttackerFeaturesMatrix(period);

        if self.owner == "DEF":
            return self.calculateDefenderFeaturesMatrix(period);


    # Return matrix of all features as a numpy matrix. 
    def calculateDefenderFeaturesMatrix(self, period):
        invariantFeatures = self.calculateDefenderInvariantFeatures(period);
        
        invariantFeaturesAsList = \
            [ invariantFeatures[key] for key in sorted(invariantFeatures.keys())];

        lastProbed = self.calculateLastTwoResources();
        
        allFeatures = None;

        index = 1;
        indexToNameMap = {};
        for name in sorted(self.resources.keys()):
            indexToNameMap[index] = name; index += 1;

            resourceSpecificFeatures = \
                self.calculateDefenderResourceFeatures(name, period, invariantFeatures, lastProbed)
            allResourceFeatures = list(invariantFeaturesAsList);
            allResourceFeatures.extend(resourceSpecificFeatures);
            if allFeatures is None:
                allFeatures = np.array(allResourceFeatures);
            else:
                allFeatures = np.vstack([allFeatures, np.array(allResourceFeatures)]);


        numFeatures = allFeatures.shape[1];        
        noneFeatures = [1];
        noneFeatures.extend([0] * (numFeatures - 1));

        allFeatures = np.vstack([np.array(noneFeatures), allFeatures]);
        indexToNameMap[0] = None;        

        if debug: 
            print "All features: ", allFeatures;
        
        return (allFeatures, indexToNameMap);

    def calculateAttackerFeaturesMatrix(self, period):
        lastProbed = self.calculateLastTwoResources();
        maxProbed = self.getMaxProbed(self.resources)[1];

        allFeatures = None;

        periodsSinceAction = self.periodsElapsed(self.lastActionTime, period);
        reimages = 0;
        for name, info in self.resources.iteritems():
            reimages += info["Reimage Count"];

        invariantFeatures = [0, 1, periodsSinceAction, reimages];

        index = 1;
        indexToNameMap = {};
        for name in sorted(self.resources.keys()):
            indexToNameMap[index] = name; index += 1;

            resourceSpecificFeatures = \
                self.calculateAttackerResourceFeatures(name, period, lastProbed, maxProbed);
            allResourceFeatures = list(invariantFeatures);
            allResourceFeatures.extend(resourceSpecificFeatures);
            if allFeatures is None:
                allFeatures = np.array(allResourceFeatures);
            else:
                allFeatures = np.vstack([allFeatures, np.array(allResourceFeatures)]);


        numFeatures = allFeatures.shape[1];        
        noneFeatures = [1];
        noneFeatures.extend([0] * (numFeatures - 1));

        allFeatures = np.vstack([np.array(noneFeatures), allFeatures]);
        indexToNameMap[0] = None;        

        if debug: 
            print "All features: ", allFeatures;
        
        return (allFeatures, indexToNameMap);


    def calculateAttackerResourceFeatures(self, name, period, lastProbed, maxProbe):
        features = [];

        activeControlByOthers = self.getActiveControlByOthers();
        features.append(int(name not in activeControlByOthers));
        features.append(int(name in activeControlByOthers));
        
        hasBeenProbed = int(self.resources[name]["status"] == "PROBED");
        features.append(hasBeenProbed); 

        compromised = int(self.resources[name]["status"] == "COMPR");
        features.append(compromised);

        uncompromised = int(self.resources[name]["status"] != "COMPR");
        features.append(uncompromised);

        periodsElapsedSinceProbed = \
            self.periodsElapsed(self.getLastProbe(name), period);
        features.append(periodsElapsedSinceProbed); 
        features.append(uncompromised*periodsElapsedSinceProbed);
        
        isLast = int(lastProbed[0] == name);
        features.append(isLast); 
        features.append(uncompromised*isLast);
        
        probeCount = self.getProbesSinceLastReimage(name);
        features.append(probeCount);
        features.append(uncompromised*probeCount);
        features.append(uncompromised*probeCount/float(periodsElapsedSinceProbed));
        
        isMaxProbe = int(probeCount == maxProbe);
        features.append(isMaxProbe); 
        features.append(uncompromised*isMaxProbe);
        if maxProbe > 0:
            unprobedness = 1 - float(probeCount)/maxProbe;
        else:
            unprobedness = 1;
        
        features.append(unprobedness);
        features.append(uncompromised*unprobedness);
        
        itsDown = int(self.time < (self.getLastReimage(name) + self.downtime));
        features.append(itsDown);

        return features;
        

    def calculateDefenderResourceFeatures(self, name, period, invariant, lastProbed):        
        # invariant is a dictionary containing the invariant features, 
        # and is used to speed up computations. lastProbed a tuple of the 
        # names (possibly None) of the two last machines to be probed and 
        # have not been reimaged. This is also passed to save computation.  

        # Total number features including the NO-OP feature.
        # Should think of a way to do this without hardcoding
        # this number. 
        #numberFeatures = 15;        
              
        #if name is None:
        #    return [1].append([0] * (numberFeatures - 1));
        
        features = [0];

        hasBeenProbed = int(self.resources[name]["status"] == "PROBED");
        features.append(hasBeenProbed); 
    
        probeCount = self.getProbesSinceLastReimage(name);
        features.append(probeCount); 
        
        compromiseProbability = self.getProbability(name);
        features.append(compromiseProbability); 

        periodsElapsedSinceReimage = \
            self.periodsElapsed(self.getLastReimage(name), period);
        
        features.append(periodsElapsedSinceReimage); 
        features.append(periodsElapsedSinceReimage*hasBeenProbed); 
        
        periodsElapsedSinceProbed = \
            self.periodsElapsed(self.getLastProbe(name), period);
        features.append(periodsElapsedSinceProbed); 
        features.append(periodsElapsedSinceProbed*hasBeenProbed);

        isLast = int(lastProbed[0] == name);
        features.append(isLast); 

        isSwitch = int(lastProbed[1] == name);
        features.append(isSwitch); 

        # The remianing features are booleans indicating whether 
        # the machine is the one that attains each of the extremal 
        # (max/min) features among the invariant features. 
        isMaxPESR = int(periodsElapsedSinceReimage == invariant["maxPESR"]);
        features.append(isMaxPESR); 
        
        isMaxPESRProbed = \
            hasBeenProbed*int(periodsElapsedSinceReimage == invariant["maxPESRIfProbed"]);
        features.append(isMaxPESRProbed); 

        isMaxPESPIfProbed = \
            hasBeenProbed*int(periodsElapsedSinceProbed == invariant["maxPESPIfProbed"]);
        features.append(isMaxPESPIfProbed); 

        isMaxProbe = \
            int(probeCount == invariant["maxProbe"]);
        features.append(isMaxProbe); 

        isMaxCompromised = \
            int(compromiseProbability == invariant["maxCompromiseProb"]);
        features.append(isMaxCompromised); 

        isDown = \
            int(self.resources[name]["status"] == "DOWN");
        features.append(isDown);

        return features;
