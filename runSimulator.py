import json
from argparse import ArgumentParser
import modules.simulator as Simulator


def readJson(jsonFolder):
    with open(jsonFolder + "/simulation_spec.json") as f:
        data = json.load(f)

    assign = data["assignment"]
    config = data["configuration"]
    params = {}
    params['IOFolder'] = jsonFolder
    #  params['startTime'] = int(config["startTime"])a
    #  Environmental parameters
    params['startTime'] = 0
    params['endTime'] = int(config["endTime"])
    params['downTime'] = int(config["downTime"])
    params['missRate'] = float(config["Probe Miss Rate"])
    params['falseRate'] = float(config["False Probe Rate"])

    # Construct attacker and defender list - fix this goddamn thing
    for st in assign["ATT"]:
        params['attackerList'] = {"A": st}
    for st in assign["DEF"]:
        params['defenderList'] = {"D": st}

    params['ResourceList'] = []
    # Construct resources list - deprecate as well
    for i in range(0, int(config["resources"])):
        params['ResourceList'].append("Server"+str(i))
    # params['ResourceList'] = config["ResourceList"]
    #  Utility params
    params['resources'] = int(config["resources"])
    params['dtCost'] = -float(config["dtCost"])
    params['prCost'] = -float(config["prCost"])

    params["attControlSlope"] = float(config["Attacker Control Slope"])
    params["attControlShift"] = float(config["Attacker Control Shift"])
    params["attDownSlope"] = float(config["Attacker Down Slope"])
    params["attDownShift"] = float(config["Attacker Down Shift"])
    params["defControlSlope"] = float(config["Defender Control Slope"])
    params["defControlShift"] = float(config["Defender Control Shift"])
    params["defDownSlope"] = float(config["Defender Down Slope"])
    params["defDownShift"] = float(config["Defender Down Shift"])

    params["attControlWeight"] = float(config["Attacker Control Weight"])
    #  params["attDownWeight"] = float(config["Attacker Down Weight"])
    params["defControlWeight"] = float(config["Defender Control Weight"])
    #  params["defDownWeight"] = float(config["Defender Down Weight"])

    #l = config["DEF"].split(',')
    #for i in range(0, len(l)):
        #l[i] = float(l[i])
    #params['DEF'] = l

    #l = config["ATT"].split(',')
    #for i in range(0, len(l)):
        #l[i] = float(l[i])
    #params['ATT'] = l

    params['alpha'] = float(config['alpha'])
    params['runs per sample'] = config["runs per sample"]
    return params


def parseArgs():
    parser = ArgumentParser()
    parser.add_argument('jsonFolder', type=str)
    parser.add_argument('samples', type=int)
    args = parser.parse_args()
    params = readJson(args.jsonFolder)
    params["samples"] = args.samples
    return params


def writeJson(payoffs, obs, args):
    payoff = {"players": []}
    for name, strategy in args['attackerList'].iteritems():
        payoff['players'].append({
            # "Name":name,
            "role": "ATT",
            "strategy": strategy,
            # "Total Probes":payoffs['totalProbes'],
            "payoff": payoffs["ATT"]
            })

        for name, strategy in args['defenderList'].iteritems():
            payoff['players'].append({
                # "Name":name,
                "role": "DEF",
                "strategy": strategy,
                # "Total Downtime":payoffs['totalDownTime'],
                "payoff": payoffs["DEF"]
                })

            with open(args['IOFolder'] + "/observation_" + str(obs)
                      + ".json", "w") as outFile:
                json.dump(payoff, outFile, indent=2)


def runSimulator(params):
    sim = Simulator.Simulator(params)
    payoff = sim.simulate()
    return payoff


def main():
    args = parseArgs()
    rps = int(args["runs per sample"])
    for i in range(args["samples"]):
        cPayoff = {
            "totalProbes": 0,
            "totalDowntime": 0,
            "DEF": 0,
            "ATT": 0
            }
        for j in range(0, rps):
            payoff = runSimulator(args)
            for k, v in payoff.iteritems():
                cPayoff[k] += v

        for k, v in cPayoff.iteritems():
            # print cPayoff[k]
            cPayoff[k] /= rps
            # print cPayoff[k]
        # print "\n\n"
        writeJson(cPayoff, i, args)

if __name__ == '__main__':
    main()
