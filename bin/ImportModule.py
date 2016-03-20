__author__ = 'Sean Yu'
'''created @2015/7/2'''
import os,sys
pardir =os.path.dirname(os.path.realpath(__file__))
pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))
sys.path.append(os.path.sep.join([pardir,'test']))
sys.path.append(os.path.sep.join([pardir,'dut']))
print('\n'.join(sys.path))

from  Tkinter import Tk,Tcl
import os
import colorama
colorama.init()
class tcltk(Tk):
    def __init__(self):
        Tk.__init__(self, None, None, 'Tk', 0)
tcltk()
from dut import dut

from winTelnet import winTelnet
logpath= '../../log'
a =dut('base', {}, logpath=logpath)
try:
    wt = winTelnet('a',{'CMD':'telnet 127.0.0.1'}, logpath=logpath)
except:
    pass

from TclInter import TclInter
try:
    ti = TclInter('a',{}, logpath=logpath)
    ti.closeSession()
except:
    pass

from IxNetwork import IxNetwork
try:
    ix = IxNetwork('a',{}, logpath=logpath)
    ix.closeSession()
except:
    pass
try:
    import  ssh
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.WarningPolicy())
    client.load_system_host_keys()
    #client.connect('localhost',22, 'user', '1234')
    chan = client.invoke_shell()

except:
    pass
from powershell import powershell
try:
    ps = powershell('a', {}, logpath=logpath)
    ps.SessionAlive=False
except:
    ps.SessionAlive=False
    pass

from SSH import SSH
try:
    ps = SSH('a', {}, logpath=logpath)
    ps.SessionAlive=False
except:
    ps.SessionAlive=False
    pass
