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
import pyHook, sys, pythoncom
from pykeyboard import PyKeyboard
import sys,time
import datetime
import traceback
from runner import *
import re
gDefaultTimeout = '2'
pid =0
keyboard =None
def check_keyboard_tab_down(event):
    try:
        if pid != os.getpid():
            return True
        if os.name =='nt':
            if chr(event.Ascii) == '\t':
                #keyboard.tap_key('\r')

                keyboard.tap_key('\n')
                #print('tab down!')
    except Exception as e:
        pass
    return True
commands = [
    "foo",
    "foo bar blah",
    "bar",
    "bar baz blah",
    "baz",
    "baz foo blah"]
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
    lenCompleteBuffer=0
    tmTimeStampOfLastCmd=None
    cmdLineBuffer=''
    rl =None
    readline =None
    color = True
    fErrorPatternCheck=True
    repeatCounter=0
    pid =0
    keyboard=None
    def complete_cmdx(self, text, line, start_index, end_index):
        if text:
            return [command for command in commands
                    if command.startswith(text)]
        else:
            return commands
    def complete_help(self, *args):
        print('aaaaaaaaaaaaaa')
    def color(self, enable='disable'):
        if enable.lower().strip()=='disable':
            self.color=False
        else:
            self.color=True
        for sut in self.sut.keys():
            if sut !='tc':
                self.sut[sut].setOutputColor(self.color)
    def monitor_keyboard(self):
        self.keyboard = pyHook.HookManager()
        #print(self.keyboard.KeyDown)
        self.keyboard.KeyDown=check_keyboard_tab_down
        self.keyboard.HookKeyboard()
        while self.flag_running:
            pythoncom.PumpWaitingMessages()#PumpMessages()


    def checkQuestionMarkEnd(self):
        while not self.flagEndCase:
            if self.rl:
                buf = self.rl.get_line_buffer()
                #buf="aaaa?"
                if str(buf).endswith('?'):
                    if self.sutname!='tc':
                        sut = self.sut[self.sutname]
                        sut.write(buf+'\b'*(len(buf)))
                        #print("##################",self.rl.mode)
                        self.rl.mode.l_buffer.set_line(buf[:-1])

                        #print('#############',self.rl.get_line_buffer())
#                        self.rl.insert_text('\b')
                        #VOID keybd_event(BYTE bVk, BYTE bScan, DWORD dwFlags, PTR dwExtraInfo);
                        #user32.keybd_event(keycode,0,1,0) #is the code for KEYDOWN
                        #user32.keybd_event(keycode,0,2,0) #is the code for KEYDOWN
                        #time.sleep(0.5)
                        #break

    def emptyline(self):
        return ''
    def do_setCheckLine(self,enable='enable'):
        if enable.strip().lower()=='enable':
            self.fErrorPatternCheck=True

        else:
            self.fErrorPatternCheck=False
        for sut in self.sut.keys():
            self.sut[sut].setErrorPatternCheck(self.fErrorPatternCheck)
    def write2TcFile(self,record):
        from common import array2csvfile
        array2csvfile(record,self.dftCaseFile)

    def __init__(self, benchfile, dutname):
        global pid,keyboard
        keyboard = PyKeyboard()
        self.flag_running = True
        pid = os.getpid()
        self.tmCreated = datetime.datetime.now()
        self.tmTimeStampOfLastCmd = self.tmCreated
        Cmd.__init__(self, 'tab', sys.stdin, sys.stdout)

        fullname = 'tc'
        removelist = '\-_.'
        pat = r'[^\w'+removelist+']'
        name = re.sub(pat, '', fullname)
        tm = ''
        if name=='tc':
            tm = '-'+self.tmCreated.isoformat('_')

        tm =  re.sub(pat, '', tm)
        self.dftCaseFile=name+tm+'.csv'



        self.tcName = 'tc'
        self.sutname='tc'
        self.tabend = 'disable'
        self.record =[['#var'], ['defaultTime', '30'],['#setup'],
                      ['#SUT_Name','Command_or_Function', 'Expect', 'Max_Wait_Time','TimeStamp','Interval']]
        self.write2TcFile(self.record)
        #self.write2TcFile(self.record[0])
        self.intro = '''welcome to InterAction of DasH'''
        logpath = '../log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath =   createLogDir('ia',logpath)
        self.logger = createLogger('ia',logpath)
        #benchfile = './bench.csv'
        from common import bench2dict
        bench =bench2dict(benchfile)

        #dutname = ['N6', 'ix-syu']
        errormessage = ''
        shareData={}
        duts= initDUT(errormessage,bench, dutname,self.logger , logpath, shareData)
        self.sut=duts
        import threading
        th = threading.Thread(target=self.show)
        th.start()
        th = threading.Thread(target=self.checkQuestionMarkEnd)
        th.start()
        self.do_setsut(dutname[0])
        self.helpDoc={}
        self.cmdbank=[]
        for sut in self.sut.keys():
            self.CreateDoc4Sut(sut)

        keyboard_monitor_thread = threading.Thread(target=self.monitor_keyboard)
        keyboard_monitor_thread.start()


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
            self.prompt= '%s@%s::>'%(os.linesep, self.sutname)
            return 'current SUT: %s'%(self.sutname)
        else:
            return 'sutsut(\'%s\') is not defined'%sutname
    def postcmd(self,stop, line):
        if stop!=None and len(str(stop))!=0 and self.sutname!='tc':

            out = self.sut[self.sutname].show()+'\n'+self.prompt+str(stop)+self.prompt
            #print(self.InteractionOutput,end='')
        stop = False
        if self.flagEndCase:
            stop =True
        return stop
    def sut_complete(self, text):
        #print('sut_complet', text)
        sutresponse=None
        if self.sutname!='tc':

            sut = self.sut[self.sutname]
            sutresponse = str(text)
            sut.write(str(text)+'\t')
            sut.timestampCmd=time.time()
            time.sleep(1)
            self.lenCompleteBuffer = len(text)
            try:
                sutresponse = sut.find('%s.+'%text, 1)
                #print('here is sut response', sutresponse)
                #print('here is sut response end')
                #lresp= sutresponse.split('\n')
                #line = lresp[-1]

                sutresponse=re.search('.*(%s.+).*$'%text,sutresponse).group(1)
                self.lenCompleteBuffer = len(sutresponse)

                #print(self.prompt)
                #sutresponse = '\b'*self.lenCompleteBuffer+sutresponse
                #print('2here is sut response', sutresponse)
                #print('2here is sut response end')
                #import readline
                #print('####hello###1',readline.get_line_buffer())
                #readline.insert_text(sutresponse)
                #print('####hello###2',readline.get_line_buffer())
                #print('sutresponse1', sutresponse)
                sutresponse = sutresponse.strip()
                sutresponse=sutresponse.split(' ')

                #print('sutresponse2', sutresponse)
                sutresponse=sutresponse[-1]+' '
            except Exception as e:
                print(e)
                sutresponse=None
        if self.lenCompleteBuffer:
            for i in range(0,self.lenCompleteBuffer):
                #print('Backspace!!!')
                self.sut[self.sutname].write('\b')
            self.lenCompleteBuffer=0
        #print('3here is sut response', sutresponse)
        #print('3here is sut response end')

        return sutresponse

    def completenames(self, text, *ignored):
        #print('hello')
        resp=[]
        if self.sutname=='tc':
            dotext = 'do_'+ text
            resp = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        else:
            sutresp = self.sut_complete(text)
            if sutresp:
                resp.append(sutresp)
        return resp


    def completedefault(self, *ignored):
        #print(ignored)
        #print('complete default')
        if self.sutname!='tc':
            #print('ignored', ignored)
            response = self.sut_complete(ignored[1])
            #print('response here:', response)
            #lResp = ignored[1].split(' ')
            #lenResp = len(lResp)
            #response =
            #response =' '.join(lResp[lenResp/2:-1])
            #response+=' '+ lResp[-1]
            #self.onecmd(ignored[1])#+'\t'
            #i.cmdqueue=[]
            #pass
            #self.RunCmd(ignored[1]+'\t')

            return [response]#Cmd.completedefault(self ,ignored)
        else:
            #print('ignored', ignored)
            return Cmd.completedefault(self, ignored)


    def precmd(self,line):
        #print('line:',line)
        #linetemp = line.strip()
        #line='\t'
        #print('')
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
                timeout = gDefaultTimeout
                strTimeout = '${defaultTime}'
                if retryCounter!=1:
                    cmd ='try %d: %s'%(retryCounter, cmd)
                #print('cmd:%s'%cmd)
                #print('len:%d'%len(cmd))
                sut = self.sut[self.sutname]
                if cmd.endswith('?'):
                    sut.write(cmd)
                    #sut.stepCheck('casename', self.cp, cmd, expectPat,str(timeout))
                    sutresponse = str(cmd).strip()[:-1]+' '
                    self.rl.insert_text(sutresponse)
                    #self.cmdLineBuffer=sutresponse
                    #import  readline
                    #print('inert text to readline :',sutresponse)
                    #readline.clear_history()
                    #readline.insert_text(sutresponse)
                    #print(readline.get_line_buffer())
                    #self.sut_complete(cmd)
                else:
                    now = datetime.datetime.now()
                    lastSut, lastCmd, lastExp, lastTimeout = self.record[-1][:4]
                    if lastSut !=self.sutname or lastCmd!= cmd or lastExp != expectPat or lastTimeout!= strTimeout:
                        if self.repeatCounter:
                            self.record[-1][1]="try %d:%s"%(self.repeatCounter+1,self.record[-1][1])
                            self.repeatCounter=0
                        newRecord = [self.sutname,cmd, expectPat,strTimeout,now.isoformat('_'), now -self.tmTimeStampOfLastCmd ]
                        self.record.append(newRecord)
                        self.write2TcFile([newRecord])
                        self.tmTimeStampOfLastCmd=now
                    else:
                        self.repeatCounter+=1
                    self.sut[self.sutname].stepCheck('casename', self.cp, cmd+'\t', '.*',str(timeout))


        except Exception as e:
            print(e)
    def show(self):
        while not self.flagEndCase:
            if self.sutname!='tc':
                try:
                    self.sut[self.sutname].show()
                except:
                    pass

            time.sleep(0.1)
    def save2file(self, name=None):
        if not name :
            name = 'tc'


        fullname = name[:60]
        removelist = '\-_.'
        pat = r'[^\w'+removelist+']'
        name = re.sub(pat, '', fullname)
        tm = ''
        if name=='tc':
            tm = '-'+self.tmCreated.isoformat('_')

        tm =  re.sub(pat, '', tm)
        fullname = name+tm
        self.tcName = fullname
        csvfile = '%s.csv'%self.tcName
        from common import array2csvfile
        array2csvfile(self.record,csvfile)
    def do_Exit(self, name =None):
        self.flag_running=False
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
            origline = readline.get_line_buffer() #('show alar\t'#
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

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.readline = readline

                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
                self.rl = readline.rl
                if self.cmdLineBuffer!='':
                    self.readline.insert_text(self.cmdLineBuffer)
                    self.rl._update_prompt_pos(len(self.cmdLineBuffer))
                    #rl.prompt_begin_pos =
                    self.rl._update_line()
                #readline.parse_and_bind('?: completeQuestion')
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = raw_input(self.prompt)#+self.cmdLineBuffer

                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                if len(self.cmdLineBuffer):
                    self.rl.console.write(self.cmdLineBuffer)
                    self.rl.console.flush()
                    line =self.cmdLineBuffer+line
                    self.readline.insert_text(self.cmdLineBuffer)

                    self.cmdLineBuffer=''
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally :
            if self.use_rawinput and self.completekey:

                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def do_bench(self, file_name):

        self.bench_file = file_name





