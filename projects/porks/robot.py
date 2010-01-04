""" Configurable. Run once then poison channels. """
from common import *
from random import expovariate

default_data = 0.8

def setup(data = default_data):
    import wx
    dlg = wx.TextEntryDialog(
        None, 'maksimalt tid foer data skal naa robotten?',
        'Configure Process', str(data))
    if dlg.ShowModal() == wx.ID_OK:
        try:
            data = eval(dlg.GetValue())
        except:
            data = dlg.GetValue()
    dlg.Destroy()
    return data

def robotFunc(in0,out0 , data = default_data):

    #Insert work here
    try:
      print "max time is ",data
      while True:
        val0 = in0()
        proctime = Now()-val0.arrivaltime
        #print "in robot time is now ",Now(),val0,
        #print "processtime is ",proctime
        if proctime<=data : 
          out0("ok process time was: %f %s"%(proctime,val0.__repr__()))
        else : out0("fail process time was: %f %s"%(proctime,val0.__repr__()))
    except ChannelPoisonException:
        poison(in0)
        poison(out0)
