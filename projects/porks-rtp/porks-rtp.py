""" Configurable. Run once then poison channels. """
from pycsp.deadline import *
#from random import expovariate, uniform, seed
import random, sys
import heapq

avg_arrival_interval = 0.9

avg_convert_processing = 0.8
avg_camera_processing = 0.07
avg_analysis_processing = 0.8
std = 0.05

time_to_camera_deadline = 0.1
time_to_deadline = avg_camera_processing+avg_convert_processing+avg_analysis_processing-0.2
dummy_work = 0.05


pigs_to_simulate =  20
number_of_simulations = 3

class Pig:
  def __init__(self,_id, arrivaltime,deadline = time_to_deadline):
    self.arrivaltime = arrivaltime
    self.deadline = arrivaltime+deadline
    self.id = _id,
    self.donetime = arrivaltime
    self.done = False
    if ran.uniform(0,9)<1: self.normal = False 
    else : self.normal = True 
    self.wait = []
  def __repr__(self):
    return "%s\tHas normal ribs: %s, total processtime = %0.3f, totaltime = %0.3f\t%s\n"%(self.done,self.normal,sum(self.wait),self.donetime-self.arrivaltime,self.wait)

def dummywork(stop_time):
    #Estimating Pi.
    k = 0
    temp = 0
    while Now() < stop_time:
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
            dummywork(Now()+work)
    except ChannelPoisonException:
        print "time spent in dummy is ", time_spent

@io
def sleep(n):
    import time
    if n>0: time.sleep(n)

@process
def feederFunc(robot, analysis, dummy, data = avg_arrival_interval):
       #Insert work here
    NextpigArrival = Now()+ran.gauss(data, data*std)
    ThispigArrival = Now()
    Set_deadline(NextpigArrival-Now())
    for x in xrange(pigs_to_simulate):
        try:
            #if x % 20 == 0 : print "doing ",x
            pig = Pig(x,ThispigArrival)
            camchannel = Channel()
            conChannel = Channel()
            feederChannel = Channel()
            cam = cameraFunc(+feederChannel,-camchannel)
            conv = convertFunc(+camchannel,-conChannel)
            ana =  analysisFunc(+conChannel,analysis)
            Spawn(cam,conv,ana)
            Alternation([
                {(robot,pig) :"OUT(feederChannel)(pig)"},
                {(OUT(feederChannel),pig):"robot(pig)"}
                ]).execute()
            Remove_deadline()
            ThispigArrival = NextpigArrival
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
            if ThispigArrival>Now() : sleep(ThispigArrival-Now())
        except DeadlineException:
            Remove_deadline()
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
    poison(robot, dummy)
    
@process    
def cameraFunc(in0,out0 , data = avg_camera_processing):
            try:
                val0 = in0()                
                if Now() - val0.arrivaltime   < time_to_camera_deadline :
                    Set_deadline((val0.arrivaltime+time_to_camera_deadline)-Now())
                    waittime = ran.gauss(data,data*std)
                    val0.wait.append(waittime)
                    dummywork(waittime+Now())
                    out0(val0)
                    Remove_deadline()
            except DeadlineException:
                Remove_deadline()
                poison(in0,out0)
        
@process
def convertFunc(in0,out0 , data = avg_convert_processing):
    try:
            try:
                val0 = in0() 
                if val0.deadline>Now():    
                    Set_deadline(val0.deadline-Now())   
                    waittime = None
                    if val0.normal : waittime = ran.gauss(data,std*data)
                    else :   waittime = ran.gauss(2*data,std*data)
                    val0.wait.append(waittime)
                    dummywork(waittime+Now())
                    out0(val0)
                    Remove_deadline()
            except DeadlineException:
                Remove_deadline()
                poison(in0,out0)
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0 , data = avg_analysis_processing):
    try:
            try:
                val0 = in0()
                if val0.deadline>Now():
                    Set_deadline(val0.deadline-Now())
                    waittime = None
                    if val0.normal : waittime = ran.gauss(data,std*data)
                    else :   waittime = ran.gauss(2*data,data*std)
                    val0.wait.append(waittime)
                    dummywork(waittime+Now())
                    out0(val0)
                    Remove_deadline()
            except DeadlineException:
                Remove_deadline()
    except ChannelPoisonException:
        exit

@process        
def robotFunc(done,start, data = time_to_deadline):
    next_deadline = {}
    try:
        @choice
        def process_pig(channel_input):
            if channel_input.id not in next_deadline : next_deadline[channel_input.id] = channel_input

        @choice
        def process_pig2(channel_input):
            if channel_input.deadline>Now():
                channel_input.done = True
            channel_input.donetime = Now()
            next_deadline[channel_input.id] = channel_input
            
        while True:
            alt = Alternation([
                {start :process_pig()},
                {done:process_pig2()}
            ]).execute()
    except ChannelPoisonException:       
        good = 0
        bad = 0
        normal = 0
        for key, pig in  next_deadline.items():
            if pig.done : good +=1
            else : bad +=1
            if pig.normal : normal +=1
        print "good = ",good,"bad =",bad, " = ",float(good)/(pigs_to_simulate)*100,"% (",normal,"/",pigs_to_simulate,") normal"


start = Now()
for x in range(number_of_simulations):
    ran = random.Random(x)

    robotC = Channel("robot")       
    #feeder = Channel("feeder")
    #camera = Channel("camera")
    #convert = Channel("convert")
    analysisC = Channel("analysis")
    dummyC = Channel("dummy")

    
    rob = robotFunc(+robotC,+analysisC)

    #Set_priority(10,cam)
    #Set_priority(10,rob)

    Parallel(
        feederFunc(-robotC,-analysisC, -dummyC),
        rob,
        1*background_dummywork(+dummyC)
    )        
print "time to process: ", Now()-start,"sec"
