from pycsp.simulation import *
from random import randint


def fifo_schedule(resource, jobs):
   cpu_offer, disk_offer = resource
   result=None
   for job in jobs:
      cpu_need, disk_need, net_need = job
      if cpu_need<=cpu_offer and disk_need<=disk_offer:
         result=job
         break
   if not jobs:
      #print Now(),'-1 : (10,0,0)'
      return (10,0,0)

   #print Now(),jobs.index(result), result
   jobs.remove(result)
    
   return result

def randrange(targetrange):
   x,y = targetrange
   return randint(x,y)

@process
def User(MiG, cpu_time, disk_use, net_use):
   for i in range(15):
       Wait(randrange((1,40)))
       request = (randrange(cpu_time), randrange(disk_use), randrange(net_use))
       MiG(request)
   retire(MiG)

@process
def Resource(MiG_in, MiG_out, max_cpu, max_disk):
    try:
        while True:
            MiG_out((max_cpu, max_disk))
            cpu, disk, net = MiG_in()
            Wait(cpu)
    except ChannelRetireException:
        pass

@choice
def NewJob(jobs, max_jobs, channel_input):
   jobs.append(channel_input)

@choice
def NewSlot(jobs, out, channel_input):
   out(schedule(channel_input, jobs))


@process
def Grid(user, resource_in, resource_out):
   mon = Monitor()
   jobs=[]
   max_jobs = 0
   interupt = 0
   try:
      while True:
        Alternation([{
            user: NewJob(jobs,max_jobs),
            resource_in: NewSlot(jobs, resource_out),
            }]).execute()
        mon.observe(len(jobs))
        if len(jobs)>max_jobs: 
            max_jobs = len(jobs)
            #print "incrementing max jobs to ",max_jobs
        interupt+=1
        if interupt%100==0:print Now(),": got ",interupt," interupts. "

   except ChannelRetireException:
       pass

   print Now(),': users have terminated and left', len(jobs), 'jobs in the queue'

   while jobs:
      offer=resource_in()
      resource_out(schedule(offer, jobs))
      mon.observe(len(jobs))
   mon.setHistogram(high=max_jobs,nbins=10)
   print mon.printHistogram()
   print "variance:",mon.var()
   print "timevariance: ", mon.timeVariance()
   print "mean: ",mon.mean()
   print "timeAverage: ", mon.timeAverage()
   
   
   plt = SimPlot()
   plt.plotHistogram(mon.histogram(high=max_jobs,nbins=10),xlab='length of queue',ylab='number of observation',
                     title="# jobs in queue",
                     color="red",width=1)
   plt.mainloop()
   plt.plotStep(mon,title="number in queue for resource")
   plt.mainloop()
    

   retire(resource_in)
      
schedule=fifo_schedule

job_channel = Channel()
slot_offer_channel = Channel()
slot_reply_channel = Channel()

resource_count=200
user_count=100

Parallel([Resource(+slot_reply_channel, -slot_offer_channel, max_cpu=100, max_disk=10) for i in range(resource_count)],
         Grid(+job_channel, +slot_offer_channel, -slot_reply_channel),
         [User(-job_channel, (10,100), (1,10), (1,5)) for i in range(user_count)],
         )

print 'Simulation ended at',Now()
