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
                "Last ReImage": self.lastReimage,
                "Downtimes": self.downTime})

    def getStatus(self):
        return self.statu

    def getControl(self):
        return self.controlledBy

    def changeStatus(self, status):
        # print "Changing status to " + str(status)
        if(status == -1):
            self.status = "COMPR"
        elif(status == 0):
            self.status = "PROBED"
        elif(status == 1):
            self.status = "HEALTHY"
        else:
            self.status = "DOWN"

    def isWoken(self, time,  downTime):
        # On waking should change status
        self.totalDowntime += downTime
        self.downTime[-1].append(time)
        self.changeStatus(1)

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

    def previouslyReimaged(self):
        # Checks if the last action performed on this was a reimage
        return (self.probesSinceLastReimage == 0 and (self.lastReimage != -1))

    def probe(self, time):
        self.totalProbes += 1
        self.probesSinceLastReimage += 1
        self.probeHistory.append(time)
        self.incrementProb()
        self.changeStatus(0)

    def reimage(self, time):
        self.lastReimage = time
        self.probesSinceLastReimage = 0
        self.probCompromise = 0
        self.controlledBy = "DEF"
        self.changeStatus(2)
        self.downTime.append([time])
        self.reimageCount += 1

    def attack(self):
        if(self.isCompromised()):
            self.controlledBy = "ATT"
            return True
        else:
            return False
