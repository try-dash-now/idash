__author__ = 'Sean Yu'
'''created @2015/10/12''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))
from dut import dut
import time
import subprocess
class powershell(dut):
    shellsession= None
    def __init__(self,name,attr,logger, logpath):
        dut.__init__(self, name,attr,logger, logpath)

        exe_cmd='C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe'
        self.shellsession = subprocess.Popen(args = exe_cmd ,shell =True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        import threading
        self.lockStreamOut =threading.Lock()
        self.streamOut=''


    def show(self):
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())
        if result!='':
            print('\t%s'%(result.replace('\n', '\n\t')))
        return result

    def singleStep(self, cmd, expect, wait, ctrl=False, noPatternFlag=False, noWait=False):
        exe_cmd='C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe %s'%cmd
        self.shellsession = subprocess.Popen(args = exe_cmd ,shell =True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out,error =self.shellsession.communicate(wait)
        print out
        print error
        self.logfile.write(out+'\n')
        self.logfile.write(error+'\n')
        self.logfile.flush()
        self.lockStreamOut.acquire()
        self.streamOut+=out+'\n'+error+'\n'
        self.lockStreamOut.release()
        self.find(expect,1,noPattern=noPatternFlag)






