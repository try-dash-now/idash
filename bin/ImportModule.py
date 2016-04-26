__author__ = 'Sean Yu'
'''created @2015/7/2'''
import os,sys
pardir =os.path.dirname(os.path.realpath(__file__))
pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))
sys.path.append(os.path.sep.join([pardir,'test']))
sys.path.append(os.path.sep.join([pardir,'dut']))
sys.path.append(os.path.sep.join([pardir,'install']))
print('\n'.join(sys.path))

from  Tkinter import Tk,Tcl
import abc
import UserDict
import _abcoll
import traceback
import colorama
colorama.init()
from case import case
logpath= '../../log'
try:
    cs = case('case', log_folder = logpath)
except Exception as e:
    pass
from webgui import webgui
try:
    ps = webgui('a', {}, logpath=logpath)
    ps.SessionAlive=False
except Exception as e:
    print(traceback.format_exc())
    ps.SessionAlive=False
class tcltk(Tk):
    def __init__(self):
        Tk.__init__(self, None, None, 'Tk', 0)
tcltk()
from dut import dut

from winTelnet import winTelnet

a =dut('base', {}, logpath=logpath)
try:
    wt = winTelnet('a',{'CMD':'telnet 127.0.0.1'}, logpath=logpath)
except Exception as e:
    print(traceback.format_exc())

from TclInter import TclInter
try:
    ti = TclInter('a',{}, logpath=logpath)
    ti.closeSession()
except Exception as e:
    print(traceback.format_exc())

from IxNetwork import IxNetwork
try:
    ix = IxNetwork('a',{}, logpath=logpath)
    ix.closeSession()
except Exception as e:
    print(traceback.format_exc())

try:
    import  ssh
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.WarningPolicy())
    client.load_system_host_keys()
    #client.connect('localhost',22, 'user', '1234')
    chan = client.invoke_shell()

except Exception as e:
    print(traceback.format_exc())
from powershell import powershell
try:
    ps = powershell('a', {}, logpath=logpath)
    ps.SessionAlive=False
except Exception as e:
    print(traceback.format_exc())
    ps.SessionAlive=False


from SSH import SSH
try:
    ps = SSH('a', {}, logpath=logpath)
    ps.SessionAlive=False
except Exception as e:
    ps.SessionAlive=False
    print(traceback.format_exc())



os._exit(0)






