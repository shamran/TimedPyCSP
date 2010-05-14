""" Configurable. Run once then poison channels. """
from pycsp.deadline import *
#from random import expovariate, uniform, seed
import random, sys, time , heapq, math, scipy


avg_convert_processing = 0.66
avg_camera_processing = 0.135
avg_analysis_processing = 0.45

cam_iter =   200000
conv_iter = 1000000
ana_iter =   700000
dummy_iter = 100000
std = 0.04
concurrent = 2
avg_arrival_interval = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)*(0.99/concurrent)

time_to_camera_deadline = avg_camera_processing*1.6
time_to_deadline = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)*(1.22*concurrent)


pigs_to_simulate =  100
number_of_simulations = 10

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
         if k%120000 ==0 : Release()
         temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
         k +=1

@process
def background_dummywork(dummy_in, time_out,work = dummy_iter):
    try:
        time_spent=0
        n = 0
        while True:
            Alternation([{Timeout(seconds=0.005):None}, {dummy_in:None}]).select()    
            n+=1
            time_spent -= Now()
            dummywork(work)
            time_spent += Now()
            #print time_spent
    except ChannelPoisonException:
        time_out(time_spent)   

@io
def sleep(n):
    import time
    if n>0: time.sleep(n)

@process
def feederFunc(robot, analysis, dummy,ran, data = avg_arrival_interval):
       #Insert work here
    NextpigArrival = Now()+ran.gauss(data, data*std)
    ThispigArrival = Now()
    Set_deadline(NextpigArrival-Now())
    for x in xrange(pigs_to_simulate):
        try:
            if x % 10 == 0 : print "\t\t",x
            pig = Pig(x,ThispigArrival,ran)
            robot(pig)
            if pig.arrivaltime+time_to_camera_deadline-Now()>0:               
                camchannel = Channel()
                conChannel = Channel()
                feederChannel = Channel()
                cam = cameraFunc(+feederChannel,-camchannel,ran)
                conv = convertFunc(+camchannel,-conChannel,ran)
                ana =  analysisFunc(+conChannel,analysis,ran)
                Set_deadline((pig.arrivaltime+time_to_camera_deadline)-Now(),cam)
                Set_deadline((pig.arrivaltime+time_to_deadline)-Now(),conv)
                Set_deadline((pig.arrivaltime+time_to_deadline)-Now(),ana)
                Spawn(cam,conv,ana)
                (-feederChannel)(pig)
            #else: print "no slack !!"
            Remove_deadline()
            ThispigArrival = NextpigArrival
            NextpigArrival = ThispigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
            if ThispigArrival>Now() : sleep(ThispigArrival-Now())
        except DeadlineException:
            #print "failed in feeder"
            Remove_deadline()
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
    #sleep(time_to_camera_deadline*2)    
    poison(robot)
    poison(dummy)
    
@process    
def cameraFunc(in0,out0,ran , data = avg_camera_processing):
    try:
        val0 = in0()                
        if Now() - val0.arrivaltime   < time_to_camera_deadline :
            #waittime = ran.gauss(data,data*std)
            #waits = "cam: ",waittime
            val0.accum.append(Now()-val0.arrivaltime)
            #val0.wait.append(waits)
            dummywork(ran.gauss(cam_iter,cam_iter*std))
            out0(val0)
            Remove_deadline()
    except DeadlineException:
        Remove_deadline()
        poison(in0,out0)
        
@process
def convertFunc(in0,out0,ran , data = avg_convert_processing):
    try:
        val0 = in0() 
        if val0.deadline>Now():    
            Set_deadline(val0.deadline-Now())   
            #waittime = None
            #waittime = ran.gauss(data,std*data)                    
            #waits = "con: ",waittime
            #val0.wait.append(waits)
            val0.accum.append(Now()-val0.arrivaltime)
            dummywork(ran.gauss(conv_iter,conv_iter*std))
            out0(val0)
            Remove_deadline()
    except DeadlineException:
        Remove_deadline()
        poison(in0,out0)
    except ChannelPoisonException:
        Remove_deadline()   
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0,ran , data = avg_analysis_processing):
    try:
        val0 = in0()
        if val0.deadline>Now():
            Set_deadline(val0.deadline-Now())
            #waittime = ran.gauss(data,std*data)                    
            #waits = "ana: ",waittime
            val0.accum.append(Now()-val0.arrivaltime)
            #val0.wait.append(waits)
            dummywork(ran.gauss(ana_iter,ana_iter*std))                
            out0(val0)
            Remove_deadline()
    except DeadlineException:
        Remove_deadline()
    except ChannelPoisonException:
        Remove_deadline()

@process        
def robotFunc(feeder,analysis,ran, statC, data = time_to_deadline):
    next_deadline = {}
    try:
        @choice
        def process_pig(channel_input):
            if channel_input.id not in next_deadline : next_deadline[channel_input.id] = channel_input

        @choice
        def process_pig2(channel_input):
            if channel_input.deadline>Now():
                channel_input.done = True
            #else :  print "arrived late in robot"
            channel_input.accum.append(Now()-channel_input.arrivaltime)
            channel_input.donetime = Now()
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
    start = Now()
    for x in range(number_of_simulations):
        print x," / ", number_of_simulations
        ran = random.Random(x)

        robotC = Channel("robot")
        analysisC = Channel("analysis")
        dummyC = Channel("dummy")

        feed = feederFunc(-robotC,-analysisC, -dummyC, ran)
        rob = robotFunc(+robotC,+analysisC,ran,statC)

        try:
            Parallel(
            feed,
            rob,
            1*background_dummywork(+dummyC,timeC)
            )
        except DeadlineException:
            print  "fucking exception"       
    poison(statC, timeC)
    
@process
def Statistic(statC):
    stc = []
    try:
        while True:
            stce = statC()
            print stce
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
            stc.append(statC())
            
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
print "RTP version"
