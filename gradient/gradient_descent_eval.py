import json
import random
import os, sys
import subprocess
import numpy as np

trials = 5;
environments = 7;

def selectAttacker(attackers):
    r = random.random();
    cumulative = 0;
    previousName = None;
    for name, probability in attackers.iteritems():
        if cumulative > r:
            break;
        else:
            previousName = name;
            cumulative += probability
    return previousName

def evaluateWeights(attackers, e, workingdir, weightsFile="", init=False):
    avgGradient = None;
    avgPayoff = 0;

    for t in range(trials):
        if init and t > 0:
            break;
        trialGradient = None;
        trialPayoff = 0;

        for attacker, probability in attackers.iteritems():

            with open('environments/env' + str(e) + '.json') as f:
                data = json.load(f);
                data["assignment"]["ATT"].append(attacker);
    
                with open(workingdir + "/simulation_spec.json", "w") as f:
                    json.dump(data, f, indent = 2);
        
                subprocess.call("python ../runSimulator.py ./" + workingdir + " 1 " + weightsFile, shell=True)

                with open(workingdir + "/observation_0.json", "r") as f:
                    result = json.load(f);
        
                for player in result["players"]:
                    if player["role"] == "DEF":
                        if trialGradient is None:
                            trialGradient = probability*np.asarray(player["gradient"]).transpose();
                        else:
                            trialGradient = trialGradient + probability*np.asarray(player["gradient"]).transpose();
                        
                        #print "payoff against attacker ", attacker, " on this trial was ", player["payoff"]
                        trialPayoff += probability*player["payoff"];                
                        break

        if avgGradient is None:
            avgGradient = trialGradient;
        else:
            avgGradient = avgGradient + trialGradient;

        avgPayoff += trialPayoff;
#        print "Payoff for this trial was: ", trialPayoff;
#        print "Gradient for this trial was: ", trialGradient;

    avgPayoff = avgPayoff/float(trials);
    avgGradient = avgGradient;

    return (avgPayoff, avgGradient)


def doDescent(attackers, e, dist_index):
    os.chdir(os.getcwd());
    workingdir = "results2/env" + str(e) + "_dist" + str(dist_index);
    try:
        os.mkdir(workingdir);
    except OSError as exc: 
        pass

    stepsize = 100;


    print "initializing run..."
    (currentPayoff, currentGradient) = evaluateWeights(attackers, e, workingdir, weightsFile="", init=True);

    currentWeights = np.random.random_sample(currentGradient.shape)/100;
    #currentWeights = np.zeros(currentGradient.shape);
    with open(workingdir + "/currentWeights.json", "w") as f:
        json.dump(currentWeights.transpose().tolist(), f);

    print "first run..."
    (currentPayoff, currentGradient) = evaluateWeights(attackers, e, workingdir, weightsFile="currentWeights.json");
    print "Payoff is now:", currentPayoff

    while stepsize > .001: 
        print currentWeights;
#        print currentGradient
        candidateWeights = currentWeights + stepsize*currentGradient;
#        print "New candidate weights are: " + str(candidateWeights)
        with open(workingdir + "/candidateWeights.json", "w") as f:
            json.dump(candidateWeights.transpose().tolist(), f);
        (nextPayoff, nextGradient) = evaluateWeights(attackers, e, workingdir, weightsFile="candidateWeights.json");
#        print "Next gradient is: ", nextGradient
        if nextPayoff > currentPayoff:
            print "taking gradient step..."
            with open(workingdir + "/currentWeights.json", "w") as f:
                json.dump(candidateWeights.transpose().tolist(), f);
            currentPayoff = nextPayoff;
            currentGradient = nextGradient
            print "Current Gradient: ", currentGradient
            currentWeights = candidateWeights
            print "Payoff is now:", currentPayoff
        else:
            print nextPayoff, " vs ", currentPayoff
            stepsize = stepsize/float(2)        
            print "reducing step size to...", stepsize
            print "recalculating payoff and gradient..."
            (currentPayoff, currentGradient) = evaluateWeights(attackers, e, workingdir, weightsFile="currentWeights.json");
        
def main():
    for e in [1,2,3,4,5,6,7]:
        with open("environments/env" + str(e) + "_dist.json") as f:
            data = json.loads(json.dumps(eval(f.read())))

        workingdir = "results_eval/env" + str(e) + "_dist0"

        distributions = data['distributions'];

        index = 0;
        for distribution in distributions:
            attackers = distribution["data"]["ATT"];
            print "Environment", e
            print "Attackers:", attackers
            print "Eq Payoff:", distribution["payoffs"]["DEF"]["payoff"]
            (currentPayoff, currentGradient) = evaluateWeights(attackers, e, workingdir, weightsFile="currentWeights.json");
            print "Learned Payoff:", currentPayoff
            index += 1;

if __name__ == '__main__':
    main()
