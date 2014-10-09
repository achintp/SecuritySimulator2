import Simulator
import json
from argparse import ArgumentParser

def readJson(jsonFolder):
	with open(jsonFolder + "/simulation_spec.json") as f:
		data = json.load(f)
	#print data

	assign = data["assignment"]
	config = data["configuration"]
	params = {}
	params['IOFolder'] = jsonFolder
	# params['startTime'] = int(config["startTime"])
	params['startTime'] = 0
	params['endTime'] = int(config["endTime"])
	params['downTime'] = int(config["downTime"])

	#Construct attacker and defender list - fix this goddamn thing
	for st in assign["ATT"]:
		params['attackerList'] = {"A":st}
	for st in assign["DEF"]:
		params['defenderList'] = {"D":st}

	params['ResourceList'] = []
	#Construct resources list - deprecate as well
	for i in range(0,3):
		params['ResourceList'].append("Server"+str(i))
	# params['ResourceList'] = config["ResourceList"]
	params['dtCost'] = -float(config["dtCost"])
	params['prCost'] = -float(config["prCost"])

	l = config["DEF"].split(',')
	for i in range(0, len(l)):
		l[i] = float(l[i])
	params['DEF'] = l

	l = config["ATT"].split(',')
	for i in range(0, len(l)):
		l[i] = float(l[i])
	params['ATT'] = l	
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
	payoff = {"players":[]}
	for name, strategy in args['attackerList'].iteritems():
		payoff['players'].append({
			# "Name":name,
			"role":"ATT",
			"strategy":strategy,
			# "Total Probes":payoffs['totalProbes'],
			"payoff":payoffs["ATT"]
			})

	for name, strategy in args['defenderList'].iteritems():
		payoff['players'].append({
			# "Name":name,
			"role":"DEF",
			"strategy":strategy,
			# "Total Downtime":payoffs['totalDownTime'],
			"payoff":payoffs["DEF"]
			})

	with open(args['IOFolder'] + "/observation_" + str(obs)\
		 + ".json", "w") as outFile:
		json.dump(payoff, outFile, indent=2)



def runSimulator(params):
	sim = Simulator.SimulateCyberScenario(params)
	payoff = sim.Simulate()
	return payoff

def main():
	args = parseArgs()
	rps = int(args["runs per sample"])
	for i in range(args["samples"]):
		cPayoff = {
			"totalProbes": 0,
			"totalDownTime": 0,
			"DEF": 0,
			"ATT": 0
		}
		for j in range(0,rps):
			payoff = runSimulator(args)
			for k,v in payoff.iteritems():
				cPayoff[k] += v

		for k,v in cPayoff.iteritems():
			#print cPayoff[k]
			cPayoff[k] /= rps
			#print cPayoff[k]
		#print "\n\n"
		writeJson(cPayoff, i, args)	

if __name__=='__main__':
	main()
	
