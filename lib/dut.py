__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''
a term is an interface to interoperate with Software/Device Under Test/Used
provides:
1. command sent to software/device
2. show the output, just the updated recently
3. searching given pattern from a given range, e.g. right after last command entered
'''
import traceback, inspect
import time, datetime,os, sys
import re
import pprint,traceback
from common import GetFunctionbyName, FunctionArgParser,csvfile2array
from runner import gShareDataLock, gShareData
import threading
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

    fake_in:
                None/string of file name, is the flag to point out the file where the fake ouotput of this dut(the input of instance), default is None
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
    lockRelogin  =None
    lockStreamOut = None
    lockSearch = None
    remain_in_update_buffer=None
    max_session_read_error_counter= 1000
    __args = None
    __kwargs = None
    dry_run =False
    max_output_time_out= 10
    disconnected =False
    fake_in = None #fake_in is the flag to point out the file where the fake ouotput of this dut(the input of instance), default is None
    def set_max_time_out(self, max_counter=10):
        if int(max_counter)>0:
            self.max_output_time_out =int(max_counter)
        else:
            self.max_output_time_out = 0

    def closeSession(self):
        self.SessionAlive= False
        if self.logfile:
            try:
                self.logfile.flush()
                self.logfile.close()
            except Exception as e:
                print(e)
    def isAlive(self, cmd='\r\n'):

        if self.dry_run:
            return True
        else:
            isAlive = False
            self.info('try to test session is ok')
            tmpIndex = self.streamOut.__len__()
            for c in xrange(1, 120, 1):
                tmpIndex1= self.streamOut.__len__()
                if tmpIndex==tmpIndex1:
                    self.write(cmd)
                    self.sleep(1)
                else:
                    isAlive = True
                    break
            if isAlive:
                self.disconnected =False
                self.info('still alive')
            else:
                self.error('session disconnected')
                self.disconnected = True
            return  isAlive



    def ReadOutput(self):
        print('quit %s'%self.name)
        raise NotImplementedError


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
        try:
            self.errorLines =   ''
            try:
                self.name       =   name
            except Exception as e:
                pass
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
                self.attribute['ERROR_PATTERN']='fail|error| err|\serr |\serr:|wrong'


            if self.attribute.get("LOGIN_LINESEP"):
                #self.SessionAlive=True
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
            self.lockStreamOut = threading.Lock()
            self.lockRelogin = threading.Lock()
            self.lockSearch =  threading.Lock()
            self.streamOut=''
            self.remain_in_update_buffer=''
            self.loginDone=False
            if self.attribute.get('FAKE_IN'):
                self.fake_in = self.attribute['FAKE_IN']
                if  not os.path.exists(self.fake_in):
                    pwd = os.getcwd()
                    raise Exception("FAKE_IN is given, current work dir is %s, but it's not a existed file: %s"%(pwd, self.fake_in))
                else:
                    path = os.path.dirname(self.fake_in)
                    file_name = os.path.basename(self.fake_in)
                    self.fake_in = self.load(file_name, path)
                    self.fake_in = self.fake_in[::-1]
                    print(self.fake_in)
        except Exception as e:
            self.SessionAlive =False
            raise e
    def appendValue(self,name,value):
       # from runner import gShareDataLock, gShareData
        gShareDataLock.acquire()
        try:
            if gShareData.has_key(name):
                gShareData[name].append(value)
            else:
                gShareData[name]=value
        except Exception as e:
            self.setFail(str(e)+'appendValue(name=%s)\n'%name+traceback.format_exc())
            print(e)
        gShareDataLock.release()
        return gShareData[name]
    def updateValue(self, name, value):
        #from runner import gShareDataLock, gShareData
        gShareDataLock.acquire()

        try:
            if gShareData.has_key(name):
                gShareData[name].update(value)
            else:
                gShareData[name]=value
        except Exception as e:
            self.setFail(str(e)+'updateValue(name=%s)\n'%name+traceback.format_exc())
            print(e)
        gShareDataLock.release()
        return gShareData[name]
    def setValue(self, name, value):
        #from runner import gShareDataLock, gShareData
        gShareDataLock.acquire()
        try:
            gShareData[name]=value
        except Exception as e:
            self.setFail(str(e)+'\n'+traceback.format_exc())
            print(e)
        gShareDataLock.release()
        return gShareData[name]
    def getValue(self, name):

        try:
            if gShareData.has_key(name):
                tmpvalue = gShareData[name]
                print(pprint.pformat(tmpvalue))
                return  tmpvalue
            else:
                print(pprint.pformat(None))
                return  None
        except Exception as e:
            print('dump of ShareData')
            print(pprint.pformat(gShareData))
            print(e)
            print('%s is not in shareData'%(str(name)))
            self.setFail(str(e)+'getValue(name=%s\n'%name+traceback.format_exc())
            return  None

    def checkLine(self,str):
        if not self.fErrorPatternCheck:
            return str

        lines = str.split('\n')

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

        lines = str.split('\n')
        rePat = re.compile(self.attribute['ERROR_PATTERN'], re.IGNORECASE)
        newLines =[]
        for line in lines:
            if re.search(rePat, line):
                try:
                    from colorama import Fore, Back, Style
                    if line.endswith('\r'):
                       line = '\033[1;31;46m'+Fore.RED+Back.CYAN + line[:-1] +'\033[0m'+'\r' #Style.RESET_ALL
                    else:
                       line = '\033[1;31;46m'+Fore.RED+Back.CYAN +line +'\033[0m'#Style.RESET_ALL
                except Exception as e:
                    return str

            newLines.append(line)
        return '\n'.join(newLines)


    def openLogfile(self, logpath):
        '''
        logpath, a folder path, where log to be found
        '''

        if not logpath:
            logpath = os.getcwd()
        log = os.path.abspath(logpath)
        log= '%s%s%s'%(log,os.path.sep,'%s.log'%self.name)

        if self.logfile:
            tmplog = self.logfile
            self.logfile=None
            max_counter=5
            counter= 0
            while max_counter>counter:
                counter+=1
                try:
                    tmplog.close()
                    break
                except Exception as e:
                    time.sleep(1)
                    pass
            self.logger.info('%s streamOut size is %d, to be reset to 0'%(self.name, len(self.streamOut)))
            #self.lockStreamOut.release()
            #self.lockStreamOut.acquire()
            self.streamOut   =  ''
            #self.lockStreamOut.release()
            self.logger.info('%s is reset to 0'%(self.name))
            self.move_search_window() #self.idxSearch   =   0
            self.idxUpdate   =   0
        self.logfile = open(log, "wb")


    def show(self):
        '''return the delta of streamOut from last call of function Print,
        and move idxUpdate to end of streamOut'''
        if self.streamOut==None:
            raise NotImplementedError('please implement function show in your class')
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        if result==self.remain_in_update_buffer:
            self.remain_in_update_buffer=''
            self.idxUpdate= newIndex+1
        else:
            last_new_line = result.rfind('\n')
            if last_new_line!=-1:
                result = result[0:last_new_line+1]
                self.idxUpdate= self.idxUpdate+last_new_line+1#newIndex
                self.remain_in_update_buffer= self.streamOut[self.idxUpdate  :]
            else:
                self.remain_in_update_buffer=result
        if result!='':
            #import sys
            #sys.stdout.write('\t%s'%(result.replace('\n', '\n\t')))
            result= self.colorString(result)
            print('%s'%(result.replace('\n', '\n\t').replace('\r\n','\n'))),
        return result


        #raise NotImplementedError('please implement function show in your class')
    def write(self, buffer=''):
        self.timestampCmd= time.time()

    def write2file(self, data, filename=None):
        '''write the data to a given file
        if filename is None, the create a term_name.txt under current path of term logfile
        '''

        if filename:
            f =open(filename, 'ab+')
            f.write(data)
            f.flush()
            f.close()
        else:
            self.info(data)

    def formatMsg(self, *msg):
        now =datetime.datetime.now()
        new_msg = ','.join([pprint.pformat(x,indent=2,width=256) for x in msg])
        msg = '%s\t%s\t%s'%(now.isoformat().replace("T", ' '), self.name, new_msg)
        print(msg)
        return msg
    def info(self, *msg):
        '''
        add info message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.info(msg)

    def error(self, *msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.error(msg)
    def debug(self, *msg):
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
        wait = float(wait)
        if self.dry_run:
            return
        if wait>10:
            interval =0.1
            counter = int(wait/interval)
            while counter>0.1 :
                time.sleep(interval)
                counter-=1
                if int(counter)%(int(10/interval))==0:
                    sys.stdout.write('.')
        else:
            time.sleep(float(wait))

    def singleStep(self, cmd, expect, wait, ctrl=False, noPatternFlag=False, noWait=False):
        self.show()
        self.send(cmd, ctrl, noWait)
        self.show()
        #import time
        #time.sleep(0.01)
        output = self.find(expect, float(wait), noPattern=noPatternFlag)
        self.show()
        return output
#       if not noPattern:
#           self.find(expect, float(wait), noPattern=noPattern)
#           self.show()
#        else:
#            self.find(expect, float(wait), noPattern=noPattern)
#            self.show()
            #raise RuntimeError('found pattern(%s) within %s'%(expect,wait))

    def step(self, cmd, expect =None,wait=None ):
        if expect is None:
            expect ='.*'
        if wait is None:
            wait = 30

        return  self.stepCheck('tc',0,cmd,expect,str(int(wait)))
    def convert_args(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        return self.__args, self.__kwargs
    def stepCheck(self, CaseName, lineNo, cmd, expect, wait):
        if self.dry_run:
            return 'cmd %s, expect %s'%(str(cmd), str(expect))
        if type(wait)!=type(''):
            wait = str(wait)
        def analyzeStep(self, casename, command, expect, wait):
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
            FunName = 'singleStep'
            if mFun:

                if mFun.group(1) !=None:
                    FunName = mFun.group(1)
                    cmd  = 'self.convert_args(%s)'%(mFun.group(2))
                    ListArg, DicArg = eval(cmd, globals(),locals())
                    #ListArg, DicArg = FunctionArgParser(mFun.group(2))
                else:
                    FunName = mFun.group(3)
                    cmd  = 'self.convert_args(%s)'%(mFun.group(4))
                    ListArg, DicArg = eval(cmd, globals(),locals())
                    #ListArg, DicArg = FunctionArgParser(mFun.group(4))
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
            counter =1
            response =None
            errormessage =''
            fun = GetFunctionbyName(self, funName)
            last_dump =None
            last_execption =None
            while(counter<maxtry+1):
                self.logger.info('try %d/%d:%s'%(counter,maxtry, str(funName)))
                counter +=1
                try:
                    if not fun:
                        self.error('FunName(%s) is NOT defined'%FunName)
                    self.info('function name:', fun)
                    self.info('args:', arg)
                    self.info('kwarg', kwarg)
                    response = fun(*arg, **kwarg)

                    IsFail=False
                    break
                except Exception as e:
                    last_execption =e
                    last_dump = traceback.format_exc()
                    errormessage=e.__str__()#+'\n'+traceback.format_exc()
                    continue
            if last_dump is not None:
                self.error(last_dump)
                print(last_dump)
            if IsFail:
                raise last_execption#ValueError('tried %d time(s), failed in function(%s),\n\targ( %s)\n\tkwarg (%s)\n\nException:%s\n'%(counter, fun.func_name, str(arg), str(kwarg),errormessage))
            return  response
        MaxTry, FunName, ListArg, DicArg = analyzeStep(self, CaseName,cmd, expect, wait)

        return retry(CaseName, int(MaxTry), FunName, ListArg, DicArg)
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
        if self.dry_run:
            return
        tmp =[]

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

        if noWait:
            pass
        else:
            self.move_search_window()
        self.timestampCmd=time.time()
    def move_search_window(self, step=None):
        self.lockSearch.acquire()
        if not step:
            self.idxSearch =self.streamOut.__len__()# +1# #move the Search window to the end of streamOut
        else:
            self.idxSearch +=step
        self.lockSearch.release()
    def get_search_buffer(self):
        self.lockSearch.acquire()
        buf = self.streamOut[self.idxSearch:]
        self.lockSearch.release()
        return buf
    def find(self, pattern, timeout = 1.0, flags=0x18, noPattern=False):
        '''find a given patten within given time(timeout),
        if pattern found, move idxSearch to index where is right after the pattern in streamOut
        return the content which matched the pattern
        if pattern doesn't find, raise a Execption
        otherwise return None
        flags: number, same as RE flags, default is re.MULTILINE|re.DOTALL 0x18
        noPattern: don't want to find the given pattern
        '''
        if self.dry_run:
            return 'fount it:%s'%(pattern)
        flag =False
        if pattern=='.+CalixE7>':
            flag=True

        response = ''
        pat = re.compile(pattern,flags)
        if timeout<0.1:
            timeout =0.1
        interval = 0.1 #second
        starttime = time.time()
        endtime = starttime+timeout+interval
        currentTime = starttime
        match=None
        buffer = ''
        findduration= time.strftime("::Find Duration: %Y-%m-%d %H:%M:%S --", time.localtime())
        tmp_idx_search=self.idxSearch
        while currentTime<endtime:
            buffer = self.streamOut[tmp_idx_search:]
            try:
                match = re.search(pat ,buffer )
                response = buffer
            except RuntimeError as e :
                match = None

            if match:
                break
            time.sleep(interval)
            currentTime=time.time()
        findduration+= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+' %f'%timeout
        #print findduration
        if match:
            found = match.group()
            self.move_search_window(buffer.find(found)+found.__len__())
            if flag and found.find('1/v1 ')==-1:
                pass
            tmp = found.replace('\n','\n****')
            #print('-'*30+'\n')
            #print('===='+buffer[0:buffer.find(found)].replace('\n','\n===='))
            #print('****'+tmp)
            #print('===='+buffer[buffer.find(found)+1+buffer.__len__():].replace('\n','\n===='))
            #print('\n'+'-'*30)
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
                self.move_search_window(buffer.__len__())
                return buffer
            else:
                msg = '%s:pattern(%s) doesn\'t find with %f, buffer is:\n--buffer start--\n%s\n--buffer end here--\n'%(self.name,pattern,timeout, buffer)
                raise RuntimeError(msg)
        return response

    def login(self):

        print('loginDone', self.loginDone)
        if self.is_simulation():
            self.loginDone=True
            return
        #self.lockRelogin.acquire()
        login = 'login'.upper()
        time.sleep(0.5)
        self.show()
        if self.attribute.has_key(login) and self.loginDone==False:
            seq = csvfile2array(self.attribute[login])
            lineno =0
            for singlestep in seq:
                if self.loginDone:
                    break
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
                try:
                    self.stepCheck(self.name, lineno, cmd, exp, wait)
                except Exception as e :
                    if self.loginDone:
                        break
                    else:
                        #self.lockRelogin.release()
                        raise e
                self.show()
                #self.singleStep(cmd, exp, wait)
        self.loginDone=True
        #self.lockRelogin.release()
    def setFail(self, msg):
        self.FailFlag=True
        self.error(msg)
        if self.ErrorMessage:
            self.ErrorMessage+=msg+'\n'
        else:
            if type(msg)==type(''):
                pass
            else:
                msg= pprint.pformat(msg)
            msg= re.sub('\\\\n','\n', msg)
            msg= re.sub('\\\\r','\r', msg)
            msg= re.sub('\\\\t','\t', msg)

            self.ErrorMessage=msg
        log_dir= os.path.dirname(self.logfile.name)
        with open('%s/case_error.txt'%log_dir, 'a+') as ef:
            msg = self.formatMsg(msg)
            ef.write(msg+'\n')
    def relogin(self):
         self.loginDone=False

    def save(self, obj, file_name='tmp.txt', path =None):
        import json
        if path:
            file_name = path+'/'+file_name
        else:
            file_name = os.path.dirname(self.logfile.name)+'/'+file_name

        with open(file_name, 'w+') as data_file:
            json.dump(obj, data_file)
    def load(self, file_name='tmp.txt', path = None):
        import json
        if path:
            file_name = path+'/'+file_name
        else:
            file_name = os.path.dirname(self.logfile.name)+'/'+file_name

        with open(file_name, 'r') as data_file:
            data = json.load(data_file)
        return  data
    def is_simulation(self):
        is_simulation = False
        if self.fake_in not in [None]:
            is_simulation = True
        return  is_simulation