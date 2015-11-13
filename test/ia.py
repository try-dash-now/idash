__author__ = 'Sean Yu'
'''created @2015/11/13'''
import os, sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
from cmd import Cmd
import sys,time
import traceback
from runner import *
class ia(Cmd, object):
    sut=None
    sutname='tc'
    tabend = 'disable'
    def __init__(self):
        Cmd.__init__(self, 'tab', sys.stdin, sys.stdout)
        logpath = './log'
        logpath =   createLogDir('ia',logpath)
        ialogger = createLogger('ia',logpath)
        benchfile = './bench.csv'
        from common import bench2dict
        bench =bench2dict(benchfile)

        dutname = ['N5', 'ix-syu']
        errormessage = ''
        duts= initDUT(errormessage,bench, dutname,ialogger, logpath)
        self.sut=duts
        import threading
        th = threading.Thread(target=self.show)
        th.start()
    def do_setsut(self,sutname='tc'):
        if sutname =='':
            sutname='tc'
        if self.sut.get(sutname) or sutname =='tc' or sutname =='__case__':
            self.sutname=sutname
            self.prompt= '%s(%s)>>>'%(os.linesep, self.sutname)
            return 'current SUT: %s'%(self.sutname)
        else:
            return 'sutsut(\'%s\') is not defined'%sutname
    def postcmd(self,stop, line):
        if stop!=None and len(str(stop))!=0:
            out = self.sut[self.sutname].show()+'\n'+self.prompt+str(stop)+self.prompt
            #print(self.InteractionOutput,end='')

        stop = False
        return stop


    def completedefault(self, *ignored):
        #print(ignored)

        if self.sutname!='tc':
            #
            self.onecmd(ignored[1]+'\t')
            #i.cmdqueue=[]
            #pass
            #self.RunCmd(ignored[1]+'\t')
        return []#Cmd.completedefault(self ,ignored)


    def precmd(self,line):
        #print('line:',line)
        #linetemp = line.strip()
        temp =line.strip().lstrip()

        if self.sutname!='tc':
            if line==' ':
                self.RunCmd(line)
            elif temp=='':
                self.RunCmd(line)
            elif temp.lower()=='help' or temp=='?':
                self.RunCmd(line)
                line= ''
        #print(self.InteractionOutput,end='')
        return line
    def default(self,line):
        try:
            if line[-1]=='\t':
                print("@"*80)
            if self.sutname!='tc':
                if self.tabend!='disable':
                    line+='\t'

                self.RunCmd(line)

        except Exception as e:
            msg = traceback.format_exc()
            print(msg)
    def RunCmd(self, cmd):
        try:

            self.sut[self.sutname].send(cmd)

        except Exception as e:
            print(e)
    def show(self):
        while True:
            if self.sutname!='tc':
                self.sut[self.sutname].show()
            time.sleep(0.1)

i=ia()
print('#'*80)


while True:
    try:
        i.cmdloop()
        time.sleep(.1)
    except Exception as e:
        msg = traceback.format_exc()
        print(msg)
