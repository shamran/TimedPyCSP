""" Configurable. Run once then poison channels. """
from pycsp.greenlets import *
#from random import expovariate, uniform, seed
import random, sys, time , heapq, math, scipy


avg_convert_processing = 0.66
avg_camera_processing = 0.135
avg_analysis_processing = 0.45

cam_iter =   200000
conv_iter = 1000000
ana_iter =   700000
dummy_iter = 50000
std = 0.2
concurrent = 1.0
avg_arrival_interval = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)/concurrent

time_to_camera_deadline = (avg_camera_processing+avg_convert_processing)*1.3
time_to_deadline = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)*(1.22*concurrent)


pigs_to_simulate =  20
number_of_simulations = 5

class Pig:
  def __init__(self,_id, arrivaltime,ran,deadline = time_to_deadline):
    self.arrivaltime = arrivaltime
    self.deadline = arrivaltime+deadline
    self.id = _id,
    self.donetime = arrivaltime
    self.done = False
    x = ran.uniform(0,9)
    #print x
    #t =  raw_input("press")
    if x<1: self.normal = False 
    else : self.normal = True 
    self.wait = []
    self.accum = []
  def __repr__(self):
    sun = 0
    for x in self.wait : sun += x[1]
    return "%s\ttotal time inc queue : %0.3f, total processtime = %0.3f = %s"%(self.done,self.donetime-self.arrivaltime,sun, self.accum)

def dummywork(iterations):
    #Estimating Pi.
    temp = 0
    import time    
    for k in xrange(int(iterations)):
         temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
         k +=1

@process
def background_dummywork(dummy, time_out):
    @process
    def internal_dummy(_id,dummy_in, dummy_out,time_out,work = dummy_iter):
        try:
            time_spent=0
            n = 0
            if _id == 0: dummy_out(time_spent)
            while True:
                time_spent = dummy_in()
                n+=1
                #print "spending time in dummy"
                time_spent -= time.time()
                dummywork(work)
                time_spent += time.time()
                dummy_out(time_spent)
        except ChannelPoisonException:
            poison(dummy_in,dummy_out)
            if _id == 0: time_out(time_spent)

    dummyC = Channel()   
    Parallel(internal_dummy(0,+dummy,-dummyC,time_out),
      internal_dummy(1,+dummyC,-dummy,time_out))

@io
def sleep(n):
    import time
    if n>0: time.sleep(n)

@process
def feederFunc(robot, analysis, dummy,ran, data = avg_arrival_interval):
    #Insert work here
    NextpigArrival = time.time()+ran.gauss(data, data*std)
    ThispigArrival = time.time()
    for x in xrange(pigs_to_simulate):
        if x % 10 == 0 : print "\t\t",x
        pig = Pig(x,ThispigArrival,ran)
        robot(pig)
        if pig.arrivaltime+time_to_camera_deadline-time.time()>0:
            camchannel = Channel()
            conChannel = Channel()
            feederChannel = Channel()
            cam = cameraFunc(+feederChannel,-camchannel,ran)
            conv = convertFunc(+camchannel,-conChannel,ran)
            ana =  analysisFunc(+conChannel,analysis,ran)
            Spawn(cam,conv,ana)
            Alternation([
                {((-feederChannel),pig):None},
                {Timeout(NextpigArrival-time.time()):None}
                ]).execute()       
        #else: print "no slack !!"
        ThispigArrival = NextpigArrival
        NextpigArrival = ThispigArrival+ran.gauss(data, data*std)
        if ThispigArrival>time.time() : sleep(ThispigArrival-time.time())
    #sleep(time_to_deadline*1.2)       
    poison(robot)
    poison(dummy)
    
@process    
def cameraFunc(in0,out0,ran , data = avg_camera_processing):
            val0 = in0()
            if time.time() - val0.arrivaltime   < time_to_camera_deadline :
                #waittime = ran.gauss(data,data*std)
                #waits = "cam: ",waittime
                val0.accum.append(time.time()-val0.arrivaltime)
                #val0.wait.append(waits)
                dummywork(ran.gauss(cam_iter,cam_iter*std))
                out0(val0)
        
@process
def convertFunc(in0,out0,ran , data = avg_convert_processing):
    try:
            val0 = in0()
            if val0.deadline>time.time():    
                #waittime = None
                #waittime = ran.gauss(data,std*data)
                #waits = "con: ",waittime
                #val0.wait.append(waits)
                val0.accum.append(time.time()-val0.arrivaltime)
                dummywork(ran.gauss(conv_iter,conv_iter*std))
                out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0,ran , data = avg_analysis_processing):
    try:
            val0 = in0()
            if val0.deadline>time.time():
                #waittime = ran.gauss(data,std*data)                
                #waits = "ana: ",waittime
                val0.accum.append(time.time()-val0.arrivaltime)
                #val0.wait.append(waits)
                dummywork(ran.gauss(ana_iter,ana_iter*std))                
                out0(val0)
    except ChannelPoisonException:
        exit

@process        
def robotFunc(feeder,analysis,ran, statC, data = time_to_deadline):
    next_deadline = {}
    try:
        @choice
        def process_pig(channel_input):
            if channel_input.id not in next_deadline : next_deadline[channel_input.id] = channel_input

        @choice
        def process_pig2(channel_input):
            if channel_input.deadline>time.time():
                channel_input.done = True
            #else :  print "arrived late in robot"
            channel_input.accum.append(time.time()-channel_input.arrivaltime)
            channel_input.donetime = time.time()
            next_deadline[channel_input.id] = channel_input
            
        while True:
                alt = Alternation([
                {feeder :process_pig()},
                {analysis:process_pig2()}
                ]).execute()
    except ChannelPoisonException:
        good = 0
        bad = 0
        normal = 0
        for key, pig in  next_deadline.items():
            if pig.done : good +=1
            else : bad +=1
            if pig.normal : normal +=1
            #print pig
        #print "good = ",good,"bad =",bad, " = ",float(good)/(pigs_to_simulate)*100,"% (",normal,"/",pigs_to_simulate,") normal"
        statC(float(good)/(pigs_to_simulate))


@process
def Work(statC,timeC):
    start = time.time()
    for x in range(number_of_simulations):
        print x," / ", number_of_simulations
        ran = random.Random(x)
        
        robotC = Channel("robot")
        analysisC = Channel("analysis")
        dummyC = Channel("dummy")

        feed = feederFunc(-robotC,-analysisC, -dummyC, ran)
        rob = robotFunc(+robotC,+analysisC,ran,statC)

        Parallel(
            3*background_dummywork(dummyC,timeC),
            feed,
            rob            
        )          
    poison(statC, timeC)

@process
def Statistic(statC):
    stc = []
    try:
        while True:
            stce = statC()
            #print "pct good: ",stce
            stc.append(stce)
            
    except ChannelPoisonException:
        print "number pigs processed in time:"
        #print stc
        #print "mean:  ",sum(stc, 0.0) / len(stc)
        print "mean: %0.2f"%scipy.mean(stc)
        print "std variance : %0.2f\n"%scipy.std(stc)
        
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
        
        
processeschan = Channel()
timechan = Channel()
Parallel(
    Work(-processeschan,-timechan),
    Statistic(+processeschan),
    StatisticTime(+timechan)
)
print "cam deadline:\t%3f\ndeadline:\t%3f"%(time_to_camera_deadline,time_to_deadline)
print "avg procsessing time: ",avg_camera_processing+avg_convert_processing+avg_analysis_processing
print "Greenlets version"
