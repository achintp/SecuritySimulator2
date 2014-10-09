
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
            "status": "HEALTHY"
            }

        self.resources = {}

        for item in args["resourceList"]:
            self.resources[item] = resourceInfo
        self.time = args["time"]
        self.owner = owner
        self.alpha = args["alpha"]
        self.actionHistory = {}
        self.previousTime = 0  # Unused for now

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
        self.resources[resource]["total no of probes"] += 1
        self.resources[resource]["probes since last reimage"] += 1
        self.resources[resource]["last probe"] = self.time
        self.resources[resource]["probability of compromise"] \
            = self.computeProb()
        self.changeStatus(0, resource)

    def sawReimage(self, resource):
        # Make sure time is updated before calling this
        self.resources[resource]["last reimage"] = self.time
        self.resources[resource]["probes since last reimage"] = 0
        self.resources[resource]["probability of compromise"] = 0
        self.resources[resource]["control"] = "DEF"
        self.changeStatus(2, resource)

    def sawServerWake(self, resource):
        # Only the defender sees this
        self.changeStatus(1, resource)

    def sawServerDown(self, resource):
        # On seeing that a server is down changes the status of that
        # server to reflect this
        self.resources[resource]["status"] = "DOWN"

    def setAllActive(self, resource):
        # Should set all the resources to active...may not be used
        return 0

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

    def getActiveResources(self):
        return [k for k, v in self.resources.iteritems()
                if v["status"] != "DOWN"]

    def getActiveControlByMe(self):
        return list(set(self.getActiveResources).
                    intersection(self.getControlByMe))
