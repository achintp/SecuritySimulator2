import resource

debug = 0


class StateManager(object):
    """Manages the resources and any changes to them"""
    def __init__(self, *args, **kwargs):
        """Takes a dict containing
            resourceList: list of resource names
            alpha: alpha value for prob calculation
        """
        self.currentTime = 0
        self.activeResources = {}
        self.inactiveResources = {}
        self.stateHistory = {}
        self.resourceReportList = {}

        #  Keep track of instantaneous utility
        self.lastAction = (0, "START")
        self.args = {}
        self.args["alpha"] = kwargs["alpha"]
        self.addResources(kwargs["resourceList"])
        self.resourceReports()

    def addResources(self, args):
        for name in args:
            self.args["name"] = name
            self.activeResources[name] = resource.Resource(self.args)
            self.activeResources[name].report()
        try:
            del self.args["name"]
        except KeyError:
            print "KeyError"
            pass

    def resourceReports(self):
        """Stores the resource report in the resourceReportList"""
        self.resourceReportList = {}
        for k, v in self.activeResources.iteritems():
            self.resourceReportList[k] = v.report()
        for k, v in self.inactiveResources.iteritems():
            self.resourceReportList[k] = v.report()

    def getResource(self, resource):
        result = {}
        if resource in self.activeResources:
            result[resource] = self.activeResources[resource]
            return result
        elif resource in self.inactiveResources:
            result[resource] = self.inactiveResources[resource]
            return result

    def recordHistory(self):
        state = {}
        t = {}
        for k, v in self.activeResources.iteritems():
            t[k] = v.report()
        state["activeResources"] = t
        t = {}
        for k, v in self.inactiveResources.iteritems():
            t[k] = v.report()
        state["inactiveResources"] = t
        self.stateHistory[self.currentTime] = state

    def updateState(self, time):
        self.updateTime(time)
        self.recordHistory()
        self.resourceReports()

    def updateTime(self, time):
        self.currentTime = time

    def probe(self, resource, time):
        self.activeResources[resource].probe(time)

    def attack(self, resource):
        return self.activeResources[resource].attack()

    def reimage(self, resource, time):
        if debug:
            print "In reimage"
            print resource
        self.activeResources[resource].reimage(time)

    def setUtility(self, utilObj):
        self.util = utilObj

    def getUtilState(self):
        downResources = len(self.inactiveResources)
        attResources = 0
        defResources = 0
        for k, v in self.activeResources.iteritems():
            if(v.controlledBy == "ATT"):
                attResources += 1
            if(v.controlledBy == "DEF"):
                defResources += 1
        return (attResources, defResources, downResources)

    def updateLastAction(self, action, time):
        """
        action - 0 is probe
                 1 is reimage
                 2 is server wake
                 -1 is the end
        time - current time
        """
        if action == 0:
            self.lastAction = (time, "ATT")
        elif action == 1:
            self.lastAction = (time, "DEF")
        elif action == 2:
            self.lastAction = (time, "WAKE")
        elif action == -1:
            self.lastAction = (time, "END")
        else:
            print "Unrecognized event in util update"
            assert(False)

    def updateUtility(self, time):
        state = self.getUtilState()
        self.util.L2P(state, time, self.lastAction)
