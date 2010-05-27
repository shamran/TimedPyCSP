from pycsp.simulation import *
from random import expovariate,seed
from heapq import *
seed(12)

class Customer:
  def __init__(self, name="",meanWT=10.0):
    self.name = name
    self.waittime = expovariate(1/meanWT)

  def __repr__(self):
    return "%s,%s"%(self.waittime,self.name)


@process
def Generator(i,number,meanTBA, meanWT, customerWRITER):
  """Generaters a customer with a given time difference"""
  for numberInserted in range(number):
    Wait(expovariate(1/meanTBA))
    customerWRITER(
      Customer(name = "Customer%d:%02d"%(i, numberInserted),
               meanWT = meanWT))

  print "%64.0f: G%d: retires"%(Now(),i) 
  retire(customerWRITER)

@process
def Bank(customerREADER):
  """Handles the action inside the bank """
  try:
    while True:
      print "%94.0f: B: waits for customer"%Now()
      customer = customerREADER()

      print "%94.0f: B: adding a customer %s to queue"%(
        Now(),customer)
      Wait(customer.waittime)
      print "%94.0f: B: customer %s exits queue"%(
        Now(),customer)

  except ChannelRetireException:
      print "%94.0f: B: got retire"%(Now())
      pass

if __name__ == "__main__":
  nprocesses = 1
  numberCustomers=5
  queue = Channel(buffer=numberCustomers*nprocesses)
  meanTBA = 3.0
  meanWT = 3.0
  Parallel(
    Bank(+queue),
    [Generator(i,numberCustomers,meanTBA, meanWT, -queue)
      for i in range (nprocesses)]
  )
