""" Configurable. Run once then poison channels. """
#from pycsp.processes import *
from pycsp.greenlets import *
#from random import expovariate, uniform, seed
import random
import heapq, time, math

avg_arrival_interval = 0.05
avg_convert_processing = 0.05
avg_camera_processing = 0.05
avg_analysis_processing = 0.05
time_to_deadline = 0.25
pigs_to_simulate =  20

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
    while time.time() < stop_time:
         temp += (math.pow(-1,k)*4) / (2.0*k+1.0)
         k +=1
@io
def sleep(n):
    time.sleep(n)

@process
def feederFunc(feeder,robot , data = avg_arrival_interval):
    print "feeder data = %f"%data
    #Insert work here
    for x in xrange(pigs_to_simulate):
        if x % 20 == 0 : print "doing ",x
        sleep(ran.expovariate(1/data))
        pig = Pig(x,time.time())
        Alternation([
            {(feeder,pig):"robot(pig)"},
            {(robot,pig) :"feeder(pig)"}
            ]).execute()        
    poison(feeder)
    
@process    
def cameraFunc(in0,out0 , data = avg_camera_processing):
    print "camera time is %f"%data
    try: 
        while True:
            val0 = in0()
            if val0.deadline>time.time():
                waittime = ran.expovariate(1/data)
                #print waittime
                val0.wait.append(waittime)
                dummywork(waittime+time.time())
                out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)
        
@process
def convertFunc(in0,out0 , data = avg_convert_processing):
    try:
        print "convert time %f"%data
        while True:
            val0 = in0()
            if val0.deadline>time.time():    
                waittime = None
                if val0.normal : waittime = ran.expovariate(1/data)
                else :   waittime = ran.expovariate(1/(2*data))
                val0.wait.append(waittime)
                dummywork(waittime+time.time())
                out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0 , data = avg_analysis_processing):
    try:
        print "analysis time %f"%data
        while True:
            val0 = in0()
            if val0.deadline>time.time():
                waittime = None
                if val0.normal : waittime = ran.expovariate(1/data)
                else :   waittime = ran.expovariate(1/(2*data))
                val0.wait.append(waittime)
                dummywork(waittime+time.time())
                out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)

 
@process        
def robotFunc(feeder,robot, data = time_to_deadline):
    next_deadline = {}
    try:
        @choice
        def process_pig(channel_input):
            next_deadline[channel_input.id] = channel_input

        @choice
        def process_pig2(channel_input):
            if channel_input.deadline>time.time():
                channel_input.done = True
            channel_input.donetime = time.time()
            next_deadline[channel_input.id] = channel_input
            
        while True:
                alt = Alternation([
                    {feeder:process_pig2()},
                    {robot :process_pig()}            
                ]).execute()
    except ChannelPoisonException:
        poison(feeder)
        poison(robot)
        good = 0
        bad = 0
        for key, pig in  next_deadline.items():
            if pig.done : good +=1
            else : bad +=1
        print "good = ",good,"bad =",bad, " = ",float(good)/(good+bad)*100,"%"

#seed(12)
ran = random.Random(12)

robot = Channel()       
feeder = Channel()
camera = Channel()
convert = Channel()
analysis = Channel()

start = time.time()
Parallel(
    feederFunc(-feeder,-robot),
    cameraFunc(+feeder,-camera),
    convertFunc(+camera,-convert),
    analysisFunc(+convert,-analysis),
    robotFunc(+analysis,+robot)
)        
 
print "time to process: ", time.time()-start,"sec"
