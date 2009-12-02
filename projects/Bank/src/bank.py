# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="shamran"
__date__ ="$Dec 1, 2009 3:59:26 PM$"

from pycsp.greenlets import *
from random import *

@process
def Time(nprocesses,timeOUT):
	_tmax = 100
	for _t in range (0,_tmax):
		#print "sending time %f"%(_t)
		for i in range (0,nprocesses):
			timeOUT(_t)

@process
def Customer(custid,interval,timeIN,barrierOUT,barrierIN):
	"""Customer walks in waits and leaves"""
	arrived = False
	left = False
	Rnd = Random()
	waittime = 0 
	arrive = Rnd.random()*20
	while True:
		barrierOUT(1)
		barrierIN()
		_t = timeIN()
      		if not arrived and arrive < _t:
			arrive = Rnd.expovariate(1.0/interval)
			#print arrive
		if _t <= arrive and _t+1 > arrive: 
			left = False
			arrived = True
			print "%8.3f : Here I am Customer %s   "%(_t,custid)
			waittime = Rnd.random()*20
		#waits for 5 min.
		if _t<arrive+waittime:
			continue

		if not left:
			print "%8.3f :cust %s waited %8.3f "%(_t,custid,waittime)
			left  = True
			arrived = False
@process
def Barrier(nprocesses, signalIN, signalOUT):
	""" Barrier, waits for a signal from nprocesses in signalIN and the inparallel sends a signal to all on signalOUT"""	
	while True:
		for i in range (0,nprocesses):
			signalIN()
		for i in range (0,nprocesses):
			signalOUT(0)

if __name__ == "__main__":
	print "main starting"
	nprocesses = 3
	time = Channel()
	done = Channel()
	cont = Channel()

	Parallel(
	    [Customer(i,10,time.reader(),-done,+cont) for i in range(5)],
	    Time(5,time.writer()),
	    Barrier(5,+done,-cont)
	)
