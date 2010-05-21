from pycsp.deadline import *
#from random import expovariate, uniform, seed
import random, sys, time , heapq, math, scipy


class Time:
    def __init__(self,hour, minut,second):
        self.hour = hour
        self.minut = minut
        self.second = second
        self.internal_seconds = ((hour*60+minut)*60+second)
        #print self.internal_seconds
    def __str__(self):return "%02.0f:%02.0f:%02.0f"%(self.hour,self.minut, self.second)

class Watch:
    def __init__(self):
        self.time = None

    def print_time(self):
        offset = Now()-start_time
        print "time in watch is %02.0f:%02.0f:%02.0f (real time spent %f = diff %f)"%(self.time.hour,self.time.minut, self.time.second, offset, offset-self.time.internal_seconds)

    def set_time(self,time):
        self.time = time
        self.offset =  Now()-start_time-self.time.internal_seconds        
        
def dummywork(iterations):
    #Estimating Pi.
    temp = 0
    import time    
    for k in xrange(int(iterations)):
         #if k%120000 ==0 : Release()
         temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
         k +=1

@process
def StatisticTime(statC):
    stc = []
    try:
        while True:
            stac = statC()
            #print "time spent: ",stac
            stc.append(stac)
            
    except ChannelPoisonException:
        print "Time spent in dummy:"        
        #print stc
        #print "mean:  ",sum(stc, 0.0) / len(stc)
        print "mean: %0.3f"%scipy.mean(stc) 
        #print "variance :", scipy.var(stc)
        print "std variance : %0.3f\n"%scipy.std(stc)


@process
def background_dummywork(dummy, time_out):
    @process
    def internal_dummy(_id,dummy_in, dummy_out,time_out,work = 50000):
        try:
            time_spent=0
            n = 0
            if _id == 0: dummy_out(time_spent)
            while True:
                time_spent = dummy_in()
                n+=1
                time_spent -= Now()
                b4 = Now()
                dummywork(work)
                time_spent += Now()
                #print "time in dummy : ",Now()-b4
                dummy_out(time_spent)
        except ChannelPoisonException:
            poison(dummy_in,dummy_out)
            if _id == 0: 
                print time_spent

    dummyC = Channel()
    Parallel(
        internal_dummy(0,+dummy,-dummyC,time_out),
        internal_dummy(1,+dummyC,-dummy,time_out))

@io
def sleep(n):
    import time
    if n>0: time.sleep(n)


@process 
def watch_process(time_in_channel,ack_out_channel):
    watch = Watch()
    try:
        offsets = []
        while True:
            watch.set_time(time_in_channel())
            offsets.append(watch.offset)
            watch.print_time()
            ack_out_channel(True)
    except ChannelPoisonException:
        print "mean: %0.3f"%scipy.mean(offsets) 
        #print "variance :", scipy.var(stc)
        print "std variance : %0.3f\n"%scipy.std(offsets)

        poison(time_in_channel,ack_out_channel)    

@process
def set_time(_id,time, time_out_Channel, ack_in_channel):
    try:
        Set_deadline(time.internal_seconds+1)
        Wait(time.internal_seconds)
        time_out_Channel(time)
        ack = ack_in_channel()
    except DeadlineException:
        print "skipped one update"

@process
def close_watch(time_channel,dummy_channel,time):
    #prioritet
    Wait(time)
    poison(time_channel,dummy_channel)
    
time_channel = Channel()
ack_channel = Channel()
dummy_channel = Channel()
dummy_timer_channel = Channel()
time_steps = 30

start_time = Now()

Parallel(
    watch_process(+time_channel,-ack_channel)
    ,[set_time(i,Time(i/(60*60),i/60,i%60),-time_channel,+ack_channel) for i in range(time_steps)]
    ,close_watch(+time_channel,+dummy_channel,time_steps)
    ,14*background_dummywork(dummy_channel,-dummy_timer_channel)
    )    

