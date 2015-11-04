import os
import sys
import json

def ConvertToGradientDistribFile(filename):
	if(os.path.isfile(filename)):
		with open(filename, 'r') as f:
			data = json.load(f)
		out = {}
		out["distributions"] = data
		with open("current_dist.json", "w+") as f:
			json.dump(out, f)

def ConvertToSimWeightsFile(filename):
	if(os.path.isfile(filename)):
		with open(filename, 'r') as f:
			data = json.load(f)
	weights = data['weights']
	with open("rename_weights_file.json", "w+") as f:
		json.dump(f, weights)

if __name__ == '__main__':
	if(len(sys.argv) < 2):
		print "Too few arguments."
	else:
		func = sys.argv[1]
		filename = sys.argv[2]
		if(func == '1'):
			ConvertToGradientDistribFile(filename)
		elif  func == '2':
			ConvertToSimWeightsFile(filename)			
		else:
			print "Not implemented"
		
