import random
import pprint

class Utility(object):
	"""
		Has the utility functions that will be used for 
		generating the payoffs
	"""

	def __init__(self, params):
		"""
			Pass in a dict of params having:
			dtCost: cost of unit downtime
			prCost: cost of unit probe
			DEF: [List of 4 payoff states for control of 0, 1, 2, 3]
			ATT: [List of 4 payoff states for control of 0, 1, 2, 3]
		"""
		self.params = {}
		self.cparams = params

	def getUtility(self, utility):
		if hasattr(self, utility):
			return getattr(self, utility)
		else:
			print "Unrecognized utility function: " + utility

	def simpleCIA(self, data):
		"""
			Simple CIA type utility. Pass in the history of
			state dict. Cost is not associated with reimage
			act, but with the amount of downtime for the
			server. Probes have associated cost.
		"""

		#pprint.pprint(data)

		#Actions costs - downtime and probe costs
		dtCost = self.cparams['dtCost']
		prCost = self.cparams['prCost']
		downTime = self.cparams['downTime']

		#Status payoffs - server control costs
		controlPayoffs = {}
		controlPayoffs['DEF'] = self.cparams['DEF']
		controlPayoffs['ATT'] = self.cparams['ATT']

		self.params['DEF'] = 0
		self.params['ATT'] = 0
		self.params['totalDowntimeCost'] = 0
		self.params['totalProbeCost'] = 0
		self.params['totalDowntime'] = 0
		previousTime = 0
		currentTime = 0
		prevC = {}
		#Tracks the servers under each agents control
		sCount = {
		'DEF':0,
		'ATT':0
		}
		#Tracks the previous controller of each server
		prevC['Server0'] = 'DEF'
		prevC['Server1'] = 'DEF'
		prevC['Server2'] = 'DEF'

		for it in sorted(data.items()):
			# sCount['DEF'] = 0
			# sCount['ATT'] = 0
			# print "------------------>>"+str(it[0])+"\n"
			time = it[0]
			hist = it[1]
			currentTime = time
			timeFactor = currentTime - previousTime
			pTime = previousTime
			previousTime = currentTime
			#Might need to correct this
			# for res, rep in hist['inactiveResources'].iteritems():
				# self.params['totalDowntimeCost'] += timeFactor*dtCost
				# # print "-------->" + res
				# self.params['totalDowntime'] += timeFactor
			# print hist['activeResources']	
			# for res, rep in hist['activeResources'].iteritems():
			# 	sCount[prevC[res]] += 1
			# 	prevC[res] = rep['Control']
			for k,v in sCount.iteritems():
				# print k,v, time
				# print "Do [" + str(currentTime) + "-" + str(pTime) + "] " + "*" +str((controlPayoffs[k])[v])
				# print ']]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]\n'
				#Accrues utility for time period (t-1) to t
				self.params[k] += timeFactor*(controlPayoffs[k])[v]
				sCount[k] = 0
			# print self.params
			#Count servers for each agent at time t
			for res, rep in hist['activeResources'].iteritems():
				sCount[rep['Control']] += 1
			for res, rep in hist['inactiveResources'].iteritems():
				sCount[rep['Control']] += 1


		lastItem = data[max(data.keys(), key=int)]
		for k,v in lastItem.iteritems():
			for s,r in v.iteritems():
				self.params['totalProbeCost'] += r['Total Probes till now']
				self.params['totalDowntime'] += r['Reimage Count']
				# print self.params


		self.params['totalDowntime'] *= downTime
		self.params['totalDowntimeCost'] = self.params['totalDowntime']*dtCost
		payoff = {}
		payoff["totalProbes"] = self.params['totalProbeCost'] 

		self.params['totalProbeCost'] *= prCost		
		payoff["DEF"] = self.params['totalDowntimeCost'] + self.params['DEF']
		payoff["ATT"] = self.params['totalProbeCost'] + self.params['ATT']
		payoff["totalDownTime"] = self.params['totalDowntime']

		# print "---------------------------------------------\n"
		# print payoff
		return payoff