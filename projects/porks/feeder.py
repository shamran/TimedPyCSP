""" Configurable. Run once then poison channels. """
from common import *
from random import expovariate, uniform

default_data = 0.1
class Pig:
  def __init__(self,arrivaltime,):
    self.arrivaltime = arrivaltime
    
    if uniform(0,9)<1: self.normal = False 
    else : self.normal = True 
    self.wait = []
  def __repr__(self):
    return "pig arrived at %f and process time is %s [%s] total processtime is %f"%(self.arrivaltime,self.normal,self.wait, sum(self.wait))

def setup(data = default_data):
    import wx
    dlg = wx.TextEntryDialog(
        None, 'gennemsnitstiden mellem grisene',
        'Configure Process', str(data))
    if dlg.ShowModal() == wx.ID_OK:
        try:
            data = eval(dlg.GetValue())
        except:
            data = dlg.GetValue()
    dlg.Destroy()
    return data

def feederFunc(out0 , data = default_data):
    print "feeder data = %f"%data
    #Insert work here
    for x in xrange(10):
        Wait(expovariate(1/data))
        pig = Pig(Now())
        out0(pig)

    poison(out0)
