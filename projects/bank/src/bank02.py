# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="shamran"
__date__ ="$Dec 1, 2009 3:59:26 PM$"

from pycsp.greenlets import *
from random import expovariate
from heapq import *

t = False

@choice
def action(__channel_input):
	global t
	print "im in action"
	t = True

class Customer:
	def __init__(self, name="",meanTBA=10.0):
		self.name = name
		self.waittime = round(expovariate(1/meanTBA))

@process
def Generator(number,meanTBA, customerOUT,barrierIN,barrierOUT):
	"""Generaters a customer with a given time difference"""
	t_event = 0
	time = 0
	numberInserted = 0
	while numberInserted<number:
		if t_event<=time:
			c = Customer(name = "Customer%02d"%(numberInserted,),meanTBA=meanTBA)
			print "%8.0f: Generator : sending customer %s"%(time,numberInserted)
			customerOUT(c)
			t_event = time + round(expovariate(1/meanTBA))
			numberInserted+=1
		barrierIN(0)
		barrierOUT()
		print "Generator incrementing time"
		time+=1
	print "%8.0f: Generator retires"%time	
	retire(customerOUT)	

@process
def Bank(meanWait,customerOUT,barrierIN,barrierOUT):
	"""Handles the action inside the bank """
	global t
	customers =  []
	time = 0
	while True:
		barrierIN(0)
		while not t:
			print "bank waits in alt"
			try:
				Alternation([{
				barrierOUT:action(),
				customerOUT:'heappush(customers,(time+__channel_input.waittime,__channel_input))'
				}]).execute()
			except ChannelRetireException:
				"""All generators have retired just empty the queue"""
				print "%8.0f: All genreators have retires, we can empty the queue and exit"%time
				while(len(customers)>0):
					ntime,ncust = heappop(customers)
					print "%8.0f: %s left bank"%(ntime,ncust.name)
				return
			print "Bank out of alt, len %d "%len(customers),
		print customers
		t = False
		if len(customers)>0:
			ntime,ncust = heappop(customers)
			if ntime<=time:
				print "%8.0f: %s left bank"%(time,ncust.name)
			else:
				heappush(customers,(ntime,ncust))
		print "Bank incrementing time"
		time+=1
	
@process
def Barrier(nprocesses, barrierIN, signalOUT):
	""" Barrier, waits for a signal from nprocesses in signalIN and the inparallel sends a signal to all on signalOUT"""	
	while True:
		for i in range (nprocesses):
			barrierIN()
		print "got done for all processes"
		
		for i in range (nprocesses):
			signalOUT(True)
		print "sent continue to all procceses"

if __name__ == "__main__":
	print "main starting"
	nprocesses = 3
	customer = Channel()
	barrierDone = Channel()
	barrierContinue = Channel()
	numberCustomers=10
	meanTBA = 10.0
	meanWT = 20.0
	Parallel(
    Bank(meanWT,+customer,-barrierDone,+barrierContinue),
    1*Generator(numberCustomers,meanTBA,-customer,-barrierDone,+barrierContinue),
		Barrier(2,+barrierDone,-barrierContinue)
	)
