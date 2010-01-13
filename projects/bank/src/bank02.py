# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="shamran"
__date__ ="$Dec 1, 2009 3:59:26 PM$"

#from pycsp.simulation import *
from pycsp.greenlets import *
from random import expovariate,seed
from heapq import *
seed(12)
class Customer:
  def __init__(self, name="",meanWT=10.0):
    self.name = name
    self.waittime = round(expovariate(1/meanWT))

  def __repr__(self):
    return "%s,%s"%(self.waittime,self.name)

@process
def Generator(i,number,meanTBA, meanWT,customerWRITER,barrierWRITER,barrierREADER):
  """Generaters a customer with a given time difference"""
  t_event = 0
  time = 0
  numberInserted = 0
  while numberInserted<number:
    if t_event<=time:
      c = Customer(name = "Customer%d:%02d"%(i,numberInserted),meanWT=meanWT)
      customerWRITER(c)
      print "%64.0f: G%d: sent customer %s =%s"%(time,i,numberInserted,c.name)
      t_event = time + round(expovariate(1/meanTBA))
      numberInserted+=1
    barrierWRITER(0)
    barrierREADER()
    time+=1
  retire(customerWRITER)
  try:
    while True:
      barrierWRITER(0)
      barrierREADER()
      time +=1
  except ChannelPoisonException:

@process
def Bank(customerREADER,barrierWRITER, barrierREADER, servicediskWRITER ):
  """Handles the action inside the bank """
  t = False
  customers =  []
  time = 0
  try:
    while True:
      print "%94.0f: B: enters barrier"%time
      barrierWRITER(0)
      while True:
        print "%94.0f: B: waits in alt"%time
        (g,msg) = Alternation([{
        barrierREADER:None,
        customerREADER:None
        }]).select()
        if g == barrierREADER:
          break
        elif g == customerREADER:
          print "%94.0f: B: adding a customer %s"%(time,msg)
          heappush(customers,(time+msg.waittime,msg))
      while len(customers)>0 and customers[0][0]<=time:
        ntime,ncust = customers.pop()
        print "%94.0f: %s left bank"%(ntime,ncust.name)
      time+=1
  except ChannelRetireException:
    """All generators have retired just empty the queue"""
    poison(barrierWRITER,barrierREADER,servicediskWRITER)
    while(len(customers)>0):
      ntime,ncust = heappop(customers)
      print "%94.0f: %s left bank"%(ntime,ncust.name)
    return

@process
def Barrier(nprocesses, barrierREADER, signalWRITER):
  """ Barrier, waits for a signal from nprocesses in signalIN and the inparallel sends a signal to all on signalOUT"""  
  time = 0
  try:
      while True:
        for i in range (nprocesses):
          barrierREADER()
        for i in range (nprocesses):
          signalWRITER(True)
        time+=1
  except ChannelPoisonException:
      pass

if __name__ == "__main__":
  print "main starting"
  nprocesses = 1
  customer = Channel()
  barrierDone = Channel()
  barrierContinue = Channel()
  queue = Channel()
  numberCustomers=5
  meanTBA = 3.0
  meanWT = 3.0
  Parallel(
    Servicedisk(+queue),
    Bank(+customer,-barrierDone,+barrierContinue,-queue),
    [Generator(i,numberCustomers,meanTBA, meanWT, -customer,-barrierDone,+barrierContinue)
      for i in range (nprocesses)],
    Barrier(nprocesses+1,+barrierDone,-barrierContinue)
  )
