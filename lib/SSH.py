__author__ = 'Sean Yu'
'''created @2015/12/4''' 


import os, sys,time , traceback
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
import ssh
from dut import dut
class SSH(dut):
    chan=None
    client=None

    def __init__(self, name, attr =None,logger=None, logpath= None, shareData=None):
        try:
            dut.__init__(self, name,attr,logger, logpath, shareData)
            import re
            reSSHcmd1 = re.compile('ssh\s+([\w._-]+)@([\w._-]+)\s*:\s*(\d+)', re.I)
            reSSHcmd2 = re.compile('ssh\s+([\w._-]+)@([\w._-]+)', re.I)
            if not self.attribute.has_key('CMD'):
                self.attribute['CMD']='ssh user@localhost'
                self.attribute['PASSWORD']='PWD'
            m1 = re.match(reSSHcmd1, self.attribute['CMD'])
            m2 = re.match(reSSHcmd2, self.attribute['CMD'])
            if m1:
                self.attribute['USER'] = m1.group(1)
                self.attribute['HOST'] = m1.group(2)
                self.attribute['PORT'] = int(m1.groups(3))
            elif m2:
                self.attribute['USER'] = m2.group(1)
                self.attribute['HOST'] = m2.group(2)
                self.attribute['PORT'] = 22
            #self.login()
            import threading
            self.lockStreamOut =threading.Lock()
            self.streamOut=''
            th =threading.Thread(target=self.ReadOutput)
            th.start()
            self.debuglevel=0

            self.login()
        except Exception as e:
            self.closeSession()
            raise e

    def ReadOutput(self):
        maxInterval = 60
        if self.timestampCmd ==None:
            self.timestampCmd= time.time()
        fail_counter = 0
        while self.SessionAlive:
            self.lockStreamOut.acquire()
            try:
                #self.info('time in ReadOutput',time.time(), 'timestampCmd', self.timestampCmd, 'max interval', maxInterval, 'delta',  time.time()-self.timestampCmd)
                if (time.time()-self.timestampCmd)>maxInterval:
                    self.write('\r\n')
                    self.timestampCmd = time.time()
                    self.info('anti-idle', fail_counter)
                if self.client and self.chan:
                    out = self.chan.recv(64)
                    if len(out):
                        self.streamOut+=out
                    if self.logfile and len(out)!=0:
                        self.logfile.write(out)
                        self.logfile.flush()
                fail_counter = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                fail_counter+=1
                if self.debuglevel:
                    print('\nReadOutput Exception %d:'%(fail_counter)+e.__str__()+'\n')
                #self.lockStreamOut.release()
                if self.autoReloginFlag and self.max_output_time_out< fail_counter:
                    import threading
                    fail_counter = 0
                    th =threading.Thread(target=self.relogin)
                    th.start()
                print("ReadOutput Exception: %s"%(str(e)))

                msg = traceback.format_exc()
                print(msg)
                self.error(msg)
            self.lockStreamOut.release()
            time.sleep(0.001)
        self.closeSession()

    def login(self):
        #self.loginDone=False
        if self.client:
                self.client.close()
                self.chan=None
                self.client=None
        self.client = ssh.SSHClient()
        ssh.util.log_to_file(self.logfile.name+'.ssh')
        self.client.set_missing_host_key_policy(ssh.WarningPolicy())
        self.client.load_system_host_keys()
        self.client.connect(self.attribute['HOST'], self.attribute['PORT'], self.attribute['USER'], self.attribute['PASSWORD'])
        self.chan = self.client.invoke_shell()
        self.loginDone=True
    def relogin(self):
        self.lockRelogin.acquire()
        try:
            if self.counterRelogin>0:
                self.lockRelogin.release()
                return
            self.counterRelogin+=1
            self.loginDone=False
            self.login()
            self.counterRelogin-=1
            self.loginDone=True
        except Exception as e:
            self.counterRelogin-=1
            self.lockRelogin.release()
            raise  e
        self.lockRelogin.release()

    def write(self, data):
        self.timestampCmd= time.time()        #super(SSH, self).write(data)
        if self.chan :
            if self.dry_run:
                self.chan.send('')
            else:
                self.chan.send(data)
