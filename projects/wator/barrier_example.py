from pycsp.greenlets import *
from time import *
#import pdb; pdb.set_trace()
@process
def numbers (cout):
  for i in range(1,10): 
    print "generating number: %i" %(i)
    cout(i)
  #retire(cout)

@process
def worker (cin, cout, barin, barout):
   while True:
      #try:
        cout(cin()+10)
        barout(1)
        barin()
      #except ChannelRetireException:
      #   break

@process
def barrier (nr, cin, cout):
  while True:
    for i in range(nr):
       cin()
       sleep(1)
       print "%i workers in barrier" %(i+1)
    for i in range(nr):
       cout(1)


@process
def printer (cin):
   while True:
      try:
        print cin() 
      except ChannelRetireException:
         break


num2worker = Channel()
worker2bar = Channel()
bar2worker = Channel()
worker2print = Channel()

Parallel(
      numbers(num2worker.writer()),
      4*worker(num2worker.reader(),worker2print.writer(),bar2worker.reader(),worker2bar.writer()),
      barrier(4,worker2bar.reader(),bar2worker.writer()),
      printer(worker2print.reader())
)
