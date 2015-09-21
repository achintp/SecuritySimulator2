import json
from argparse import ArgumentParser
import modules.simulator as Simulator
import os
import numpy as np

def readJson(jsonFolder, weightsFile):
    with open(jsonFolder + "/simulation_spec.json") as f:
        data = json.load(f)
    
    if weightsFile == "":
        weights = None;
    else:
        weightsFile = jsonFolder + "/" + weightsFile;

        if os.path.isfile(weightsFile):        
            with open(weightsFile) as f:
                weights = json.load(f)
                weights = np.asarray(weights);
                weights = weights.transpose();
#                print "using weights:", weights
        else:
            print "warning: specified weights file '" + weightsFile + "' not found, proceeding without..."
    assign = data["assignment"]
    config = data["configuration"]
    params = {}

    params["weights"] = weights
    params['IOFolder'] = jsonFolder
    #  params['startTime'] = int(config["startTime"])a
    #  Environmental parameters
    params['startTime'] = 0
    params['endTime'] = int(config["endTime"])
    params['downTime'] = int(config["downTime"])
    params['missRate'] = float(config["Probe miss rate"])
    params['falseRate'] = float(config["False probe rate"])

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
    params["attControlShift"] = float(config["Attacker Control Shift"]) * \
        int(config['resources'])
    params["attDownSlope"] = float(config["Attacker Down Slope"])
    params["attDownShift"] = float(config["Attacker Down Shift"]) * \
        int(config['resources'])
    params["defControlSlope"] = float(config["Defender Control Slope"])
    params["defControlShift"] = float(config["Defender Control Shift"]) * \
        int(config['resources'])
    params["defDownSlope"] = float(config["Defender Down Slope"])
    params["defDownShift"] = float(config["Defender Down Shift"]) * \
        int(config['resources'])

    params["attControlWeight"] = float(config["Attacker Control Weight"])
    params["defControlWeight"] = float(config["Defender Control Weight"])

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
    parser.add_argument('weightsFile', type=str, nargs="?", default="")
    args = parser.parse_args()

    params = readJson(args.jsonFolder, args.weightsFile)
    params["samples"] = args.samples
    return params


def writeJson(payoffs, gradient, obs, args):
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
                #"Total Downtime":payoffs['totalDownTime'],
                "payoff": payoffs["DEF"],
                "gradient" : gradient.transpose().tolist()
                })

            with open(args['IOFolder'] + "/observation_" + str(obs)
                      + ".json", "w") as outFile:
                json.dump(payoff, outFile, indent=2)



def runSimulator(params):
    sim = Simulator.Simulator(params)
    payoff = sim.simulate()
    (gradient) = sim.getDefenderGradient();
#    print sim.stateManager.getUtilState();
    return (payoff, gradient)


def main():
    args = parseArgs()
    rps = int(args["runs per sample"])
    for i in range(args["samples"]):
        defGradient = None;
        cPayoff = {
            "totalProbes": 0,
            "totalDowntime": 0,
            "DEF": 0,
            "ATT": 0,
            }
        for j in range(0, rps):
            (payoff, gradient) = runSimulator(args)
            if defGradient is None:
                defGradient = gradient;
            else:
                defGradient += gradient;
            
            for k, v in payoff.iteritems():
                cPayoff[k] += v

        defGradient /= rps

        for k, v in cPayoff.iteritems():
            # print cPayoff[k]
            cPayoff[k] /= rps
            # print cPayoff[k]
        # print "\n\n"
        writeJson(cPayoff, defGradient, i, args)

if __name__ == '__main__':
    main()
