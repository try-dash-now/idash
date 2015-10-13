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
        th =threading.Thread(target=self.ReadDataFromSubProcess)
        th.start()
        self.write('\r\n')



    def write(self,data):
        resp  =self.shellsession.stdin.write(data)
        #resp = self.shellsession.communicate(data,timeout=0.1)
        self.shellsession.stdin.write(os.linesep)
        self.shellsession.stdin.flush()
        time.sleep(0.1)
    def show(self):
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())
        if result!='':
            print('\t%s'%(result.replace('\n', '\n\t')))
        return result
    def ReadDataFromSubProcess(self):
        import time, os
        maxInterval = 60
        if self.timestampCmd ==None:
            self.timestampCmd= time.time()
        import time
        counter = 0
        from os import read#O_NONBLOCK
        #os.O_APPEND
        #from fcntl import fcntl, F_GETFL, F_SETFL
        #flags = fcntl(self.shellsession.stdout, F_GETFL) # get current p.stdout flags
        #fcntl(self.shellsession.stdout, F_SETFL, flags | 0_NONBLOCK)
        while self.SessionAlive:
            self.lockStreamOut.acquire()
            try:
                #if not self.sock:
                #    self.relogin()
                if (time.time()-self.timestampCmd)>maxInterval:
                    self.write(os.linesep)
                    self.timestampCmd = time.time()

                #data = subprocess._eintr_retry_call(self.shellsession.stdout.read)
                data =self.shellsession.stdout.read(1)
                if self.logfile:
                    self.logfile.write(data)
                    self.logfile.flush()
                counter = 0
            except Exception, e:
                counter+=1
                if self.debuglevel:
                    print('\nReadDataFromSocket Exception %d:'%(counter)+e.__str__()+'\n')
                #self.lockStreamOut.release()
                if str(e)!='timed out':
                    if str(e) =='[Errno 10053] An established connection was aborted by the software in your host machine' or '[Errno 9] Bad file descriptor'==str(e):
                        #self.lockStreamOut.acquire()
                        try:
                            time.sleep(7)
                            if self.sock:
                                #self.write('quit\r\n')
                                self.sock.close()
                                self.sock = 0
                                self.eof = 1
                                self.iacseq = ''
                                self.sb = 0
                            self.open(self.host,self.port,self.timeout)
                        except Exception as e:
                            print('\nReadDataFromSocket Exception2 %d:'%(counter)+e.__str__()+'\n')
                            pass
                        #self.lockStreamOut.release()
                    else:
                        print("ReadDataFromSocket Exception: %s"%(str(e)))
                        import traceback
                        msg = traceback.format_exc()
                        print(msg)
                        self.error(msg)
            self.lockStreamOut.release()


