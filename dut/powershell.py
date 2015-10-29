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
    timestampCmd =None
    def __init__(self,name,attr,logger, logpath):
        dut.__init__(self, name,attr,logger, logpath)

        exe_cmd=['cmd.exe']
        a  = ['C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe',
                 '/c',
                 'pwd']
        #self.fw= open(self.logfile.name,'wb')
        #self.fr= open(self.logfile.name, 'r')
        #mystdin = open(self.logfile.name+'.in','wb')
        self.shellsession = subprocess.Popen(args = exe_cmd ,shell =True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        import threading
        self.lockStreamOut =threading.Lock()
        self.streamOut=''
        th =threading.Thread(target=self.ReadOutput)
        th.start()
        self.debuglevel=0

    def ReadOutput(self):
        import time, os
        maxInterval = 60
        if self.timestampCmd ==None:
            self.timestampCmd= time.time()
        counter = 0
        while self.SessionAlive:
            self.lockStreamOut.acquire()
            try:
                #if not self.sock:
                #    self.relogin()
                if (time.time()-self.timestampCmd)>maxInterval:
                    self.write(os.linesep)
                    self.timestampCmd = time.time()
                if self.shellsession:
                    out = self.shellsession.stdout.readline()
                    if len(out):
                        self.streamOut+=out
                if self.logfile and len(out)!=0:
                    self.logfile.write(out)
                    self.logfile.flush()
                counter = 0
            except Exception, e:
                counter+=1
                if self.debuglevel:
                    print('\nReadOutput Exception %d:'%(counter)+e.__str__()+'\n')
                #self.lockStreamOut.release()

                print("ReadOutput Exception: %s"%(str(e)))
                import traceback
                msg = traceback.format_exc()
                print(msg)
                self.error(msg)
            self.lockStreamOut.release()

    def show(self):
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())
        if result!='':
            print('\t%s'%(result.replace('\n', '\n\t')))
        return result


    def send(self,cmd, Ctrl=False, noWait=False):
        import os
        tmp =[]
        stdin = self.shellsession.stdin

        if Ctrl:
            ascii = ord(cmd[0]) & 0x1f
            ch = chr(ascii)
            stdin.write(ch)

        else:
            stdin.write(cmd)

        if self.loginDone:
            if self.attribute.get("LINESEP"):
                LINESEP = self.attribute.get('LINESEP').replace('\\r', '\r').replace('\\n', '\n')
                stdin.write(LINESEP)
            else:
                stdin.write('\n')
        else:
            if self.attribute.get("LOGIN_LINESEP"):
                LINESEP = self.attribute.get('LOGIN_LINESEP').replace('\\r', '\r').replace('\\n', '\n')
                stdin.write(LINESEP)
            else:
                stdin.write('\r\n')

        if noWait:
            pass
        else:
            self.idxSearch =self.streamOut.__len__() #move the Search window to the end of streamOut



        #stdin.write('\r\n'+cmd+'\r\n')
        #stdin.flush()

    def xsingleStep(self, cmd, expect, wait, ctrl=False, noPatternFlag=False, noWait=False):
        exe_cmd='C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe %s'%cmd
        print exe_cmd
        #cmd ='ls'
        #self.shellsession = subprocess.Popen(args = exe_cmd ,shell =True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        a = self.shellsession.stdin
        #self.shellsession.stdin.newlines='\r\n'
        import sys
        #sys.stdout.write(cmd+'\n')
        #sys.stdout.flush()
        self.shellsession.stdin.write('\r\n'+cmd+'\r\n')
        self.shellsession.stdin.flush()
        print(self.streamOut)
        #out,error =self.shellsession.communicate(cmd+'\r\n')#wait











