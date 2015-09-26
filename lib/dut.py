__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''
a term is an interface to interoperate with Software/Device Under Test/Used
provides:
1. command sent to software/device
2. show the output, just the updated recently
3. searching given pattern from a given range, e.g. right after last command entered
'''

class dut(object):
    '''
    streamOut:  string of Software/Device's output, __init__ will set it to ''
    idxSearch:  number, based on 0, default is 0, it's the index of streamOut, and point to where to find the pattern
                right after this index.
                function Send(will move it to the end of streamOut
                function Find will move idxSearch to index where is right after the pattern in streamOut
    idxUpdate:  number, 0-based, default is 0, point to index of streamOut, when the last call of function Print
                function Prind will move it to the end of streamOut
    attr     :  the attributes gave by caller
    logfile  :  the log file, which named as name.log
    Connect2SUTDone:
                bool, initial value is False, means didn't complete the process of Device log-in, after log-in, it should be set to True
    attribute   :
                dict, initial is None, and assigned in __init__ as {} or set to the given variable attr
    SessionAlive:
                bool, initial is True, when session is closing, set it to False
    '''
    streamOut   =   None
    idxSearch   =   0
    idxUpdate   =   0
    attr        =   None
    logfile     =   None
    Connect2DUTDone = False
    attribute   =   None
    SessionAlive =  True
    name         =  None #the term name, string
    logger       =  None #parent logger, passed to term, default is logger,no logger needed
    defaultHandler= 'stepCheck' # the default handler for each action in sequences e.g. setup, run ,teardown

    def __del__(self):
        self.SessionAlive=False


    def __init__(self, name, attr =None,logger=None, logpath= None):
        '''
        initializing the term
        name:       string, the term's name
        attr:       a dict, the attributes of term
        logger:     a logger instance, allow this term pass message to parent object
        logpath:    string, the path of the log file for this ter
        '''
        self.name       =   name
        self.logger     =   logger
        if attr:
            self.attribute =attr
        else:
            self.attribute = {}
        self.openLogfile(logpath)
    def openLogfile(self, logpath):
        '''
        logpath, a folder path, where log to be find
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
        self.logfile = open(log, "wb")


    def send(self, cmd):
        '''send a command to Software/Device, add a line end
        move idxSearch to the end of streamOut
        '''
        pass
    def find(self, pattern, timeout = 1.0):
        '''find a given patten within given time(timeout)
        if pattern found, move idxSearch to index where is right after the pattern in streamOut
        return the content which matched the pattern
        otherwise return None
        '''
        pass
    def show(self):
        '''return the delta of streamOut from last call of function Print,
        and move idxUpdate to end of streamOut'''
        pass
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



    def stepCheck(self, cmd, expect, wait):
        def  analyzeStep(command, expect, wait):
            import re
            reRetry         = re.compile("^\s*try\s+([0-9]+)\s*:(.*)", re.I)
            reFunction      = re.compile('\s*FUN\s*:\s*(.+?)\s*\(\s*(.*)\s*\)|\s*(.+?)\s*\(\s*(.*)\s*\)\s*$',re.IGNORECASE)
            reCtrl          = re.compile("^\s*ctrl\s*:(.*)", re.I)
            reNoWait        = re.compile("[\s]*NOWAIT[\s]*:([\s\S]*)",re.IGNORECASE)
            reNo            = re.compile("^\s*NO\s*:(.*)", re.I)

            NewCommand  = command
            NewExpect = expect
            FunName     = None
            ListArg     = None
            DicArg      = None
            IsCtrl      = False
            Retry       = 0
            IsNoWait    = False
            IsNo        = False

            if wait.strip() =='0':
                IsNo    = True

            mTry = re.match(reRetry, command)
            if mTry:
                Retry       = mTry.group(1)
                NewCommand  = mTry.group(2)

            mFun    = re.match(reFunction, NewCommand)
            from common import GetFunctionbyName
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

            return NewCommand, NewExpect, wait,  FunName, ListArg, DicArg, IsCtrl, IsNo, IsNoWait

        def singleStep(self, cmd, expect, wait):
            self.send(cmd)
            self.find(expect, wait)
        def noPattern(exp, wait):
            try:
                self.find(exp, wait)
            except Exception as e:
                raise ValueError('found pattern(%s) within %s'%(exp, wait))
        def retry(maxtry, fun, arg, kwarg):
            maxtry+=1
            IsFail= True
            counter =0
            while(maxtry):
                maxtry-=1
                counter +=1
                try:
                    fun(arg, kwarg)
                    IsFail=False
                    break
                except Exception as e:
                    continue
            if IsFail:
                raise ValueError('tried %d time, failed in function(%s), arg( %s) kwarg (%s)'%(counter, str(fun), str(arg), str(kwarg)))


