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
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

class powershell(dut):
    shellsession= None
    timestampCmd =None
    q_out = None
    q_err = None
    index_of_output=0
    index_of_error= 0
    def __init__(self,name,attr,logger, logpath, shareData):
        dut.__init__(self, name,attr,logger, logpath, shareData)

        exe_cmd=['cmd.exe']
        a  = ['C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe',
                 '/c',
                 'pwd']

        self.shellsession = subprocess.Popen(args = exe_cmd ,shell =True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.q_out = Queue()
        self.q_err = Queue()
        import threading
        self.lockStreamOut =threading.Lock()
        self.streamOut=''
        th =threading.Thread(target=self.ReadOutput)
        th.start()
        th2 =threading.Thread(target=self.fill_queue_of_stdout)
        th3 =threading.Thread(target=self.fill_queue_of_stderr)
        th2.start()
        th3.start()
        self.debuglevel=0

    def fill_queue_of_stdout(self):
        while self.SessionAlive:
            for line in iter(self.shellsession.stdout.readline, b''):
                self.q_out.put(line)
    def fill_queue_of_stderr(self):
        while self.SessionAlive:
            for line in iter(self.shellsession.stderr.readline, b''):
                self.q_err.put(line)
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
                    try:
                        err = self.q_err.get_nowait() # or q.get(timeout=.1)
                        #cur_index = self.index_of_error
                        #self.index_of_error= len(err)
                        #err = err[cur_index:]
                        if len(err):
                            self.streamOut+=err
                            self.logfile.write(err)
                            self.logfile.flush()
                    except Empty:
                        pass

                    try:
                        out = self.q_out.get_nowait() # or q.get(timeout=.1)
                        #cur_index = self.index_of_output
                        #self.index_of_output= len(out)
                        #out = out[cur_index:]

                        if len(out):
                            self.streamOut+=out
                            self.logfile.write(out)
                            self.logfile.flush()
                    except Empty:
                        pass



                counter = 0
            except Exception as e:
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
        newIndex = self.streamOut.rfind('\n')#self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate+1  :  newIndex]

        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())
        if result not in ['', '\n', '\r\n', '\r']:
            print('\t%s'%(result.replace('\r\n','\n').replace('\n', '\n\t')))
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
    def getCurrentTime(self,tmName='tm', format='%s:%s'):

        try:
            self.send('date /t')
            ymd = self.find('(\d{4}/\d{2}/\d{2})', 5)
        except:
            self.send('date /t')
            mdy = self.find('(\d{2})/(\d{2})/(\d{4})', 30)
            mdy = mdy.split('/')
            ymd = '%s/%s/%s'%(mdy[2], mdy[0],mdy[1])
        self.send('time /t')
        hm = self.find('(\d{2}:\d{2})', 30)
        self.setValue(str(tmName), format%(ymd,hm))
        print(self.getValue(tmName))












