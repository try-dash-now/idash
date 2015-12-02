__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''
a term is an interface to interoperate with Software/Device Under Test/Used
provides:
1. command sent to software/device
2. show the output, just the updated recently
3. searching given pattern from a given range, e.g. right after last command entered
'''
import time
class dut(object):
    '''
    streamOut:  string of Software/Device's output, __init__ will set it to ''
    idxSearch:  number, based on 0, default is 0, it's the index of streamOut, and point to where to find the pattern
                right after this index.
                function Send(will move it to the end of streamOut
                function Find will move idxSearch to index where is right after the pattern in streamOut
    idxUpdate:  number, 0-based, default is 0, point to index of streamOut, when the last call of function Print
                function Prind will move it to the end of streamOut
    logfile  :  the log file, which named as name.log
    loginDone:
                bool, initial value is False, means didn't complete the process of Device log-in, after log-in, it should be set to True
    attribute   :
                dict, initial is None, and assigned in __init__ as {} or set to the given variable attr
    SessionAlive:
                bool, initial is True, when session is closing, set it to False
    '''
    streamOut   =   None
    idxSearch   =   0
    idxUpdate   =   0
    logfile     =   None

    attribute   =   None
    SessionAlive =  True
    name         =  None #the term name, string
    logger       =  None #parent logger, passed to term, default is logger,no logger needed
    defaultHandler= 'stepCheck' # the default handler for each action in sequences e.g. setup, run ,teardown
    timestampCmd   =None # record the time stamp of last interaction, to anti-idle
    loginDone   = False
    sock        =None
    debuglevel  = 0
    FailFlag    =False # the flag means in Session's perspective view, case failed
    ErrorMessage =None # to store the error message
    autoReloginFlag = False
    counterRelogin =0
    color =True
    errorLines=None
    fErrorPatternCheck = False
    shareData=None
    def __del__(self):
        self.SessionAlive=False
        if self.logfile:
            self.logfile.flush()
    def setOutputColor(self, enable=True):
        self.color=enable
    def setErrorPatternCheck(self, enable=True):
        self.fErrorPatternCheck=enable

    def setAutoReloginFlag(self, flag=True):
        if flag:
            self.autoReloginFlag =True
        else:
            self.autoReloginFlag=False
    def __init__(self, name, attr =None,logger=None, logpath= None, shareData=None):
        '''
        initializing the term
        name:       string, the term's name
        attr:       a dict, the attributes of term
        logger:     a logger instance, allow this term pass message to parent object
        logpath:    string, the path of the log file for this ter
        '''
        self.errorLines =   ''
        self.name       =   name
        self.logger     =   logger
        if attr:
            self.attribute =attr
        else:
            self.attribute = {}
        if logger:
            logger.info('openLogfile %s in %s'%(name,logpath))
        if self.attribute.get("LINESEP"):
            LINESEP = self.attribute.get('LINESEP').replace('\\r', '\r').replace('\\n', '\n')
            self.attribute['LINESEP']=LINESEP
        else:
            self.attribute['LINESEP']='\n'

        if self.attribute.get("ERROR_PATTERN"):
            LINESEP = self.attribute.get('ERROR_PATTERN').replace('\\r', '\r').replace('\\n', '\n')
            self.attribute['ERROR_PATTERN']=LINESEP
        else:
            self.attribute['ERROR_PATTERN']='fail|error|err|wrong'


        if self.attribute.get("LOGIN_LINESEP"):
            LOGIN_LINESEP = self.attribute.get('LOGIN_LINESEP').replace('\\r', '\r').replace('\\n', '\n')
            self.attribute['LOGIN_LINESEP']=LOGIN_LINESEP
        else:
            self.attribute['LOGIN_LINESEP']='\n'
        self.openLogfile(logpath)
        try:
            from colorama import Fore, Back, Style, init
            init()
            self.color=True
        except Exception as e:
            self.color=False
        if shareData:
            self.shareData =shareData
        else:
            self.shareData={}
    def setValue(self, name, value):
        from runner import gShareDataLock, gShareData
        gShareDataLock.acquire()
        try:
            gShareData[name]=value
        except Exception as e:
            print(e)
        gShareDataLock.release()
    def getValue(self, name):
        from runner import gShareDataLock, gShareData
        try:
            tmpvalue = gShareData[name]
            print('%s:%s'%(str(name), str(tmpvalue).replace('\\n','\n').replace('\\r','\r')))
            return  tmpvalue
        except Exception as e:

            import pprint
            print('dump of ShareData')
            print(pprint.pformat(gShareData))
            print(e)
            print('%s is not in shareData'%(str(name)))

    def checkLine(self,str):
        if not self.fErrorPatternCheck:
            return str

        lines = str.split('\n')
        import re
        rePat = re.compile(self.attribute['ERROR_PATTERN'], re.IGNORECASE)
        newLines =[]
        for line in lines:
            if re.search(rePat, line):
                self.FailFlag= True
                if self.ErrorMessage:
                    pass
                else:
                    self.ErrorMessage=''
                self.ErrorMessage+="%s checkLine: ERROR_PATTERN FOUND: %s"%(self.name, line)
                self.errorLines+='\n%s'%line
                if self.logger:
                    self.logger.error("%s ERROR_PATTERN FOUND: %s"%(self.name, line))
                else:
                    print("ERROR_PATTERN FOUND(%s): %s"%(self.name, line))
    def colorString(self, str):
        if not self.color:
            return  str
        try:
            from colorama import Fore, Back, Style
        except Exception as e:
            return str
        lines = str.split('\n')
        import re
        rePat = re.compile('fail|error|err|wrong', re.IGNORECASE)
        newLines =[]
        for line in lines:
            if re.search(rePat, line):
                line = Fore.RED+Back.CYAN + line +Style.RESET_ALL
            newLines.append(line)
        return '\n'.join(newLines)


    def openLogfile(self, logpath):
        '''
        logpath, a folder path, where log to be found
        '''
        import os
        if not logpath:
            logpath = os.getcwd()
        log = os.path.abspath(logpath)
        log= '%s%s%s'%(log,os.path.sep,'%s.log'%self.name)

        if self.logfile:
            tmplog = self.logfile
            self.logfile=None
            tmplog.close()
            self.logger.info('streamOut size is %d, to be reset to 0'%(len(self.streamOut)))
            self.streamOut   =  ''
            self.idxSearch   =   0
            self.idxUpdate   =   0
        self.logfile = open(log, "wb")


    def show(self):
        '''return the delta of streamOut from last call of function Print,
        and move idxUpdate to end of streamOut'''
        if self.streamOut==None:
            raise NotImplementedError('please implement function show in your class')
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())
        if result!='' and result[-1]!='\n' and result[-1]!='\r':
            #import sys
            #sys.stdout.write('\t%s'%(result.replace('\n', '\n\t')))
            result= self.colorString(result)
            print('\t%s'%(result.replace('\n', '\n\t').replace('\r\n','\n'))),
        return result


        #raise NotImplementedError('please implement function show in your class')
    def write(self, buffer=''):
        import time
        self.timestampCmd= time.time()

    def write2file(self, data, filename=None):
        '''write the data to a given file
        if filename is None, the create a term_name.txt under current path of term logfile
        '''

        if filename:
            f =open(filename, 'wb')
            f.write(data)
            f.flush()
        else:
            self.info(data)

    def formatMsg(self, msg):
        import datetime
        now =datetime.datetime.now()
        msg = '%s\t%s\t%s'%(now.isoformat().replace("T", ' '), self.name, msg)
        print(msg)
        return msg
    def info(self, msg):
        '''
        add info message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.info(msg)

    def error(self, msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.error(msg)
    def debug(self, msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)

        if self.logger:
            self.logger.debug(msg)

    def call(self, funName, *args, **kwargs):
        fun = self.__getattribute__(funName)
        try:
            return fun(*args, **kwargs)
        except:
            import inspect
            (arg, varargs, keywords, defaults) =inspect.getargspec(fun)
            msg ='''
call function(%s)
    input args:
        %s
    input Kwargs:
        %s.
    define args:
        %s
    define varargs:
        %s
    define keywords:
        %s
    define defaults:
        %s'''%(
            funName,
            str(args),
            str(kwargs),
            str(arg),
            str(varargs),
            str(keywords),
            str(defaults)
        )
            raise ValueError(msg)
    def sleep(self, wait):
        import time
        time.sleep(float(wait))

    def singleStep(self, cmd, expect, wait, ctrl=False, noPatternFlag=False, noWait=False):

        self.send(cmd, ctrl, noWait)
        self.show()
        import time
        time.sleep(0.01)
        self.find(expect, float(wait), noPattern=noPatternFlag)
        self.show()
#       if not noPattern:
#           self.find(expect, float(wait), noPattern=noPattern)
#           self.show()
#        else:
#            self.find(expect, float(wait), noPattern=noPattern)
#            self.show()
            #raise RuntimeError('found pattern(%s) within %s'%(expect,wait))

    def test(self,cmd, expect, wait):
        self.stepCheck('tc', '', cmd, expect,wait)
    def stepCheck(self, CaseName, lineNo, cmd, expect, wait):
        def analyzeStep(casename, command, expect, wait):
            import re
            reRetry         = re.compile("^\s*try\s+([0-9]+)\s*:(.*)", re.I)
            reFunction      = re.compile('\s*FUN\s*:\s*(.+?)\s*\(\s*(.*)\s*\)|\s*(.+?)\s*\(\s*(.*)\s*\)\s*$',re.IGNORECASE)
            reCtrl          = re.compile("^\s*ctrl\s*:(.*)", re.I)
            reNoWait        = re.compile("[\s]*NOWAIT[\s]*:([\s\S]*)",re.IGNORECASE)
            reNo            = re.compile("^\s*NO\s*:(.*)", re.I)

            NewCommand  = command
            NewExpect = expect
            FunName     = None
            ListArg     = []
            DicArg      = {}
            IsCtrl      = False
            Retry       = '1'
            IsNoWait    = False
            IsNo        = False

            if wait.strip() =='0':
                IsNo    = True

            mTry = re.match(reRetry, command)
            if mTry:
                Retry       = mTry.group(1)
                if Retry =='':
                    Retry ='1'
                NewCommand  = mTry.group(2)

            mFun    = re.match(reFunction, NewCommand)
            from common import GetFunctionbyName
            FunName = 'singleStep'
            if mFun:
                from common import FunctionArgParser
                if mFun.group(1) !=None:
                    FunName = mFun.group(1)
                    ListArg, DicArg = FunctionArgParser(mFun.group(2))
                else:
                    FunName = mFun.group(3)
                    ListArg, DicArg = FunctionArgParser(mFun.group(4))
            else:

                mCtrl = re.match(reCtrl, NewCommand)
                if mCtrl:
                    IsCtrl=True
                    NewCommand = mCtrl.group(1)

                mNo = re.match(reNo, expect)
                if mNo:
                    IsNo    = True
                    NewExpect = mNo.group(1)
                mNoWait = re.match(reNoWait, NewExpect)
                if mNoWait:
                    IsNoWait=True
                    NewExpect = mNoWait.group(1)

                FunName = 'singleStep'
                ListArg = [NewCommand, NewExpect, wait, IsCtrl, IsNo, IsNoWait]

            return Retry, FunName, ListArg, DicArg

        def retry(casename, maxtry, funName, arg, kwarg, ):
            #maxtry+=1
            IsFail= True
            counter =0
            from common import GetFunctionbyName
            errormessage =''
            fun = GetFunctionbyName(self, funName)
            while(counter<maxtry):
                #maxtry-=1
                counter +=1
                if funName!='singleStep':
                    print('try %d/%d:%s'%(counter,maxtry, str(funName)))
                try:
                    if not fun:
                        print('FunName(%s) is NOT defined'%FunName)
                    fun(*arg, **kwarg)
                    IsFail=False
                    break
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    errormessage=e.__str__()#+'\n'+traceback.format_exc()
                    continue
            if IsFail:
                raise ValueError('tried %d time(s), failed in function(%s),\n\targ( %s)\n\tkwarg (%s)\n\nException:%s\n'%(counter, fun.func_name, str(arg), str(kwarg),errormessage))

        MaxTry, FunName, ListArg, DicArg = analyzeStep(CaseName,cmd, expect, wait)

        retry(CaseName, int(MaxTry), FunName, ListArg, DicArg)
    def run(self,*arglist):#name, strFormat='%s'):
        if len(arglist)>1:
            namelist = arglist[:-1]
            strFormat=arglist[-1]
            if strFormat.find("%")==-1:
                return
            newArgs = []
            for a in namelist:
                v = self.getValue(a)
                if type(v)!=type(''):
                    newArgs.append(str(v))
                else:
                    newArgs.append('"%s"'%v)
            evalstring = '"'+strFormat+"\"%("+ ','.join(newArgs)+")"
            newcmd = eval(evalstring,globals(),locals())
        else:
            newcmd= self.getValue(arglist[0])
        self.send(newcmd)
    def send(self, cmd, Ctrl=False, noWait=False):
        '''send a command to Software/Device, add a line end
        move idxSearch to the end of streamOut
        Ctrl, bool, default is False, if it's True, then send a key combination: Ctrl+first_char_of_cmd
        noWait, bool, defualt is False, means move searching index, otherwise doesn't move the searching index
        '''

        import os
        tmp =[]
        if noWait:
            pass
        else:
            self.lockStreamOut.acquire()
            self.idxSearch =self.streamOut.__len__() #move the Search window to the end of streamOut
            self.lockStreamOut.release()

        if self.loginDone:
            linesep=self.attribute['LINESEP']
        else:
            linesep=self.attribute['LOGIN_LINESEP']

        if Ctrl:
            ascii = ord(cmd[0]) & 0x1f
            ch = chr(ascii)
            self.write(ch)
        else:
            self.write(cmd+linesep)

        self.timestampCmd=time.time()
    def find(self, pattern, timeout = 1.0, flags=0x18, noPattern=False):
        '''find a given patten within given time(timeout),
        if pattern found, move idxSearch to index where is right after the pattern in streamOut
        return the content which matched the pattern
        if pattern doesn't find, raise a Execption
        otherwise return None
        flags: number, same as RE flags, default is re.MULTILINE|re.DOTALL 0x18
        noPattern: don't want to find the given pattern
        '''

        import re
        pat = re.compile(pattern,flags)
        if timeout<0.1:
            timeout =0.1
        interval = 0.1 #second
        import  time
        starttime = time.time()
        endtime = starttime+timeout+interval
        currentTime = starttime
        match=None
        buffer = ''
        findduration= time.strftime("::Find Duration: %Y-%m-%d %H:%M:%S --", time.localtime())

        while currentTime<endtime:
            buffer = self.streamOut[self.idxSearch:]
            match = re.search(pat ,buffer )

            if match:
                break
            time.sleep(interval)
            currentTime=time.time()
        findduration+= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+' %f'%timeout
        #print findduration
        if match:
            self.idxSearch += buffer.find(pattern)+match.group().__len__()+1
            if noPattern:
                delta = endtime-time.time()
                delta = int(delta+0.5)
                if delta>0:
                    interval=1
                    while delta:
                        delta-=interval
                        time.sleep(interval)
                raise  RuntimeError('pattern(%s) found with %f, buffer is:\n--buffer start--\n%s\n--buffer end here--\n'%(pattern,timeout, buffer))
            else:
                #self.idxSearch += buffer.find(pattern)+match.group().__len__()+1
                return match.group()
        else:
            if noPattern:
                self.idxSearch += buffer.__len__()+1
                return ''
            else:
                msg = 'pattern(%s) doesn\'t find with %f, buffer is:\n--buffer start--\n%s\n--buffer end here--\n'%(pattern,timeout, buffer)
                raise RuntimeError(msg)

    def login(self):
        self.loginDone=False
        login = 'login'.upper()
        import time
        time.sleep(0.5)
        self.show()
        if self.attribute.has_key(login):
            from common import csvfile2array
            seq = csvfile2array(self.attribute[login])
            lineno =0
            for singlestep in seq:
                lenStep = len(singlestep)
                if lenStep>2:
                    cmd, exp, wait  = singlestep[:3]
                elif lenStep ==2:
                    cmd, exp = singlestep
                    wait= 1
                elif lenStep ==1:
                    cmd = singlestep[0]
                    exp , wait= ['.*', 1]
                else:
                    continue
                lineno+=1
                self.stepCheck(self.name, lineno, cmd, exp, wait)
                self.show()
                #self.singleStep(cmd, exp, wait)
        self.loginDone=True
