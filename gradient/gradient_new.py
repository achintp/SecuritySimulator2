import json
import random
import os, sys
import subprocess
import numpy as np
import math, random 

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

def evaluateWeights(attackers, directory, init=False):
    avgGradient = None;
    avgPayoff = 0;

    for t in range(trials):
        if init and t > 0:
            break;
        trialGradient = None;
        trialPayoff = 0;

        for attacker, probability in attackers.iteritems():

            with open(directory + "/current_env.json") as f:
                data = json.load(f);
                data["assignment"]["ATT"].append(attacker);
    
                with open(directory + "/results/simulation_spec.json", "w") as f:
                    json.dump(data, f, indent = 2);        


                callstring = "python ../runSimulator.py ./" + directory + "/results" + " 1 ";
                subprocess.call(callstring, shell=True)

                with open(directory + "/results/observation_0.json", "r") as f:
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

    avgPayoff = avgPayoff/float(trials);
    avgGradient = avgGradient/float(trials);

    return (avgPayoff, avgGradient)

def doAscentRandomRestarts(attackers, directory, eqPayoff=0):
    bestPayoff = 0;
    haveBest = os.path.isfile(directory + "/best.json"); 
    
    if haveBest:
        with open(directory + "/best.json") as f:
            best = json.load(f);
            bestPayoff = best["payoff"];

    print "initializing run... no purpose other than to get dimensions"
    (currentPayoff, currentGradient) = evaluateWeights(attackers, directory, init=True);
    
    # Should be a column vector
    size = currentGradient.size;
    print "deciding random restart points..."

    weights0 = np.zeros((size, 1));
    weightsList = [weights0];
    # Change these parameters to go faster.
    samples = 3;
    fractions = [.1,.25,.5,1];
    ######################################

    for fraction in fractions:
        for sample in range(samples):
            permutation = np.random.permutation(size);
            giveWeight = math.floor(size*fraction);
            indices = permutation[0:giveWeight];

            weights = np.zeros((size, 1));
            for index in indices:
                weights[index,0] = random.random();                        
        
            weightsList.append(weights);
    for weight in weightsList:
        (weights, payoff) = doAscent(weight, attackers, directory);
        print "##### DONE WITH ONE ASCENT #####";
        print "best payoff so far: ", bestPayoff;
        print "current payoff: ", payoff;
        print "equilibrium payoff: ", eqPayoff;
        if payoff > bestPayoff:
            bestPayoff = payoff;
            with open(workingdir + "/best.json", "w") as f:
                best = {};
                best["payoff"] = payoff;
                best["weights"] = weights;
                json.dump(best, f, indent = 2);
    

def doAscent(weights, attackers, directory):
    converged = False;
    while not converged:
        (weights, newPayoff, newDirection, converged) = doAscentLineSearch(weights, attackers, directory, .5, .25);        
        gradientNorm = newDirection.transpose().dot(newDirection);
        print "gradientNorm ", gradientNorm
        converged = converged or (gradientNorm < .00000001);
    return (weights, newPayoff);

def doAscentLineSearch(startWeights, attackers, directory, decayRate, stopParameter):
    t0 = .0001;
    stepsize = 10;

    with open(directory + "/eval_weights.json", "w") as f:
        json.dump(startWeights.transpose().tolist(), f);
    
    print "recalculating gradient...";
    (startPayoff, direction) = evaluateWeights(attackers, directory);
    print "gradient:", direction

    while stepsize > t0:
        stopCriterion = startPayoff - stopParameter*stepsize*direction.transpose().dot(direction);
        print "line search terminates at payoff: ", stopCriterion

        step = startWeights + stepsize*direction;
        
        with open(directory + "/eval_weights.json", "w") as f:
            json.dump(step.transpose().tolist(), f);

        print "evaluating step..."
        (stepPayoff, stepGradient) = evaluateWeights(attackers, directory);
        print "step payoff:", stepPayoff

        if stepPayoff > stopCriterion:
            return (step, stepPayoff, stepGradient, False);

        stepsize = decayRate*stepsize;
        print "decreasing step size to: ", stepsize

    return (startWeights, startPayoff, direction, True);
        
def main():
    working_directory = "working"

    try:
        os.chdir(os.getcwd());
        os.mkdir("./" + working_directory + "/results");
    except OSError as exc: 
        pass
    
    with open(working_directory + "/current_dist.json") as f:
        data = json.loads(json.dumps(eval(f.read())))
    
    distributions = data['distributions'];

    for distribution in distributions:
        attackers = distribution["data"]["ATT"];
        eqPayoff = distribution["payoffs"]["DEF"]["payoff"];
        doAscentRandomRestarts(attackers, working_directory, eqPayoff);


if __name__ == '__main__':
    main()
