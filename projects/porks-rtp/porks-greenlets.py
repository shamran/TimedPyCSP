""" Configurable. Run once then poison channels. """
#from pycsp.processes import *
from pycsp.greenlets import *
#from random import expovariate, uniform, seed
import random, sys, time , heapq, math


avg_convert_processing = 0.8
avg_camera_processing = 0.03
avg_analysis_processing = 0.8
std = 0.04

avg_arrival_interval = avg_camera_processing+avg_convert_processing+avg_analysis_processing-0.05

time_to_camera_deadline = avg_arrival_interval
time_to_deadline = avg_camera_processing+avg_convert_processing+avg_analysis_processing+0.3
dummy_work = 0.05


pigs_to_simulate =  10
number_of_simulations = 1

class Pig:
  def __init__(self,_id, arrivaltime,deadline = time_to_deadline):
    self.arrivaltime = arrivaltime
    self.deadline = arrivaltime+deadline
    self.id = _id,
    self.donetime = arrivaltime
    self.done = False
    x = ran.uniform(0,9)
    print x
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
    while time.time() < stop_time:
         temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
         k +=1

@process
def background_dummywork(dummy_in,work = dummy_work):
    try:
        time_spent=0
        n = 0
        while True:
            time_spent +=work
            Alternation([{Timeout(seconds=0.005):None}, {dummy_in:None}]).select()    
            n+=1
            #print "will do dummy_work : ",n
            #yt=input()
            dummywork(time.time()+work)
    except ChannelPoisonException:
        print "time spent in dummy is ", time_spent

@io
def sleep(n):
    if n>0: time.sleep(n)

@process
def feederFunc(robot, analysis, dummy, data = avg_arrival_interval):
    #Insert work here
    NextpigArrival = time.time()+ran.gauss(data, data*std)
    ThispigArrival = time.time()
    for x in xrange(pigs_to_simulate):
        #if x % 20 == 0 : print "doing ",x
        pig = Pig(x,ThispigArrival)
        robot(pig)
        if pig.arrivaltime+time_to_camera_deadline-time.time()>0:
            #print "slack: ",pig.arrivaltime+time_to_deadline-time.time()
            camchannel = Channel()
            conChannel = Channel()
            feederChannel = Channel()
            cam = cameraFunc(+feederChannel,-camchannel)
            conv = convertFunc(+camchannel,-conChannel)
            ana =  analysisFunc(+conChannel,analysis)
            Spawn(cam,conv,ana)
            Alternation([
                {(robot,pig) :"None"},
                {Timeout(NextpigArrival-time.time()):None}
                ]).execute()
            Alternation([
                {(OUT(feederChannel),pig):None},
                {Timeout(NextpigArrival-time.time()):None}
                ]).execute()       
            ThispigArrival = NextpigArrival
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            if ThispigArrival>time.time() : 
                sleep(ThispigArrival-time.time())
        else: print "no slack !!"
    poison(robot)
    #poison(dummy)
    
@process    
def cameraFunc(in0,out0 , data = avg_camera_processing):
            val0 = in0()
            if time.time() - val0.arrivaltime   < time_to_camera_deadline :
                waittime = ran.gauss(data,data*std)
                waits = "cam: ",waittime
                val0.accum.append(time.time()-val0.arrivaltime)
                val0.wait.append(waits)
                dummywork(waittime+time.time())
                out0(val0)
        
@process
def convertFunc(in0,out0 , data = avg_convert_processing):
    try:
            val0 = in0()
            if val0.deadline>time.time():    
                waittime = None
                waittime = ran.gauss(data,std*data)
                waits = "con: ",waittime
                val0.wait.append(waits)
                val0.accum.append(time.time()-val0.arrivaltime)
                dummywork(waittime+time.time())
                out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0 , data = avg_analysis_processing):
    try:
            val0 = in0()
            if val0.deadline>time.time():
                waittime = ran.gauss(data,std*data)                
                waits = "ana: ",waittime
                val0.accum.append(time.time()-val0.arrivaltime)
                val0.wait.append(waits)
                dummywork(waittime+time.time())
                out0(val0)
    except ChannelPoisonException:
        exit
 
@process        
def robotFunc(feeder,analysis, data = time_to_deadline):
    next_deadline = {}
    try:
        @choice
        def process_pig(channel_input):
            if channel_input.id not in next_deadline : next_deadline[channel_input.id] = channel_input

        @choice
        def process_pig2(channel_input):
            if channel_input.deadline>time.time():
                channel_input.done = True
            else :  print "arrived late in robot"
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
        print "cam deadline:\t%3f\ndeadline:\t%3f"%(time_to_camera_deadline,time_to_deadline)
        print "avg procsessing time: ",avg_camera_processing+avg_convert_processing+avg_analysis_processing
        for key, pig in  next_deadline.items():
            if pig.done : good +=1
            else : bad +=1
            if pig.normal : normal +=1
            print pig
        print "good = ",good,"bad =",bad, " = ",float(good)/(pigs_to_simulate)*100,"% (",normal,"/",pigs_to_simulate,") normal"


start = time.time()
for x in range(number_of_simulations):
    ran = random.Random(x)
    
    robotC = Channel("robot")       
    #feeder = Channel("feeder")
    #camera = Channel("camera")
    #convert = Channel("convert")
    analysisC = Channel("analysis")
    dummyC = Channel("dummy")

    
    feed = feederFunc(-robotC,-analysisC, -dummyC)
    rob = robotFunc(+robotC,+analysisC)

    #Set_priority(10,cam)
    #Set_priority(10,rob)

    Parallel(
        feed,
        rob#,
        #1*background_dummywork(+dummyC)
    )        
print "time to process: ", time.time()-start,"sec"
