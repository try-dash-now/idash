#! /usr/bin/env python
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
import re
class ia(Cmd, object):
    tmCreated=None
    record= None
    cp = 0
    sut=None
    sutname=None
    tabend = None #'disable'
    tcName = None
    flagEndCase = False
    quoting = '"'
    def __init__(self, benchfile, dutname):
        import datetime
        self.tmCreated = datetime.datetime.now()
        Cmd.__init__(self, 'tab', sys.stdin, sys.stdout)
        self.tcName = 'tc'
        self.sutname='tc'
        self.tabend = 'disable'
        self.record =[['#var'], ['#setup']]

        logpath = './log'
        logpath =   createLogDir('ia',logpath)
        self.logger = createLogger('ia',logpath)
        #benchfile = './bench.csv'
        from common import bench2dict
        bench =bench2dict(benchfile)

        #dutname = ['N6', 'ix-syu']
        errormessage = ''
        duts= initDUT(errormessage,bench, dutname,self.logger , logpath)
        self.sut=duts
        import threading
        th = threading.Thread(target=self.show)
        th.start()
        self.do_setsut(dutname[0])
        self.helpDoc={}
        self.cmdbank=[]
        for sut in self.sut.keys():
            self.CreateDoc4Sut(sut)


    def CreateDoc4Sut(self, sutname=None):
        if not sutname:
            self.sutname =sutname
        if  self.helpDoc.has_key(self.sutname):
            return
        members =dir(self.sut[self.sutname])

        self.helpDoc.update({self.sutname:{}})
        for m in sorted(members):
            if m.startswith('__'):
                pass
            else:
                import inspect
                try:
                    try:
                        fundef = inspect.getsource(eval('self.sut[self.sutname].%s'%m)) # recreate function define for binary distribute
                        fundefstr = fundef[:fundef.find(':')]
                    except Exception as e:
                        (args, varargs, keywords, defaults) =inspect.getargspec(eval('self.sut[self.sutname].%s'%m))
                        argstring = ''
                        largs=len(args)
                        ldefaults= len(defaults)
                        gaplen = largs-ldefaults
                        index =0

                        for  arg in args:
                            if index <gaplen:
                                argstring+='%s, '%arg
                            else:
                                defvalue = defaults[index-gaplen]
                                if type('')==type(defvalue):
                                    defvalue = '"%s"'%defvalue
                                argstring+='%s = %s, '%(arg,str(defvalue))
                            index+=1


                        fundefstr ='%s( %s )'%(m, argstring)
                        fundef =fundefstr
                    listoffun =fundef.split('\n')
                    ret = eval('self.sut[self.sutname].%s.__doc__'%m)
                    if ret:
                        fundefstr = fundefstr +'\n\t'+'\n\t'.join(ret.split('\n'))
                    self.helpDoc[self.sutname].update({m: fundefstr})
                except Exception as e:
                    pass
    def doc(self, functionName=None):
        print('SUT:%s\n'%self.sutname)

        if self.sutname not in ['tc' , '__case__']:
            self.CreateDoc4Sut(self.sutname)
            for fun in sorted(self.helpDoc[self.sutname].keys()):
                if functionName:
                    lowerFunName = fun.lower()
                    if lowerFunName.find(functionName.lower())!=-1:
                        print(fun)
                        print('\t'+self.helpDoc[self.sutname][fun])
                else:
                    print(fun)
                    print('\t'+self.helpDoc[self.sutname][fun])
    def do_setsut(self,sutname='tc'):
        if sutname =='':
            sutname='tc'
        if self.sut.get(sutname) or sutname =='tc' or sutname =='__case__':
            self.sutname=sutname
            self.prompt= '%s(%s)###'%(os.linesep, self.sutname)
            return 'current SUT: %s'%(self.sutname)
        else:
            return 'sutsut(\'%s\') is not defined'%sutname
    def postcmd(self,stop, line):
        if stop!=None and len(str(stop))!=0:
            out = self.sut[self.sutname].show()+'\n'+self.prompt+str(stop)+self.prompt
            #print(self.InteractionOutput,end='')
        stop = False
        if self.flagEndCase:
            stop =True
        return stop
    def sut_complete(self, text):
        sutresponse=None
        if self.sutname!='tc':
            sut = self.sut[self.sutname]
            sutresponse = sut.write(str(text)+'\t')
            sut.timestampCmd=time.time()
            time.sleep(1)
            try:
                sutresponse = sut.find('%s\S+\s'%text, 1)
            except:
                sutresponse=None
        return sutresponse

    def completenames(self, text, *ignored):
        #print('hello')
        dotext = 'do_'+ text
        resp = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        sutresp = self.sut_complete(text)
        if sutresp:
            resp.append(sutresp)
        return resp


    def completedefault(self, *ignored):
        #print(ignored)
        #print('complete default')
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
        #line='\t'
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
    def IARunCmd(self,data):
        import shlex
        lex = shlex.shlex(data)
        lex.quotes = '"'
        lex.whitespace_split = True
        cmd=list(lex)
        reQuoting=re.compile('\s*"(.*)"', re.DOTALL)
        for i in range(0, len(cmd)):
            m = re.match(reQuoting, cmd[i] )
            if m:
                cmd[i]=m.group(1)
        funname = cmd[0]
        i_arg = cmd[1:]
        fun = self.__getattribute__(funname)
        import inspect
        (def_args, def_varargs, def_keywords, def_defaults) =inspect.getargspec(fun)

        def_args=def_args[1:]
        if def_defaults!=None  :
            real_vars =list(def_defaults)
        else:
            real_vars=[]

        def_len = len(def_args)

        while len(real_vars)<def_len:
            real_vars.insert(0, None)
        index =0
        for a in i_arg:
            real_vars[index]=a
            index+=1

        response =fun(*real_vars)
        return response
    def RunCmd(self, cmd):
        try:
            #cmd='sh\t'
            reIA = re.compile('\s*i\.(.+)')
            m = re.match(reIA, cmd)
            if m :
                response = self.IARunCmd(m.group(1))
            else:
                #stepCheck(self, CaseName, lineNo, cmd, expect, wait):
                reFun = re.compile('\s*f\.(.+)')
                import shlex

                reTry =re.compile('(.*)\s*try\s+(\d+)\s*:\s*(.+)', re.DOTALL|re.IGNORECASE)
                m = re.search(reTry, cmd)
                retryCounter=1
                if m:
                    retryCounter=int(m.group(2))
                    cmd = m.group(1)+m.group(3)
                lex = shlex.shlex(cmd)
                lex.quotes = '"'
                lex.whitespace_split = True
                newcmd=list(lex)
                m=None
                if len(newcmd):
                    m = re.match(reFun, newcmd[0])
                if m:

                    funname = m.group(1)

                    reQuoting=re.compile('\s*"(.*)"', re.DOTALL)
                    for i in range(0, len(newcmd)):
                        m = re.match(reQuoting, newcmd[i] )
                        if m:
                            newcmd[i]=m.group(1)

                    i_arg =[]
                    for x in newcmd[1:]:
                        if x.startswith('"') or x.startswith("'"):
                            i_arg.append(x)
                        else:
                            i_arg.append("'%s'"%str(x))

                    newcmd = '%s(%s)'%(funname,', '.join(i_arg))
                    cmd = newcmd

                self.cp+=1

                expectPat = '>|#'

                if self.sut[self.sutname].attribute.has_key('PROMPT'):
                    expectPat=self.sut[self.sutname].attribute['PROMPT']
                timeout = '2'
                if retryCounter!=1:
                    cmd ='try %d: %s'%(retryCounter, cmd)
                #print('cmd:%s'%cmd)
                #print('len:%d'%len(cmd))
                if cmd.endswith('?'):
                    self.sut_complete(cmd)
                else:
                    self.sut[self.sutname].stepCheck('casename', self.cp, cmd+'\t', expectPat,timeout)
                    self.record.append([self.sutname,cmd, expectPat,timeout])
        except Exception as e:
            print(e)
    def show(self):
        while not self.flagEndCase:
            if self.sutname!='tc':
                self.sut[self.sutname].show()
            time.sleep(0.1)
    def save2file(self, name=None):
        if not name :
            name = 'tc'

        import re
        fullname = name[:60]
        removelist = '\-_.'
        pat = r'[^\w'+removelist+']'
        name = re.sub(pat, '', fullname)
        tm = self.tmCreated.isoformat('_')
        tm =  re.sub(pat, '', tm)
        fullname = name+'-'+tm
        self.tcName = fullname
        csvfile = '%s.csv'%self.tcName
        from common import array2csvfile
        array2csvfile(self.record,csvfile)
    def do_Exit(self, name =None):
        if not name :
            name = 'tc'
        self.save2file(name)
        from runner import releaseDUTs
        releaseDUTs(self.sut, self.logger)
        self.flagEndCase =True
    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        #print('complete function hell')
        #print(text)
        #print(state)
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            #print(self.completion_matches)
            #print(state)
            #print(type(text))

            #self.RunCmd(str(text)+'\t')
            return self.completion_matches[state]

        except Exception as e :#IndexError :
            #print(e)
            #import traceback
            #print(traceback.format_exc())
            #print('hit here!!!')
            #print('text: %s'%(str(text)))
            #return  str(text)+'\t'
            return None
print('ia.exe/ia.py bench_file DUT1 [DUT2, DUT3 ...]')
benchfile = sys.argv[1]
dutNames = sys.argv[2:]
i=ia(benchfile, dutNames)
print('#'*80)

flagEndCase = False
while not i.flagEndCase:
    try:
        i.cmdloop()
        time.sleep(.1)
    except Exception as e:
        msg = traceback.format_exc()
        print(msg)
        i.save2file()

os._exit(0)
