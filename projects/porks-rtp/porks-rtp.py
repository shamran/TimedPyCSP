""" Configurable. Run once then poison channels. """
from pycsp.deadline import *
#from random import expovariate, uniform, seed
import random 
import heapq

avg_arrival_interval = 1.1
avg_convert_processing = 0.5
avg_camera_processing = 0.5
avg_analysis_processing = 0.1
dummy_work = 0.05
std = 0.1
time_to_deadline = 2.5
time_to_camera_deadline = 0.1
pigs_to_simulate =  10
number_of_simulations = 1

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
            print "will do dummy_work : ",n
            dummywork(Now()+work)
    except ChannelPoisonException:
        print time_spent

@io
def sleep(n):
    import time
    if n>0: time.sleep(n)

@process
def feederFunc(feeder,robot,dummy, data = avg_arrival_interval):
    
    #Insert work here
    NextpigArrival = Now()+ran.gauss(data, data*std)
    ThispigArrival = Now()
    Set_deadline(NextpigArrival-Now())
    for x in xrange(pigs_to_simulate):
        try:
            #if x % 20 == 0 : print "doing ",x
            pig = Pig(x,ThispigArrival)
            Alternation([
                {(robot,pig) :"feeder(pig)"},
                {(feeder,pig):"robot(pig)"}
                ]).execute()
            Remove_deadline()
            ThispigArrival = NextpigArrival
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)
            Set_deadline(NextpigArrival-Now())
            if ThispigArrival>Now() : sleep(ThispigArrival-Now())
        except DeadlineException:
            Remove_deadline()
            NextpigArrival = NextpigArrival+ran.gauss(data, data*std)

    poison(feeder,dummy)
    
@process    
def cameraFunc(in0,out0 , data = avg_camera_processing):
    try: 
        while True:
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
    except ChannelPoisonException:
        poison(in0,out0)        
        
@process
def convertFunc(in0,out0 , data = avg_convert_processing):
    try:
        while True:
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
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0 , data = avg_analysis_processing):
    try:
        while True:
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
        poison(in0,out0)

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
        poison(feeder)
        poison(robot)
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

    robot = Channel("robot")       
    feeder = Channel("feeder")
    camera = Channel("camera")
    convert = Channel("convert")
    analysis = Channel("analysis")
    dummy = Channel("dummy")


    Parallel(
        feederFunc(-feeder,-robot, -dummy),
        cameraFunc(+feeder,-camera),
        convertFunc(+camera,-convert),
        analysisFunc(+convert,-analysis),
        robotFunc(+analysis,+robot),
        1*background_dummywork(+dummy)
    )        
#print "time to process: ", Now()-start,"sec"
