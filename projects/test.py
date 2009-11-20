from pycsp.greenlets import *



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

