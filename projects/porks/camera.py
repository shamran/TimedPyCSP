""" Configurable. Eternal loop. Read data. Write data. """
from common import *
from random import expovariate

default_data = 0.1

def setup(data = default_data):
    import wx
    dlg = wx.TextEntryDialog(
        None, 'gennemsnittiden for kameraet?',
        'Configure Process', str(data))
    if dlg.ShowModal() == wx.ID_OK:
        try:
            data = eval(dlg.GetValue())
        except:
            data = dlg.GetValue()
    dlg.Destroy()
    return data

def cameraFunc(in0,out0 , data = default_data):
    print "camera time is %f"%data
    try: 
        while True:
            val0 = in0()
            waittime = expovariate(1/data)
            val0.wait.append(waittime)
            Wait(waittime)
            out0(val0)
    except ChannelPoisonException:
      poison(in0,out0)
