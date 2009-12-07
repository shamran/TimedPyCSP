from pycsp.greenlets import *

@io
def sleep(n):
	import time
	time.sleep(n)

@process
def P(cin, din):
	try:
		while True:
			print "0 : im in alt"
			Alternation([{
				cin:'print "2 : cin %d"%__channel_input',
				din:'print "1 : din %d"%__channel_input'
												}]).execute()
			print "0 : leaving alt"
			#sleep(2)
	except ChannelRetireException:
		retire(cin,din)
		print "retire"
	except ChannelPoisonException:
		poison(cin,din)
		print "poison"

@process
def Q(id,out,tmax):
	t = 0
	while t<tmax:
		out(t)
		t+=1
	print "%d : poisons channel"%id
	poison(out)
	print "%d : done poison"%id


if __name__ == "__main__":
	print "main starting"

	c = Channel()
	d = Channel()

	Parallel(
		P(+d,+c),
		Q(1,-d,1),
		Q(2,-c,1)
	)

