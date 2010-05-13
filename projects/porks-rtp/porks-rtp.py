""" Configurable. Run once then poison channels. """
from pycsp.deadline import *
#from random import expovariate, uniform, seed
import random, sys
import heapq
import scipy

mul = 0.5
avg_convert_processing = 0.8*mul
avg_camera_processing = 0.1*mul
avg_analysis_processing = 0.5*mul
std = 0.04

avg_arrival_interval = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)*0.99

time_to_camera_deadline = avg_camera_processing+max(avg_convert_processing,avg_analysis_processing)
time_to_deadline = (avg_camera_processing+avg_convert_processing+avg_analysis_processing)*1.3
dummy_work = 0.09


pigs_to_simulate =  100
number_of_simulations = 20

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

def dummywork(stop_time):
    #Estimating Pi.
    k = 0
    temp = 0
    import time    
    if stop_time>0: time.sleep(stop_time-Now())
    #while Now() < stop_time:
    #     temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
    #     k +=1

@process
def background_dummywork(dummy_in, time_out,work = dummy_work):
    try:
        time_spent=0
        n = 0
        while True:
            time_spent +=work
            Alternation([{Timeout(seconds=0.005):None}, {dummy_in:None}]).select()    
            n+=1
            #print "will do dummy_work : ",n
            #yt=input()
            dummywork(Now()+work)
    except ChannelPoisonException:
        #print "time spent in dummy is ", time_spent
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
            #if x % 20 == 0 : print "doing ",x
            pig = Pig(x,ThispigArrival,ran)
            robot(pig)
            if pig.arrivaltime+time_to_camera_deadline-Now()>0:
                #print "slack: ",pig.arrivaltime+time_to_deadline-Now()
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
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
            if ThispigArrival>Now() : sleep(ThispigArrival-Now())
        except DeadlineException:
            print "failed in feeder"
            Remove_deadline()
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
    poison(robot)
    poison(dummy)
    
@process    
def cameraFunc(in0,out0,ran , data = avg_camera_processing):
    try:
        val0 = in0()                
        if Now() - val0.arrivaltime   < time_to_camera_deadline :
            waittime = ran.gauss(data,data*std)
            waits = "cam: ",waittime
            val0.accum.append(Now()-val0.arrivaltime)
            val0.wait.append(waits)
            dummywork(waittime+Now())
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
            waittime = None
            waittime = ran.gauss(data,std*data)                    
            waits = "con: ",waittime
            val0.wait.append(waits)
            val0.accum.append(Now()-val0.arrivaltime)
            dummywork(waittime+Now())
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
            waittime = ran.gauss(data,std*data)                    
            waits = "ana: ",waittime
            val0.accum.append(Now()-val0.arrivaltime)
            val0.wait.append(waits)
            dummywork(waittime+Now())
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

print "cam deadline:\t%3f\ndeadline:\t%3f"%(time_to_camera_deadline,time_to_deadline)
print "avg procsessing time: ",avg_camera_processing+avg_convert_processing+avg_analysis_processing

@process
def Work(statC,timeC):
    start = Now()
    for x in range(number_of_simulations):
        ran = random.Random(x)

        robotC = Channel("robot")
        analysisC = Channel("analysis")
        dummyC = Channel("dummy")

        feed = feederFunc(-robotC,-analysisC, -dummyC, ran)
        rob = robotFunc(+robotC,+analysisC,ran,statC)

        #Set_priority(10,feed)
        #Set_priority(10,rob)

        try:
            Parallel(
            feed,
            rob#,
            #1*background_dummywork(+dummyC,timeC)
            )
        except DeadlineException:
            print  "fucking exception"       
    #print "time to process: ", Now()-start,"sec"
    poison(statC, timeC)
    
@process
def Statistic(statC):
    stc = []
    try:
        while True:
            stc.append(statC())
            
    except ChannelPoisonException:
        print "number pigs processed in time:"
        #print stc
        #print "mean:  ",sum(stc, 0.0) / len(stc)
        print "mean: %0.3f"%scipy.mean(stc) 
        print "std variance : %0.3f\n"%scipy.std(stc)
        
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
