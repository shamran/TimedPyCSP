""" Configurable. Run once then poison channels. """
from pycsp.deadline import *
from random import expovariate, uniform
import heapq

avg_arrival_interval = 0.1
avg_convert_processing = 0.1
avg_camera_processing = 0.1
avg_analysis_processing = 0.1
time_to_deadline = 1

class Pig:
  def __init__(self,_id,arrivaltime,deadline = time_to_deadline):
    self.arrivaltime = arrivaltime
    self.deadline = arrivaltime+deadline
    self.id = _id
    if uniform(0,9)<1: self.normal = False 
    else : self.normal = True 
    self.wait = []
  def __repr__(self):
    return "pig arrived at %f and process time is %s: [%s] total processtime is %0.3f"%(self.arrivaltime,self.normal,self.wait, sum(self.wait))

@process
def feederFunc(feeder,robot , data = avg_arrival_interval):
    print "feeder data = %f"%data
    #Insert work here
    for x in xrange(10):
        Wait(expovariate(1/data))
        pig = Pig(x,Now())
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
            try:
                val0 = in0()
                Set_deadline(val0.deadline-Now())
                waittime = expovariate(1/data)
                val0.wait.append(waittime)
                Wait(waittime)
                out0(val0)
                Remove_deadline()
            except DeadlineException:
                Remove_deadline()
    except ChannelPoisonException:
        poison(in0,out0)
        
        
@process
def convertFunc(in0,out0 , data = avg_convert_processing):
    try:
        print "convert time %f"%data
        while True:
            try:
                val0 = in0() 
                Set_deadline(val0.deadline-Now())   
                waittime = None
                if val0.normal : waittime = expovariate(1/data)
                else :   waittime = expovariate(1/(2*data))
                val0.wait.append(waittime)
                Wait(waittime)
                out0(val0)
                Remove_deadline()
            except DeadlineException:
                Remove_deadline()
    except ChannelPoisonException:
        poison(in0,out0)
             
@process
def analysisFunc(in0,out0 , data = avg_analysis_processing):
    try:
        print "analysis time %f"%data
        while True:
            try:
                val0 = in0()
                Set_deadline(val0.deadline-Now())
                waittime = None
                if val0.normal : waittime = expovariate(1/data)
                else :   waittime = expovariate(1/(2*data))
                val0.wait.append(waittime)
                Wait(waittime)
                out0(val0)
                Remove_deadline()
            except DeadlineException:
                Remove_deadline()
    except ChannelPoisonException:
        poison(in0,out0)

 
@process        
def robotFunc(feeder,robot, data = time_to_deadline):
    next_deadline = []
    try:
        def cancel(p):
            for i in xrange(len(next_deadline)):
                if next_deadline[i][1] == p:
                    next_deadline.pop(i)
                    break
            heapq.heapify(next_deadline)
           
        @choice
        def analysis_arived(channel_input):
            proctime = Now()-channel_input.arrivaltime
            if proctime<=data : 
                print "ok process time was: %f %s"%(proctime,channel_input.__repr__())
            else : print "fail process time was: %f %s"%(proctime,channel_input.__repr__())
            cancel(channel_input.id)                     

        @choice
        def start_timer(channel_input):
            heapq.heappush(next_deadline,(channel_input.deadline,channel_input))
            
        @choice
        def deadline_crossed(channel_input):
            print "deadline crossed, cutting pig: %s"%next_deadline.pop(0)[1]
       
        while True:
            while not next_deadline:
                alt = Alternation([
                    {feeder:analysis_arived()},
                    {robot :start_timer()}            
                ]).execute()
            if next_deadline :
                Set_deadline(next_deadline[0][0]-Now())
                Alternation([
                    {feeder:analysis_arived()},
                    {robot :start_timer()},
                    {Timeout(next_deadline[0][0]-Now()):deadline_crossed()}            
                ]).execute()
    except ChannelPoisonException:
        poison(feeder)
        poison(robot)       

robot = Channel()       
feeder = Channel()
camera = Channel()
convert = Channel()
analysis = Channel()


Parallel(
    feederFunc(-feeder,-robot),
    cameraFunc(+feeder,-camera),
    convertFunc(+camera,-convert),
    analysisFunc(+convert,-analysis),
    robotFunc(+analysis,+robot)
)        
