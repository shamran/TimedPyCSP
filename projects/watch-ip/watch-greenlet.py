from pycsp.greenlets import *
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
        self.present_time = None

    def print_time(self):
        offset = time.time()-start_time
        print "time in watch is %02.0f:%02.0f:%02.0f (late by %f)"%(self.present_time.hour,self.present_time.minut, self.present_time.second, offset-self.present_time.internal_seconds)
    def set_time(self,timestamp):
        self.present_time = timestamp         
        self.offset =  time.time()-start_time-self.present_time.internal_seconds        





def dummywork(iterations):
    #Estimating Pi.
    temp = 0
    import time    
    for k in xrange(int(iterations)):
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
                time_spent -= time.time()
                b4 = time.time()
                dummywork(work)
                time_spent += time.time()
                #print "time in dummy : ",time.time()-b4
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
    #b4 = time.time()
    if n>0: time.sleep(n)
    #print "in sleep", time.time()-b4,"=",n

@process 
def watch_process(time_in_channel,ack_out_channel):
    watch = Watch()
    try:
        offsets = []
        while True:
            timestamp = time_in_channel()
            if time.time()-start_time < (timestamp.internal_seconds+1):
                watch.set_time()
                offsets.append(watch.offset)
                watch.print_time()
                #ack_out_channel(True)
    except ChannelPoisonException:
        print "mean: %0.3f"%scipy.mean(offsets) 
        #print "variance :", scipy.var(stc)
        print "std variance : %0.3f\n"%scipy.std(offsets)
        print "len of received timestamps; %0.3f"%len(offsets)

        poison(time_in_channel,ack_out_channel)    

@process
def set_time(_id,timeset, time_out_Channel, ack_in_channel):       
    sleeptime = (timeset.internal_seconds-(time.time()-start_time))
    sleep(sleeptime)
    realtime = time.time()-start_time
    #print "internal time :%0.0f , real time: %f, diff: %f slept for %f"%(timeset.internal_seconds,realtime,timeset.internal_seconds-realtime,sleeptime)

    sending_time = (timeset.internal_seconds-(time.time()-start_time)+1)
    
    if timeset.internal_seconds-time.time()+start_time+1 > 0 :
        Alternation([
            {(time_out_Channel,timeset):None},
            {Timeout(sending_time):None}
            ]).execute()   
    #ack = ack_in_channel()


@process
def close_watch(time_channel,dummy_channel,time):
    #set_prioritet
    sleep(time)
    poison(time_channel,dummy_channel)
    
time_channel = Channel()
ack_channel = Channel()
dummy_channel = Channel()
dummy_timer_channel = Channel()
time_steps = 100
start_time = time.time()
#try:
Parallel(
    watch_process(+time_channel,-ack_channel)
    ,[set_time(i,Time(i/(60*60),i/60,i%60),-time_channel,+ack_channel) for i in range(time_steps)]
    ,close_watch(+time_channel,+dummy_channel,time_steps)
    ,10*background_dummywork(dummy_channel,-dummy_timer_channel)
    )    
