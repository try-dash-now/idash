__author__ = 'Sean Yu'
'''created @2015/7/2'''
import os,sys
pardir =os.path.dirname(os.path.realpath(__file__))
pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))
sys.path.append(os.path.sep.join([pardir,'test']))
print('\n'.join(sys.path))
from  Tkinter import Tk,Tcl
import os
class tcltk(Tkinter.Tk):
    def __init__(self):
        Tkinter.Tk.__init__(self, None, None, 'Tk', 0)
tcltk()
from dut import dut
a =dut('base', {}, logpath='./bin')
from winTelnet import winTelnet
try:
    wt = winTelnet('a',{'CMD':'telnet 127.0.0.1'}, logpath='./bin')
except:
    pass

from TclInter import TclInter
try:
    ti = TclInter('a',{}, logpath='./bin')
except:
    pass

from IxNetwork import IxNetwork
try:
    ix = IxNetwork('a',{}, logpath='./bin')
except:
    pass
from e7 import  e7
try:
    e7 = e7('a', {}, logpath='./bin')
except:
    pass


from powershell import powershell
try:
    ps = powershell('a', {}, logpath='./bin')
except:
    pass





