# To change this template, choose Tools | Templates
# and open the template in the editor.
from pycsp.greenlets import *
from numpy import *


a = arange(1)
print "a1"
print a
a = a.resize(5,5)
print "a2"
print a

__author__="shamran"
__date__ ="$Nov 18, 2009 8:00:20 PM$"

#    Aquarium = matrix( [[1,2,3],[11,12,13],[21,22,23]])
@process
def counter(cout, limit):
  for i in xrange(limit):
    cout(i)
  poison(cout)

@process
def printer(cin):
  while True:
    print cin(),

A = Channel('A')
Parallel(
  counter(A.writer(), limit=10),
  printer(A.reader())
)

#@process
#def
