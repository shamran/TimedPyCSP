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
      print "%64.0f: G%d: %s =%s"%(time,i,numberInserted,c.name)
      customerWRITER(c)
      print "%64.0f: G%d: sent customer %s =%s"%(time,i,numberInserted,c.name)
      t_event = time + round(expovariate(1/meanTBA))
      numberInserted+=1
    print "%64.0f: G%d: enters barrier "%(time,i)
    barrierWRITER(0)
    print "%64.0f: G%d: enters barrier2 "%(time,i)
    barrierREADER()
    print "%64.0f: G%d: increments time "%(time,i)
    time+=1
  print "%64.0f: G%d: retires"%(time,i) 
  retire(customerWRITER)
  try:
    while True:
      barrierWRITER(0)
      barrierREADER()
      time +=1
  except ChannelPoisonException:
    print "%64.0f: G%d: got poison"%(time,i) 

@process
def Servicedisk(customerREADER):
    try:
        while True:
            customer = customerREADER()
            print Now(),": ",customer, "entered servicedisk"
            Wait(customer.meanWT)
            print Now(),": ",customer, "left servicedisk"
    except ChannelPoisonException:
        pass

@process
def Bank(customerREADER,barrierWRITER, barrierREADER, servicediskWRITER ):
  """Handles the action inside the bank """
  t = False
  customers =  []
  time = 0
  
  @choice
  def action(__channel_input):
    global t
    print "%94.0f: B: im in action; ending the alt loop"%time
    t = True

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
          print "%94.0f: B: done alt"%time
          print "%94.0f: B: Length of queue in bank %d"%(time,len(customers))
          break
        elif g == customerREADER:
          print "%94.0f: B: adding a customer %s"%(time,msg)
          heappush(customers,(time+msg.waittime,msg))
          print "%94.0f: B:"%(time)
          #show_tree(customers,offset=93)
          print customers
      while len(customers)>0 and customers[0][0]<=time:
        ntime,ncust = customers.pop()
        print "%94.0f: %s left bank"%(ntime,ncust.name)
      print "%94.0f: Length of queue in bank %d"%(time,len(customers))
      time+=1
  except ChannelRetireException:
    """All generators have retired just empty the queue"""
    print "%94.0f: All genreators have retired"%time
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
          print "%124.0f: Barr: got done for %d processes"%(time,i+1)
        print "%124.0f: Barr: got done for all processes"%time
        
        for i in range (nprocesses):
          signalWRITER(True)
          print "%124.0f: Barr: sent done to %d processes"%(time,i+1)
        print "%124.0f: Barr: sent continue to all procceses"%time
        time+=1
  except ChannelPoisonException:
      pass


if __name__ == "__main__":
  print "main starting"
  nprocesses = 1
  customer = Channel()
  barrierDone = Channel()
  barrierContinue = Channel()
  queue = Channel(10000)
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
