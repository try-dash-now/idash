__author__ = 'Sean Yu'
'''created @2015/7/3'''
from  Tkinter import Tk,Tcl
from dut import dut
class TclInter(dut):
    tclInter=None
    def __init__(self, name,attrs,logger=None, logpath=None, shareData=None):
        dut.__init__(self, name, attrs, logger, logpath,shareData)
        import threading
        self.lockStreamOut =threading.Lock()
        self.streamOut=''
        th =threading.Thread(target=self.ReadOutput)
        #th.start()
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

    def __del__(self):
        try:
            if self.tclInter is not None:
                self.tclInter.eval('''
    rename  original_puts puts
    ''')
        except:
            pass

    def openTcl(self):
        if self.tclInter is not None:
            self.tclInter.quit()
        self.tclInter = Tcl( None, None, 'Tk', 0)
        self.tclInter.eval('''
rename puts original_puts
proc puts {args} {
    if {[llength $args] == 1} {
        return "=> [lindex $args 0]"
    } else {
        eval original_puts $args
    }
}
''')

    def send(self, command , Ctrl=False, Alt=False ):
        if self.tclInter is None:
            self.openTcl()
        command =command.strip()
        print('tcl command: %s'%command)
        self.output =self.tclInter.eval(command)

        output ="%s\n%s\n"%(command, self.output)
        self.streamOut+=output
        self.logfile.write(output)
        self.logfile.flush()
        print(output)
        self.idxSearch =self.streamOut.__len__() #move the Search window to the end of streamOut
        return  self.output
    def find(self,pattern, timeout =None, lags=0x18, noPattern=False): #(self, pattern, timeout = 1.0, ):
        import re
        p =re.compile(pattern, re.I|re.M)
        m =re.search(p, self.streamOut)
        if m:
            pass
        else:
            msg = 'not found pattern: %s'%pattern
            raise Exception(msg)


