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
			sleep(1)
	except ChannelRetireException:
		retire(cin,din)
		print "0 : got retire propergating"
	except ChannelPoisonException:
		print "0 : got poison propergating"
		poison(cin,din)

@process
def Q(id,out,tmax):
	t = 0
	while t<tmax:
		try:
			out(t)
		except ChannelRetireException:
			print "%d : got retire"%id
			return
		except ChannelPoisonException:
			print "%d : got poison"%id
			return
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

