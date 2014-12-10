import pprint
import os

identMap = {
    -1: "Game horizon",
    0: "Attacker",
    1: "Defender",
    2: "Downtime",
    3: "Defender"
    }

actionMap = {
    -1: "Ending Game",
    0: "Probing",
    1: "Reimaging",
    2: "Waking up",
    3: "see fake probe on"
    }


def printAgentKS(attacker, defender, fname="events.log"):
    if(fname is None):
        print "Attacker KS"
        for k, v in attacker.knowledge.resources.iteritems():
            pprint.pprint(v)
    else:
        with open(fname, 'a') as f:
            f.write("Attacker KS")
            for k, v in attacker.knowledge.resources.iteritems():
                pprint.pprint(v, stream=f)
    if(fname is None):
        print "Defender KS"
        for k, v in defender.knowledge.resources.iteritems():
            pprint.pprint(v)
    else:
        with open(fname, 'a') as f:
            f.write("Defender KS")
            for k, v in defender.knowledge.resources.iteritems():
                pprint.pprint(v, stream=f)


def printTruth(activeRes, inactiveRes, fname="events.log"):
    if(fname is None):
        print "Active Resources"
        for k, v in activeRes.iteritems():
            pprint.pprint(v.report())
        print "Inactive Resources"
        for k, v in inactiveRes.iteritems():
            pprint.pprint(v.report())
    else:
        with open(fname, 'a') as f:
            f.write("Active resources")
            for k, v in activeRes.iteritems():
                pprint.pprint(v.report(), stream=f)
            f.write("Inactive Resources")
            for k, v in inactiveRes.iteritems():
                pprint.pprint(v.report(), stream=f)


def eventLog(event, resource=None, fname="events.log"):
    if resource is None:
        resource = "None"
    with open(fname, 'a') as f:
        f.write(identMap[event[2]] + " is " + actionMap[event[2]] + " "
                + resource + " at time " + str(event[0]) + "\n")


def logCompromise(resource, time, fname="events.log"):
    with open(fname, 'a') as f:
        f.write("Attacker compromised " + resource
                + " at time " + str(time) + "\n")


def log(string, fname="events.log"):
    with open(fname, 'a') as f:
        f.write(string + "\n")


def refreshLog(fname="events.log"):
    try:
        os.remove(fname)
    except OSError:
        print "Could not delete file"
