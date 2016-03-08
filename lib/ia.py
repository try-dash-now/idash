#! /usr/bin/env python
__author__ = 'Sean Yu'
'''created @2015/11/13'''
import os, sys

pardir = os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir, sub])
    if libpath not in sys.path:
        sys.path.insert(0, libpath)
import threading
from cmd import Cmd
import pyHook, sys, pythoncom
from pykeyboard import PyKeyboard
import sys, time
import datetime
import traceback
from runner import *
import re

gDefaultTimeout = '2'
pid = 0
keyboard = None
flag_tab_down = False
line_buffer = ''


def check_keyboard_tab_down(event):
    try:
        global flag_tab_down, IA_INSTANCE
        if pid != os.getpid():
            return True
        if os.name == 'nt':

            if chr(event.Ascii) == '\t':
                try:
                    #print('hit tab!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    #flag_tab_down = True
                    #keyboard.tap_key('\r')
                    #keyboard.tap_key('\n')
                    pass
                    #print('hit tab@@@')
                except NotImplementedError:
                    print('not implemented Error ')
                    pass
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
    tmCreated = None
    record = None
    cp = 0
    sut = None
    sutname = None
    tabend = None  # 'disable'
    tcName = None

    flagEndCase = False
    quoting = '"'
    lenCompleteBuffer = 0
    tmTimeStampOfLastCmd = None
    cmdLineBuffer = ''
    rl = None
    readline = None
    color = True
    fErrorPatternCheck = True
    repeatCounter = 0
    pid = 0
    keyboard = None
    log_path = None  # default is ../../log, it's to make the log file not part of this project
    bench_file = None  # the file name of bench file, if not given, it will be ./bench.csv
    case_path = None  # default is ../../test, it's to make the log file not part of this project
    output = None

    def complete_cmdx(self, text, line, start_index, end_index):
        print('cmdx ', text, line, start_index, end_index)
        if text:
            print([command for command in commands
                    if command.startswith(text)])
            return [command for command in commands
                    if command.startswith(text)]
        else:
            print(commands)
            return commands

    def complete_help(self, *args):
        print('aaaaaaaaaaaaaa')
        return [['1', '2']]

    def color(self, enable='disable'):
        if enable.lower().strip() == 'disable':
            self.color = False
        else:
            self.color = True
        for sut in self.sut.keys():
            if sut != 'tc':
                self.sut[sut].setOutputColor(self.color)

    def monitor_keyboard(self):
        self.keyboard = pyHook.HookManager()
        # print(self.keyboard.KeyDown)

        self.keyboard.KeyDown = check_keyboard_tab_down
        self.keyboard.HookKeyboard()
        while self.flag_running:
            pythoncom.PumpWaitingMessages()  # PumpMessages()

    def checkQuestionMarkEnd(self):
        print('check question mark')
        while not self.flagEndCase:
            if self.rl:
                buf = self.rl.get_line_buffer()
                print('buffer is', buf)
                if str(buf).endswith('?'):
                    if self.sutname != 'tc':
                        sut = self.sut[self.sutname]
                        sut.write(buf + '\b' * (len(buf)))
                        self.rl.mode.l_buffer.set_line(buf[:-1])




    def do_setCheckLine(self, enable='enable'):
        if enable.strip().lower() == 'enable':
            self.fErrorPatternCheck = True
        else:
            self.fErrorPatternCheck = False
        for sut in self.sut.keys():
            self.sut[sut].setErrorPatternCheck(self.fErrorPatternCheck)
        print('%s check error in line '%('enabled' if self.fErrorPatternCheck else 'disabled'))


    def __init__(self, benchfile, dutname):
        global pid, keyboard
        keyboard = PyKeyboard()
        self.flag_running = True
        pid = os.getpid()
        self.tmCreated = datetime.datetime.now()
        self.tmTimeStampOfLastCmd = self.tmCreated
        Cmd.__init__(self)#, 'tab', sys.stdin, sys.stdout)
        try:
            from readline import rl
            self.rl = rl
        except ImportError:
            pass

        fullname = 'tc'
        removelist = '\-_.'
        pat = r'[^\w' + removelist + ']'
        name = re.sub(pat, '', fullname)
        tm = ''
        if name == 'tc':
            tm = '-' + self.tmCreated.isoformat('_')

        tm = re.sub(pat, '', tm)
        self.dftCaseFile = name + tm + '.csv'

        self.tcName = 'tc'
        self.sutname = 'tc'
        self.tabend = 'disable'
        self.record = [['#var'], ['defaultTime', '30'], ['#setup'],
                       ['#SUT_Name', 'Command_or_Function', 'Expect', 'Max_Wait_Time', 'TimeStamp', 'Interval']]
        self.save2file()
        # self.save2file(self.record[0])
        self.intro = '''welcome to InterAction of DasH'''
        logpath = '../../log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath = createLogDir('ia', logpath)
        self.logger = createLogger('ia', logpath)
        # benchfile = './bench.csv'
        from common import bench2dict
        if os.path.exists(benchfile):
            bench = bench2dict(benchfile)
            # dutname = ['N6', 'ix-syu']
            errormessage = ''
            shareData = {}
            duts = initDUT(errormessage, bench, dutname, self.logger, logpath, shareData)
            self.sut = duts

            th = threading.Thread(target=self.show)
            th.start()
            th = threading.Thread(target=self.checkQuestionMarkEnd)
            th.start()
            self.do_setsut(dutname[0])
            self.helpDoc = {}
            self.cmdbank = []
            for sut in self.sut.keys():
                self.CreateDoc4Sut(sut)
        else:
            self.sut = {}
            self.do_setsut('tc')
            self.helpDoc = {}
            self.cmdbank = []
            self.output = 'no test bench assigned, please try "set bench [path/file_name] or [file_name]", the default path is ../../test'
            print(self.output)

        keyboard_monitor_thread = threading.Thread(target=self.monitor_keyboard)
        keyboard_monitor_thread.start()

    def CreateDoc4Sut(self, sutname=None):
        if not sutname:
            self.sutname = sutname
        if self.helpDoc.has_key(self.sutname):
            return
        members = dir(self.sut[self.sutname])

        self.helpDoc.update({self.sutname: {}})
        for m in sorted(members):
            if m.startswith('__'):
                pass
            else:
                import inspect
                try:
                    try:
                        fundef = inspect.getsource(
                            eval('self.sut[self.sutname].%s' % m))  # recreate function define for binary distribute
                        fundefstr = fundef[:fundef.find(':')]
                    except Exception as e:
                        (args, varargs, keywords, defaults) = inspect.getargspec(eval('self.sut[self.sutname].%s' % m))
                        argstring = ''
                        largs = len(args)
                        ldefaults = len(defaults)
                        gaplen = largs - ldefaults
                        index = 0

                        for arg in args:
                            if index < gaplen:
                                argstring += '%s, ' % arg
                            else:
                                defvalue = defaults[index - gaplen]
                                if type('') == type(defvalue):
                                    defvalue = '"%s"' % defvalue
                                argstring += '%s = %s, ' % (arg, str(defvalue))
                            index += 1

                        fundefstr = '%s( %s )' % (m, argstring)
                        fundef = fundefstr
                    listoffun = fundef.split('\n')
                    ret = eval('self.sut[self.sutname].%s.__doc__' % m)
                    if ret:
                        fundefstr = fundefstr + '\n\t' + '\n\t'.join(ret.split('\n'))
                    self.helpDoc[self.sutname].update({m: fundefstr})
                except Exception as e:
                    pass

    def doc(self, functionName=None):
        print('SUT:%s\n' % self.sutname)
        if self.sutname not in ['tc', '__case__']:
            self.CreateDoc4Sut(self.sutname)
            for fun in sorted(self.helpDoc[self.sutname].keys()):
                if functionName:
                    lowerFunName = fun.lower()
                    if lowerFunName.find(functionName.lower()) != -1:
                        print(fun)
                        print('\t' + self.helpDoc[self.sutname][fun])
                else:
                    print(fun)
                    print('\t' + self.helpDoc[self.sutname][fun])

    def do_setsut(self, sutname='tc'):
        output =''
        if sutname == '':
            sutname = 'tc'
        if self.sut.get(sutname) or sutname == 'tc' or sutname == '__case__':
            self.sutname = sutname
            self.prompt = '%s@%s::>' % (os.linesep, self.sutname)
            output= 'current SUT: %s' % (self.sutname)
        else:
            output ='sutsut(\'%s\') is not defined' % sutname
        print(output)
        return output

    def postcmd(self, stop, line):
        if stop != None and len(str(stop)) != 0 and self.sutname != 'tc':
            out = self.sut[self.sutname].show() + '\n' + self.prompt + str(stop) + self.prompt
        stop = False
        if self.flagEndCase:
            stop = True
        return stop

    def sut_complete(self, text):
        sutresponse = None
        if self.sutname != 'tc':

            sut = self.sut[self.sutname]
            sutresponse = str(text)
            sut.write(str(text) + '\t')
            sut.timestampCmd = time.time()
            time.sleep(1)
            self.lenCompleteBuffer = len(text)
            try:
                sutresponse = sut.find('%s.+' % text, 1)
                sutresponse = re.search('.*(%s.+).*$' % text, sutresponse).group(1)
                self.lenCompleteBuffer = len(sutresponse)

                sutresponse = sutresponse.strip()
                sutresponse = sutresponse.split(' ')

                sutresponse = sutresponse[-1] + ' '
            except Exception as e:
                print(e)
                sutresponse = None
        if self.lenCompleteBuffer:
            for i in range(0, self.lenCompleteBuffer):
                # print('Backspace!!!')
                self.sut[self.sutname].write('\b')
            self.lenCompleteBuffer = 0
        # print('3here is sut response', sutresponse)
        # print('3here is sut response end')

        return sutresponse




    def complete(self, text, state):
        response_of_complete = super(ia,self).complete(text,state)
        #print(response_of_complete)
        print(self.prompt)
        if  not response_of_complete:
            response_of_completenames = self.completenames(text)
            print(self.prompt+'\n')
            for opt in response_of_completenames:
                print('\t'+opt)
            print('\n')
            if len(response_of_completenames)==1:
                #if response_of_complete and text.strip()!='':
                for char in response_of_complete[len(text):]:
                    keyboard.tap_key(char)
                keyboard.tap_key(' ')
        else:
            print('\n')
            for opt in response_of_complete:
                print('\t'+opt)
            print('\n')

    def precmd(self, line):
        if self.sutname != 'tc':
            if line == ' ':
                self.RunCmd(line)
            elif temp == '':
                self.RunCmd(line)
            elif temp.lower() == 'help' or temp == '?':
                self.RunCmd(line)
                line = ''
        # print(self.InteractionOutput,end='')
        return line

    def default(self, line):
        try:
            if line[-1] == '\t':
                print("@" * 80)
            if self.sutname != 'tc':
                if self.tabend != 'disable':
                    line += '\t'

                self.RunCmd(line)

        except Exception as e:
            msg = traceback.format_exc()
            print(msg)

    def IARunCmd(self, data):
        import shlex
        lex = shlex.shlex(data)
        lex.quotes = '"'
        lex.whitespace_split = True
        cmd = list(lex)
        reQuoting = re.compile('\s*"(.*)"', re.DOTALL)
        for i in range(0, len(cmd)):
            m = re.match(reQuoting, cmd[i])
            if m:
                cmd[i] = m.group(1)
        funname = cmd[0]
        i_arg = cmd[1:]
        fun = self.__getattribute__(funname)
        import inspect
        (def_args, def_varargs, def_keywords, def_defaults) = inspect.getargspec(fun)

        def_args = def_args[1:]
        if def_defaults != None:
            real_vars = list(def_defaults)
        else:
            real_vars = []

        def_len = len(def_args)

        while len(real_vars) < def_len:
            real_vars.insert(0, None)
        index = 0
        for a in i_arg:
            real_vars[index] = a
            index += 1

        response = fun(*real_vars)
        return response

    def RunCmd(self, cmd):
        try:
            # cmd='sh\t'
            reIA = re.compile('\s*i\.(.+)')
            m = re.match(reIA, cmd)
            if m:
                response = self.IARunCmd(m.group(1))
            else:
                # stepCheck(self, CaseName, lineNo, cmd, expect, wait):
                reFun = re.compile('\s*f\.(.+)')
                import shlex

                reTry = re.compile('(.*)\s*try\s+(\d+)\s*:\s*(.+)', re.DOTALL | re.IGNORECASE)
                m = re.search(reTry, cmd)
                retryCounter = 1
                if m:
                    retryCounter = int(m.group(2))
                    cmd = m.group(1) + m.group(3)
                lex = shlex.shlex(cmd)
                lex.quotes = '"'
                lex.whitespace_split = True
                newcmd = list(lex)
                m = None
                if len(newcmd):
                    m = re.match(reFun, newcmd[0])
                if m:

                    funname = m.group(1)

                    reQuoting = re.compile('\s*"(.*)"', re.DOTALL)
                    for i in range(0, len(newcmd)):
                        m = re.match(reQuoting, newcmd[i])
                        if m:
                            newcmd[i] = m.group(1)

                    i_arg = []
                    for x in newcmd[1:]:
                        if x.startswith('"') or x.startswith("'"):
                            i_arg.append(x)
                        else:
                            i_arg.append("'%s'" % str(x))

                    newcmd = '%s(%s)' % (funname, ', '.join(i_arg))
                    cmd = newcmd

                self.cp += 1

                expectPat = '>|#'

                if self.sut[self.sutname].attribute.has_key('PROMPT'):
                    expectPat = self.sut[self.sutname].attribute['PROMPT']
                timeout = gDefaultTimeout
                strTimeout = '${defaultTime}'
                if retryCounter != 1:
                    cmd = 'try %d: %s' % (retryCounter, cmd)
                # print('cmd:%s'%cmd)
                # print('len:%d'%len(cmd))
                sut = self.sut[self.sutname]
                if cmd.endswith('?'):
                    sut.write(cmd)
                    # sut.stepCheck('casename', self.cp, cmd, expectPat,str(timeout))
                    sutresponse = str(cmd).strip()[:-1] + ' '
                    if self.rl:
                        self.rl.insert_text(sutresponse)
                    else:
                        print(sutresponse)
                        # self.cmdLineBuffer=sutresponse
                        # import  readline
                        # print('inert text to readline :',sutresponse)
                        # readline.clear_history()
                        # readline.insert_text(sutresponse)
                        # print(readline.get_line_buffer())
                        # self.sut_complete(cmd)
                else:
                    now = datetime.datetime.now()
                    lastSut, lastCmd, lastExp, lastTimeout = self.record[-1][:4]
                    if lastSut != self.sutname or lastCmd != cmd or lastExp != expectPat or lastTimeout != strTimeout:
                        if self.repeatCounter:
                            self.record[-1][1] = "try %d:%s" % (self.repeatCounter + 1, self.record[-1][1])
                            self.repeatCounter = 0
                        newRecord = [self.sutname, cmd, expectPat, strTimeout, now.isoformat('_'),
                                     now - self.tmTimeStampOfLastCmd]
                        self.record.append(newRecord)
                        self.write2TcFile([newRecord])
                        self.tmTimeStampOfLastCmd = now
                    else:
                        self.repeatCounter += 1
                    self.sut[self.sutname].stepCheck('casename', self.cp, cmd + '\t', '.*', str(timeout))


        except Exception as e:
            print(e)

    def show(self):
        while not self.flagEndCase:
            if self.sutname != 'tc':
                try:
                    self.sut[self.sutname].show()
                except:
                    pass

            time.sleep(0.1)

    def save2file(self, name=None, record=None):
        if not name:
            name = 'tc'

        fullname = name[:60]
        removelist = '\-_.'
        pat = r'[^\w' + removelist + ']'
        name = re.sub(pat, '', fullname)
        tm = ''
        if name == 'tc':
            tm = '-' + self.tmCreated.isoformat('_')

        tm = re.sub(pat, '', tm)
        fullname = name + tm
        self.tcName = fullname
        if self.case_path:
            pass
        else:
            self.case_path = '../../test'
        if not os.path.exists(self.case_path):
            os.mkdir(self.case_path)
        csvfile = '%s/%s.csv' % (self.case_path, self.tcName)
        from common import array2csvfile
        if not record:
            record = self.record
        array2csvfile(record, csvfile)
        self.record=[]

    def do_Exit(self, name=None):
        self.flagEndCase = False
        if not name:
            name = 'tc'
        self.save2file(name)
        from runner import releaseDUTs
        releaseDUTs(self.sut, self.logger)
        self.flagEndCase = True




    def do_bench(self, file_name):

        self.bench_file = file_name

    def __del__(self):
        self.flagEndCase = False
