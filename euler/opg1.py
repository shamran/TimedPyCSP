# To change this template, choose Tools | Templates
# and open the template in the editor.


__author__="ebdrup"
__date__ ="$Nov 12, 2009 10:45:00 PM$"

from pycsp.threads import *

@process
def three (cout):
  for i in range(3, 1000, 3):
    if i%5 != 0:
      cout(i)
  retire(cout)

@process
def five (cout):
  for i in range(5, 1000, 5):
    cout(i)
  retire(cout)


@process
def printer (cin):
  total = 0
  
  while True:
      try:
          total = total + cin()
      except ChannelRetireException:
        print total
        break

A = Channel()
Parallel(
  three(A.writer()),
  five(A.writer()),
  printer(A.reader())
)