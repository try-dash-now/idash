__author__ = 'Sean Yu'
'''created @2015/12/4''' 


import os, sys,time
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
import ssh
import dut
class SSH(dut.dut):
    chan=None
    client=None

    def __init__(self, name, attr =None,logger=None, logpath= None, shareData=None):
        dut.dut.__init__(self, name,attr,logger, logpath, shareData)
        import re
        reSSHcmd1 = re.compile('ssh\s+([\w._-]+)@([\w._-]+)\s*:\s*(\d+)', re.I)
        reSSHcmd2 = re.compile('ssh\s+([\w._-]+)@([\w._-]+)', re.I)
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

    def ReadOutput(self):
        import time, os
        maxInterval = 60
        if self.timestampCmd ==None:
            self.timestampCmd= time.time()
        counter = 0
        while self.SessionAlive:
            self.lockStreamOut.acquire()
            try:
                if (time.time()-self.timestampCmd)>maxInterval:
                    self.write('\r\n')
                    self.timestampCmd = time.time()
                if self.client and self.chan:
                    out = self.chan.recv(64)
                    if len(out):
                        self.streamOut+=out
                    if self.logfile and len(out)!=0:
                        self.logfile.write(out)
                        self.logfile.flush()
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
            time.sleep(0.001)

    def login(self):
        self.loginDone=False
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
        self.timestampCmd= time.time()
        #super(SSH, self).write(data)
        if self.client:
            self.chan.send(data)
