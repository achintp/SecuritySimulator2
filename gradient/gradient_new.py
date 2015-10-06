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

def evaluateWeights(attackers, environment_json, results, weightsFile="", init=False):
    avgGradient = None;
    avgPayoff = 0;

    for t in range(trials):
        if init and t > 0:
            break;
        trialGradient = None;
        trialPayoff = 0;

        for attacker, probability in attackers.iteritems():

            with open(environment_json) as f:
                data = json.load(f);
                data["assignment"]["ATT"].append(attacker);
    
                with open(results + "/simulation_spec.json", "w") as f:
                    json.dump(data, f, indent = 2);
        
                subprocess.call("python ../runSimulator.py ./" + results + " 1 " + weightsFile, shell=True)

                with open(results + "/observation_0.json", "r") as f:
                    result = json.load(f);
        
                for player in result["players"]:
                    if player["role"] == "DEF":
                        if trialGradient is None:
                            trialGradient = probability*np.asarray(player["gradient"]).transpose();
                        else:
                            trialGradient = trialGradient + probability*np.asarray(player["gradient"]).transpose();
                        
                        print "payoff against attacker ", attacker, " on this trial was ", player["payoff"]
                        trialPayoff += probability*player["payoff"];                
                        break

        if avgGradient is None:
            avgGradient = trialGradient;
        else:
            avgGradient = avgGradient + trialGradient;

        avgPayoff += trialPayoff;
        print "Payoff for this trial was: ", trialPayoff;
#        print "Gradient for this trial was: ", trialGradient;

    avgPayoff = avgPayoff/float(trials);
    avgGradient = avgGradient;

    return (avgPayoff, avgGradient)


def doDescent(attackers, environment_json, dist_index):
    os.chdir(os.getcwd());
    results = "results_directory"

    try:
        os.mkdir(results);
    except OSError as exc: 
        pass

    stepsize = 100;


    print "initializing run..."
    (currentPayoff, currentGradient) = evaluateWeights(attackers, environment_json, results, weightsFile="", init=True);

    #currentWeights = np.random.random_sample(currentGradient.shape)/100;
    currentWeights = np.zeros(currentGradient.shape);
    with open(results + "/currentWeights.json", "w") as f:
        json.dump(currentWeights.transpose().tolist(), f);

    print "first run..."
    (currentPayoff, currentGradient) = evaluateWeights(attackers, environment_json, results, weightsFile="currentWeights.json");
    print "Payoff is now:", currentPayoff

    while stepsize > .001: 
        print currentWeights;
        candidateWeights = currentWeights + stepsize*currentGradient;

        with open(results + "/candidateWeights.json", "w") as f:
            json.dump(candidateWeights.transpose().tolist(), f);
        (nextPayoff, nextGradient) = evaluateWeights(attackers, environment_json, results, weightsFile="candidateWeights.json");

        if nextPayoff > currentPayoff:
            print "taking gradient step..."
            with open(results + "/currentWeights.json", "w") as f:
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
            (currentPayoff, currentGradient) = evaluateWeights(attackers, environment_json, results, weightsFile="currentWeights.json");
        
def main():
    environment_json = "current_env.json";
    distribution_json = "current_dist.json";

    with open(distribution_json) as f:
        data = json.loads(json.dumps(eval(f.read())))
    
    distributions = data['distributions'];

    # Whats the use of the index
    index = 0
    for distribution in distributions:
        attackers = distribution["data"]["ATT"];
        doDescent(attackers, environment_json, index)


if __name__ == '__main__':
    main()
