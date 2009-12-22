# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="shamran"
__date__ ="$Dec 1, 2009 3:59:26 PM$"

from pycsp.simulation import *
#from pycsp.greenlets import *
from random import expovariate,seed
from heapq import *
seed(12)
class Customer:
  def __init__(self, name="",meanTBA=10.0):
    self.name = name
    self.waittime = round(expovariate(1/meanTBA))

  def __repr__(self):
    return "(%s,%s)"%(self.waittime,self.name)

@process
def Generator(i,number,meanTBA, customerWRITER):
  """Generaters a customer with a given time difference"""
  t_event = 0
  numberInserted = 0
  while numberInserted<number:
    Wait(t_event)
    c = Customer(name = "Customer%d:%02d"%(i,numberInserted),meanTBA=meanTBA)
    print "%64.0f: G%d: %s =%s"%(Now(),i,numberInserted,c.name)
    customerWRITER(c)
    print "%64.0f: G%d: sent customer %s =%s"%(Now(),i,numberInserted,c.name)
    t_event = round(expovariate(1/meanTBA))
    numberInserted+=1
  print "%64.0f: G%d: retires"%(Now(),i) 
  retire(customerWRITER)


@process
def Bank(meanWait,customerREADER):
  """Handles the action inside the bank """
  t = False
  customers =  []
  
  try:
    while True:
      msg = customerREADER()
      heappush(customers,(Now()+msg.waittime,msg))

      while len(customers)>0:
        print "%94.0f: B: timeout is:%f"%(Now(),customers[0][0]-Now())
        (g,msg) = Alternation([(customerREADER,None),
                               (Timeout(seconds=customers[0][0]- Now()),None)
                             ]).select()
        if g == customerREADER:
          heappush(customers,(Now()+msg.waittime,msg))
        else:
          ntime,ncust = heappop(customers)
          print "%94.0f: %s left bank"%(Now(),ncust.name)

        print "%94.0f: B:"%(Now())
        #show_tree(customers,total_width=140,offset=10)
        #print customers
        print "%94.0f: Length of queue in bank %d"%(Now(),len(customers))
  except ChannelRetireException:
    """All generators have retired just empty the queue"""
    print "%94.0f: All genreators have retired"%Now()
    while(len(customers)>0):
      ntime,ncust = heappop(customers)
      print "%94.0f: %s left bank"%(ntime,ncust.name)
    return

if __name__ == "__main__":
  print "main starting"
  nprocesses = 2 
  customer = Channel()
  numberCustomers=5
  meanTBA = 10.0
  meanWT = 50.0
  Parallel(
    Bank(meanWT,+customer),
    [Generator(i,numberCustomers,meanTBA,-customer)
      for i in range (nprocesses)]
  )
