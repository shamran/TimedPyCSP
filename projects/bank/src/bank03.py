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
  def __init__(self, name="",meanWT=10.0):
    self.name = name
    self.waittime = round(expovariate(1/meanWT))

  def __repr__(self):
    return "(%s,%s)"%(self.waittime,self.name)

@process
def Generator(i,number,meanTBA, meanWT, customerWRITER):
  """Generaters a customer with a given time difference"""
  for numberInserted in range(number):
    Wait(expovariate(1/meanTBA))
    #print "%64.0f: G%d: %s =%s"%(Now(),i,numberInserted,c.name)
    customerWRITER(Customer(name = "Customer%d:%02d"%(i,numberInserted),meanWT = meanWT))
    #print "%64.0f: G%d: sent customer %s =%s"%(Now(),i,numberInserted,c.name)
  print "%64.0f: G%d: retires"%(Now(),i) 
  retire(customerWRITER)


@process
def Bank(meanWait,customerREADER):
  """Handles the action inside the bank """
  t = False
  customers =  []
  mon = Monitor() 
  try:
    while True:
      print "%94.0f: blocking wait to receive customer"%(Now())
      msg = customerREADER()
      print "%94.0f: %s enter bank"%(Now(),msg.name)
      heappush(customers,(Now()+msg.waittime,msg))
      mon.observe(len(customers))
      while len(customers)>0:
        print "%94.0f: B: timeout is:%f"%(Now(),customers[0][0]-Now())
        (g,msg) = Alternation([(customerREADER,None),
                               (Timeout(seconds=customers[0][0]- Now()),None)
                             ]).select()
        if g == customerREADER:
          heappush(customers,(Now()+msg.waittime,msg))
          print "%94.0f: %s enter bank"%(Now(),msg.name)
        else:
          ntime,ncust = heappop(customers)
          print "%94.0f: %s left bank"%(Now(),ncust.name)
        mon.observe(len(customers))
        #print "%94.0f: B:"%(Now())
        #show_tree(customers,total_width=140,offset=10)
        #print customers
        print "%94.0f: Length of queue in bank %d"%(Now(),len(customers))
  except ChannelRetireException:
    """All generators have retired just empty the queue"""
    print "%94.0f: All genreators have retired"%Now()
    while(len(customers)>0):
        Wait(customers[0][0]-Now())
        ntime,ncust = heappop(customers)
        mon.observe(len(customers))
        print "%94.0f: %s left bank"%(Now(),ncust.name)
    Histo = mon.histogram()
    plt = SimPlot()
    plt.plotHistogram(Histo,xlab='length of queue',ylab='number of observation', 
                    title="# customers in bank",
                    color="red",width=1)                         
    plt.mainloop()  
    return

if __name__ == "__main__":
  print "main starting"
  nprocesses = 10 
  customer = Channel(buffer=9,mon = mon)
  
  numberCustomersprprocess=10
  meanTBA = 3.0
  meanWT =  5.0
  b = Bank(meanWT,+customer)
  Parallel(
    b,
    [Generator(i,numberCustomersprprocess,meanTBA, meanWT,-customer)
      for i in range (nprocesses)]
  )
  print b.executed
  print "end"

