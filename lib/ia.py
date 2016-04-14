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
import inspect
import pyHook, sys, pythoncom
#from pykeyboard import PyKeyboard
import pprint
import sys, time
import shlex
import datetime
import traceback
from runner import *
import re
from reload import reload
import imp
gDefaultTimeout = '2'
pid = 0
keyboard = None
flag_tab_down = False
line_buffer = ''
ia_instance =None
from common import bench2dict
def check_keyboard_tab_down(event):
    try:
        global flag_tab_down, ia_instance
        if pid != os.getpid():
            return True
        if os.name == 'nt':

            if chr(event.Ascii) == '\t':
                try:
                    #print('hit tab!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    #flag_tab_down = True
                    #keyboard.tap_key('\r')
                    if ia_instance:
                        ia_instance
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
    __args=None
    __kwargs=None
    script_file_name =None
    update =True # show output of sut immediately
    bench=None
    share_data = {}
    def convert_args(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        return self.__args, self.__kwargs
    def match_functions(self,function_name, sutname=None):
        if not sutname:
            sutname= self.sutname
        #class_obj =self.do_reload(function_name, sutname)
        members = inspect.getmembers(self.sut[sutname],inspect.ismethod)
        match =[]
        match_pair=[]
        index =0
        for k,v in members:
            if k.lower().find(function_name.lower())!=-1:
                match.append(index)
                try:
                    func =self.sut[sutname].__dict__[k]
                except KeyError:
                    parents = type.mro(type(self.sut[sutname]))[:-1]
                    for p in parents:
                        if p.__dict__.has_key(k):
                            func = p.__dict__[k]
                            break
                    func = v
                match_pair.append((k,func))
            index+=1
        if len(match)==1:
            match_pair=[members[match[0]]]
        elif len(match)>1:
            for k in match:
                if re.match("^%s$"%function_name,members[k][0]):
                    match_pair=[members[k]]
                    break
                elif re.match("^%s$"%function_name,members[k][0],re.IGNORECASE):
                    match_pair=[members[k]  ]
        return  match_pair

    def handle_command(self, command, sutname=None):

        options = self.__parseline__(command)
        if not sutname:
            sutname = self.sutname

        len_option = len(options)

        if len_option>0:
            function_name = options[0]
            candidate_function_pair = self.match_functions(function_name, sutname)
            len_candidate_fun = len(candidate_function_pair)
            if len_candidate_fun>1:
                print('more than 1 functions matched the input:')
                for k,v in candidate_function_pair:
                    print('\t'+k)
            elif len_candidate_fun==0:
                print('no function match!!!')
                try:
                    self.sut[sutname].send(command)
                except:
                    pass
            else:
                arg,kwargs=[],{}
                if len_option>1:
                    cmd = 'self.convert_args(self.sut[sutname], %s)'%(', '.join(options[1:]) )
                    eval(cmd, globals(),locals())
                    arg, kwargs = self.__args, self.__kwargs
                else:
                    cmd = 'self.convert_args(self.sut[sutname])'
                    eval(cmd, globals(),locals())
                    arg, kwargs = self.__args, self.__kwargs
                function_name, function_to_be_called = candidate_function_pair[0]
                #function_to_be_called(*arg, **kwargs)
                script_line = '\t%s.%s(%s)'%(sutname, function_name, ', '.join(options[1:]))
                self.__add_new_command__(sutname,function_name,', '.join(options[1:]) , arg, kwargs)
                try:
                    new_module =self.do_reload(function_name, sutname)
                    new_module.__dict__[function_name](*arg, **kwargs)
                except KeyError:
                    cmd = 'self.convert_args(%s)'%(', '.join(options[1:]) )
                    eval(cmd, globals(),locals())
                    arg, kwargs = self.__args, self.__kwargs
                    getattr(self.sut[sutname],function_name)(*arg, **kwargs)


    def help_set(self):
        print('''set variable in module ia:
        set bench ''')
    def complete_set(self, text, line, start_index,end_index):
        option = ['bench\n',
                  'bench <bench_file_name>\n',
                  'logpath',
                 'logpath <path_of_log>\n',
                  'sut',
                 'sut <sut_name>\n'
                  ]
        return  self.__complete_common(option, text,line,start_index,end_index)
    def do_help(self, line):

        options = self.__parseline__(line)
        number_of_options = len(options)
        response =super(ia, self).do_help(line)
        #if number_of_options==0:

        #elif number_of_options==1:

        #    if options[0] in dir(self) and self.sutname not in ['tc', '__case__', None]:
        #        function =self.__getattribute__(options[0])
        #        function(' '.join(options[1:]))





    def do_show(self, line):
        cmd = self.__parseline__(line)
        if len(cmd)==0:
            for var in dir(self):
                if not var.startswith('_') :
                    print(var)
            if self.sutname in ['tc', None, 'case', '__case__']:
                pass
            else:
                print('-%s below-'%self.sutname)
                for var in dir(self.sut[self.sutname]):
                    if not var.startswith('_'):
                        print('\t'+var)
            return

        var = cmd[0]
        print(var.lower(), self.__getattribute__(var.lower()))
    def do_set(self, line):

        cmd = self.__parseline__(line)
        var, value = cmd[:2]
        self.__setattr__(var.lower(), value.lower())
    def __complete_common(self, commands, text, line, start_index, end_index):
        if text:
            #print([command for command in commands
                    #if command.startswith(text)])
            return [command for command in commands
                    if command.startswith(text)]
        else:
            #print(commands)
            return commands
    def complete_cmdx(self, text, line, start_index, end_index):
        #print('cmdx ', text, line, start_index, end_index)
        if text:
            #print([command for command in commands
                    #if command.startswith(text)])
            return [command for command in commands
                    if command.startswith(text)]
        else:
            #print(commands)
            return commands

    def complete_help(self, *args):
        print('aaaaaaaaaaaaaa')
        return ['1', '2']

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
        #print('check question mark')
        while not self.flagEndCase:
            if self.rl:
                buf = self.rl.get_line_buffer()
                #print('buffer is', buf)
                if str(buf).endswith('?'):
                    if self.sutname != 'tc':
                        sut = self.sut[self.sutname]
                        sut.write(buf + '\b' * (len(buf)))
                        self.rl.mode.l_buffer.set_line(buf[:-1])



    def setErrorPatternCheck(self, enable=True):
        self.fErrorPatternCheck=enable
    def do_setCheckLine(self, enable='enable'):
        if enable.strip().lower() == 'enable':
            self.fErrorPatternCheck = True
        else:
            self.fErrorPatternCheck = False
        for sut in self.sut.keys() :
            self.sut[sut].setErrorPatternCheck(self.fErrorPatternCheck)
        print('%s check error in line '%('enabled' if self.fErrorPatternCheck else 'disabled'))


    def __init__(self, benchfile, dutname):
        #global pid, keyboard
        #keyboard = PyKeyboard()
        self.flag_running = True
        pid = os.getpid()
        self.tmCreated = datetime.datetime.now()
        self.tmTimeStampOfLastCmd = self.tmCreated
        self.share_data ={}
        Cmd.__init__(self, 'tab', sys.stdin, sys.stdout)#)#
        try:
            from readline import rl
            self.rl = rl
        except ImportError:
            pass
#script file

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
        self.script_file_name = '%s/%s.csv' % (self.case_path, self.tcName)
        ###########

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
        self.record = [['#var'],
                       ['defaultTime', '30'],
                       ['#setup'],
                       ['#SUT_Name', 'Command_or_Function', 'Expect', 'Max_Wait_Time', 'TimeStamp', 'Interval']
                       ]
        for record in self.record:
            self.save2file(None,[record])
        # self.save2file(self.record[0])

        logpath = '../../log'


        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath = createLogDir('ia', logpath)
        self.logger = createLogger('ia', logpath)




        # benchfile = './bench.csv'

        if os.path.exists(benchfile):
            bench = bench2dict(benchfile)
            self.bench_file= benchfile
            self.bench= bench
            self.log_path= logpath
            # dutname = ['N6', 'ix-syu']
            errormessage = ''
            duts = initDUT(errormessage, bench, dutname, self.logger, logpath, self.share_data)
            self.sut = duts
            self.sut['tc']=self

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
        self.update =True
        keyboard_monitor_thread = threading.Thread(target=self.monitor_keyboard)
        keyboard_monitor_thread.start()
    def do_t(self,line):
        options = self.__parseline__(line)

        sutname ,function_name = options[:2]
        members = inspect.getmembers(self.sut[sutname], inspect.ismethod)
        match =[]
        index =0
        for k,v in members:

            if k.lower().find(function_name.lower())!=-1:
                match.append(index)
            index+=1
        if len(match)==1:
            members[match[0]][1](*options[2:])
        elif len(match)>1:
            for k in match:
                if re.match(function_name,members[k][0]):
                    members[k][1](*options[2:])
                    break
                elif re.match(function_name,members[k][0],re.IGNORECASE):
                    members[k][1](*options[2:])
                    break
                else :
                    print(members[k][0]+"\n")
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
                        fundefstr = fundefstr + '\n\t'.join(ret.split('\n'))
                    self.helpDoc[self.sutname].update({m: fundefstr})
                except Exception as e:
                    pass

    def do_man(self, functionName=None):
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
        print('SUTs avaiable: %s'%( ', '.join(self.sut)))
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
    def default(self, line):
        #super(ia, self).default(line)
        th = threading.Thread(target=self.handle_command, args=[line, self.sutname])
        th.start()
        #self.handle_command(line, self.sutname)


    def postcmd(self, stop, line):
        if stop != None and len(str(stop)) != 0 and self.sutname != 'tc':
            out = self.sut[self.sutname].show() + '\n' + self.prompt + str(stop) + self.prompt
        stop = False
        self.emptyline()
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
    def do_dump(self, variable_name, sut_name=None):
        if sut_name is None:
            sut_name =self.sutname
        if sut_name not in self.sut:
            print('%s is not a correct sut name, choose one in [%s]'%(sut_name, ', '.join(self.sut)))
        if variable_name in dir(self.sut[sut_name]):
            if self.sutname in ['tc', '__case__', 'i']:
                print(pprint.pformat(self.__getattribute__(variable_name)))
            else:
                print(pprint.pformat(self.sut[sut_name].__getattribute__(variable_name)))
        else:
            print('ERROR: "%s" is not defined in sut %s'%(variable_name, sut_name))

    def __parseline__(self,line):

        lex = shlex.shlex(line)
        lex.quotes = "'\""
        lex.whitespace_split = True
        cmd = list(lex)
        if len(cmd)>0:
            if 'send'==cmd[0].lower():
                cmd=['send', '"%s"'%line[5:]]
        return cmd

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
                        self.save2file(record = [newRecord])

                        self.tmTimeStampOfLastCmd = now
                    else:
                        self.repeatCounter += 1
                    self.sut[self.sutname].stepCheck('casename', self.cp, cmd + '\t', '.*', str(timeout))


        except Exception as e:
            print(e)

    def show(self):
        while not self.flagEndCase:
            if self.sutname != 'tc' and self.update not in ['0', 'False', 0,'null', 'off', False]:
                try:
                    self.sut[self.sutname].show()
                except:
                    pass

            time.sleep(0.1)
    def __add_new_command__(self, sutname, function_name,arg_string, arg=None, kwarg=None):
        if not arg:
            arg=[]
        if not kwarg:
            kwarg={}
        now = datetime.datetime.now()
        strTimeout = '${defaultTime}'
        new_record =  [sutname, '%s(%s)'%(function_name, arg_string), '.*', strTimeout, now.isoformat('_'),
                                     now - self.tmTimeStampOfLastCmd]
        self.tmTimeStampOfLastCmd = now
        self.record.append(new_record)
        self.save2file(None, [new_record])

    def save2file(self, name=None, record=None):
        csvfile= self.script_file_name
        from common import array2csvfile
        if not record:
            record = self.record[-1]
        array2csvfile(record, csvfile)

    def do_eof(self, name=None):
        self.flagEndCase = False
        if name:
            fullname = name[:60]
            removelist = '\-_.'
            pat = r'[^\w' + removelist + ']'
            name = re.sub(pat, '', fullname)
            if name.endswith('.csv') or name.endswith('.CSV'):
                pass
            else:
                name+='.csv'
            new_file_name = os.path.dirname(self.script_file_name)+'/'+name
            os.rename(self.script_file_name,new_file_name )
            self.script_file_name= new_file_name
        print('saved to file %s '%(os.path.abspath(self.script_file_name)))
        if self.bench_file:
            print('cr.py %s %s full '%(os.path.abspath(self.script_file_name), os.path.abspath(self.bench_file)))
        from runner import releaseDUTs
        releaseDUTs(self.sut, self.logger)
        self.flagEndCase = True

    def do_bench(self, file_name):

        self.bench_file = file_name

    def do_reload(self,function_name, sutname=None):
        if not sutname:
            sutname = self.sutname
        modulename = self.sut[sutname].__module__
        parents = type.mro(type(self.sut[sutname]))[:-1]
        parents.insert(0, self.sut[sutname])
        class_name = 0
        import imp
        target_module_name =None
        target_module = None
        for p in parents:
            if p.__dict__.has_key(function_name):
                target_module_name= p.__module__
                break


        for p in parents:#[::-1]:
            mn = p.__module__
            if target_module_name==mn:
                module_info =imp.find_module(mn )# imp.new_module(modulename)
                module_dyn = imp.load_module(mn ,*module_info)
                reload(module_dyn)
                target_module= module_dyn




        #module_info =imp.find_module(modulename )# imp.new_module(modulename)
        #module_dyn = imp.load_module(modulename ,*module_info)
        #reload(module_dyn)
        #return module_dyn.__dict__[self.sut[sutname].__class__.__name__]
        return target_module.__dict__[target_module_name]#

    def __del__(self):
        self.flagEndCase = False
    def do_path(self,path):
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and path not in sys.path and abs_path not in sys.path:
            sys.path.insert(0, abs_path)
            print('add abs path(%s) to sys.path, original is %s'%(abs_path, path))
        elif path in sys.path or abs_path in sys.path:
            print('%s or %s is already in sys.path \n%s'%(abs_path, path, '\n'.join(sys.path)))

        else:
            print('path(%s) is not existed! please double check it'%(path))
    def help_path(self):
        print ( 'add a new path')

    def emptyline(self):
        """Called when an empty line is entered in response to the prompt.

        If this method is not overridden, it repeats the last nonempty
        command entered.

        """
        if self.lastcmd:
            self.lastcmd = ""
            return self.onecmd('\n')
    def help_init(self):
        print('"init new_sut_name" to create a new session named as "new_sut_name", defined in a given bench file %s'%self.bench_file)
    def do_init(self, sut_name):
        sut_name_list = self.__parseline__(sut_name)
        if sut_name in self.sut:
            print('sut(%s) is existed, "setsut %s" to switch to it'%(sut_name,sut_name))
        else:
            errormessage = ''

            bench = bench2dict(self.bench_file)
            duts = initDUT(errormessage, bench, sut_name_list, self.logger, self.log_path, self.share_data)
            last_sut='tc'
            for name in sut_name_list:
                if name in duts:
                    self.sut[name]= duts[name]
                    last_sut=name
                else:
                    print('failed to init %s'%name)
            self.do_setsut(last_sut)