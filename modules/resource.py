import math
import random


class Resource(object):
    """Defines the resource object. Pass in a dict containing
        name: name of resource
        alpha: alpha value for calculating prob
    """
    def __init__(self, kwargs):
        self.name = kwargs["name"]
        self.probesSinceLastReimage = 0
        self.totalProbes = 0
        self.probCompromise = 0
        self.reimageCount = 0
        self.totalDowntime = 0
        self.status = "HEALTHY"
        self.controlledBy = "DEF"
        self.alpha = kwargs["alpha"]
        self.probeHistory = []
        self.lastReimage = -1
        self.downTime = []

    def report(self):
        return({"Status": self.status,
                "Name": self.name,
                "Probes till now": self.probesSinceLastReimage,
                "Total Probes till now": self.totalProbes,
                "Probability of Compromise": self.probCompromise,
                "Reimage Count": self.reimageCount,
                "Total Downtime": self.totalDowntime,
                "Control": self.controlledBy,
                "Probe History": self.probeHistory,
                "Last ReImage": self.lastReImage,
                "Downtimes": self.downTime})

    def getStatus(self):
        return self.status

    def changeStatus(self, status):
        if(status == -1):
            self.Status = "COMPR"
        elif(status == 0):
            self.Status = "PROBED"
        elif(status == 1):
            self.Status = "HEALTHY"
        else:
            self.Status = "DOWN"

    def incrementProb(self):
        """Increment probability of compromise depending on curve used"""
        if(self.probesSinceLastReimage == 0):
            self.probCompromise = 0
        else:
            self.probCompromise = (1 - math.exp(-self.alpha *
                                                self.probesSinceLastReimage))

    def isCompromised(self):
        # Currently uses a simple random uniform sampling.
        random.seed()
        rand = random.random()
        if rand < self.probCompromise:
            return 1
        else:
            return 0

    def perviouslyReimaged(self):
        # Checks if the last action performed on this was a reimage
        return (self.probesSinceLastReimage == 0)
