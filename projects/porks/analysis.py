""" Configurable. Run once then poison channels. """
from common import *
from random import expovariate

default_data = 0.1

def setup(data = default_data):
    import wx
    dlg = wx.TextEntryDialog(
        None, 'Data value?',
        'Configure Process', str(data))
    if dlg.ShowModal() == wx.ID_OK:
        try:
            data = eval(dlg.GetValue())
        except:
            data = dlg.GetValue()
    dlg.Destroy()
    return data

def analysisFunc(in0,out0 , data = default_data):
    try:
        print "analysis time %f"%data
        while True:
            val0 = in0()
            waittime = None
            if val0.normal : waittime = expovariate(1/data)
            else :   waittime = expovariate(1/(2*data))
            val0.wait.append(waittime)
            Wait(waittime)
            out0(val0)
    except ChannelPoisonException:
        poison(in0,out0)
