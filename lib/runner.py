__author__ = 'Sean Yu'
'''created @2015/9/29''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])

sys.path.append(os.path.sep.join([pardir,'dut']))
import os
def logAction(fun):
    def inner(*arg, **kwargs):
        try:
            msg ='Called function: %s'%(fun.func_name)
            print(msg)
            response = fun(*arg, **kwargs)
            return  response
        except Exception as e:
            arglist = list(arg)
            argstring =''
            for a in arglist:
                argstring +='\n\t\t'+str(a)
            kwargstring = ''
            for k,v in kwargs:
                kwargstring += '\n\t\t%s: %s'%(str(k),str(v))
            msg ='*logAction dump:\n\tFunction Name: \t\t%s\n\tArguments: \t\t%s\n\tKeyword Arguments: \t\t%s'%(fun.func_name, argstring, kwargstring)
            from common import DumpStack
            msg =msg +'\n-------------------------------------------------------------------------------'+DumpStack(e)
            msg = '\n*********************************ERROR DUMP************************************\n'+msg.replace('\n', '\n*')+'*********************************EREOR END*************************************\n\n'
            print(msg)
            import os
            with open(os.getcwd()+'/error.txt','a+') as errorfile:
                errorfile.write(msg)
            raise Exception(msg)
        return inner
    return inner
@logAction
def createLogger(name, logpath='./'):
    #create  a unique folder for case, and logfile for case
    if not os.path.exists(logpath):
        os.mkdir(logpath)
    import logging
    logfile = logpath+"/%s.log"%(name)
    logger = logging.Logger(name,logging.DEBUG)
    hdrlog = logging.FileHandler(logfile)
    hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
    logger.addHandler(hdrlog )
    return logger
@logAction
def createLogDir(name,logpath='./'):
    import re, datetime
    fullname = name[:80]
    removelist = '\-_.'
    pat = r'[^\w'+removelist+']'
    name = re.sub(pat, '', fullname)
    tm = datetime.datetime.now().isoformat('_')
    tm =  re.sub(pat, '', tm)
    name = name+'-'+tm
    logpath = logpath+'/'+ name
    if not os.path.exists(logpath):
        os.mkdir(logpath)
    return logpath

@logAction
def openDutLogfile(duts, logpath, logger):
    for dut_name in duts.keys():
        duts[dut_name].openLogfile(logpath)
        logger.info("DUT %s redirected to case folder"%dut_name)

@logAction
def initDUT(errormessage ,bench, dutnames, logger=None, casepath='./'):
    dictDUTs={}
    #global  gInitErrorMessage

    def connect2dut(InitErrorMessage , dutname, dut_attr, logger=None,path='./'):
        msg = ''
        try:
            import os
            if dut_attr["SUT"].strip() =='':
                if os.name!='nt':
                    raise  ImportError('need implment default session for non-NT')#sutattr['SUT'] ='Session'
                else:
                    dut_attr['SUT'] ='winTelnet'

            classname = dut_attr["SUT"]
            ModuleName = __import__(classname)
            ClassName = ModuleName.__getattribute__(classname)
            ses= ClassName(dutname, dut_attr,logger=logger ,logpath = path)
            ses.login()
            dictDUTs[dutname]=ses
            return  ses
        except Exception as e:
            msg = 'can\'t init dut(%s)\n%s\n'%(dutname, e.__str__())
            InitErrorMessage.append(msg)
            raise ValueError(msg)
    import threading
    dutobjs=[]

    for dutname in dutnames:
        th = threading.Thread(target= connect2dut, args =[errormessage, dutname, bench[dutname],logger, casepath])
        dutobjs.append(th)
    for th in dutobjs:
        th.start()

    for th in dutobjs:
        th.join()
    if len(errormessage)!=0 or (len(dictDUTs)!= len(dutnames)):
        raise ValueError('\n\t'.join(errormessage))
    return  dictDUTs


CASE_MODE = set(['full', 'f',
                 'setup', 's',
                 'run', 'r',
                 'tear', 't', 'teardown',
                 'nosetup', 'ns',
                 'norun', 'nr',
                 'notear', 'noteardown', 'nt',
                 ])
@logAction
def run(casename,duts, seqs ,mode, logger):
        global  CASE_MODE
        import datetime
        def analyzeStep(casename, dut, commnad, expect, wait):
            funName = dut.defaultFunction
        if mode not in CASE_MODE:
            raise ValueError('case mode is wrong, should be one of %s'%(str(CASE_MODE)))

        def runSegment( casename, mode, modeset, duts, seq, segName, logger):

            if mode in modeset:#{'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'}:
                segment=segName#'setup'
                stepindex= 1
                for dut, cmd,expect , due, lineno in seq:#self.seqSetup:
                    session = duts[dut]
                    stepinfo = """###############################################################################
# %s
# Case: %s, LineNo:%d, %s.%d
# DUT(%s) Action(%s),Exp(%s),Wait(%s)
###############################################################################"""%(datetime.datetime.now().isoformat('_'),casename,lineno,segment, stepindex,
                         dut,cmd, expect, due)
                    print(stepinfo)

                    session.stepCheck(casename, lineno, cmd, expect, due)
                    stepindex+=1


        modeset =[
                    {'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'},
                    {'full', 'run', 'nosetup', 'notear', 'r', 'ns', 'nt', 'f'},
                    {'full', 'tear', 'norun', 'nosetup', 't', 'nr', 'ns', 'f'}

                  ]
        seqlist =[seqs[0],
                  seqs[1],
                  seqs[2]
                  ]
        segNamelist =['setup', 'run', 'teardown']
        index = 0
        totalseg = len(seqlist)
        while index <totalseg:
            logger.info('starting segment:%d'%index)
            runSegment(casename, mode, modeset[index], duts,seqlist[index],  segNamelist[index], logger)
            index +=1


        caseFailFlag =False
        caseErrorMessage = ''
        for dutname in duts.keys():
            if duts[dutname].FailFlag:
                caseFailFlag=True
                caseErrorMessage+=duts[dutname].ErrorMessage+'\n'


        return caseFailFlag,caseErrorMessage


def case_runner(casename, dictDUTs, case_seq, mode='full', logger =None):
    m =mode
    if mode :
        m =str(mode).lower()
    caseFail, errorMessage = run(casename, dictDUTs, case_seq, m, logger)
    #print(response)
    return  caseFail, errorMessage

def run_case_in_suite(casename, currentBenchfile, currentBenchinfo,logger, stop_at_fail,logdir, cmd):
    import re
    patDash  = re.compile('\s*(python |python[\d.]+ |python.exe |)\s* cr.py\s+(.+)\s*', re.DOTALL|re.IGNORECASE)
    m =  re.match(patDash, cmd)
    returncode = 0
    if m:
        argstring = m.group(2)
        import shlex
        lstArg = shlex.split(argstring)
        #0-case.csv, 1-bench, 2-mode, 4...-2- args
        casefile = lstArg[0]
        benchfile = lstArg[1]
        mode       = lstArg[2]
        args= lstArg[3:]
        newBenchInfo =None
        if currentBenchfile!=benchfile:
            from common import bench2dict
            bench =bench2dict(benchfile)
            releaseDUTs()
        else:
            bench = currentBenchinfo
        from Parser import  caseParser

        cs = caseParser(casename, mode, logdir)
        sdut, lvar, lsetup, lrun, ltear =cs.load(casefile)
        ldut = list(sdut)
        errormessage =[]
        duts= initDUT(errormessage,bench,ldut,logger, logdir)
        seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]
        returncode, caseErrorMessage= case_runner(casename,duts,seq, mode)
    else:
        import subprocess
        pp =None
        if cmd.startswith('\w+.py') :
            exe_cmd ='python '+ cmd+" "+logdir
            pp = subprocess.Popen(args = exe_cmd ,shell =True)

        import time
        ChildRuning = True
        first =True
        while ChildRuning:
            if pp.poll() is None:
                interval = 1
                if first:
                    first=False
                time.sleep(interval)
            else:
                ChildRuning = False

        returncode = pp.returncode


def loop(counter, casename, currentBenchfile, currentBenchinfo,logger,stop_at_fail, cmd):

    i = 0
    flagFail = False
    msgError = ''
    while i <counter:
        try:
            i +=1
            import shlex
            cmdlist = shlex.split(cmd,comments=True)
            run_case_in_suite(*cmdlist)
        except:
            flagFail=True
            msgError +='%s: failed @%d of %d'%(cmd, i,counter)
            if stop_at_fail:
                break

    return  flagFail, msgError



def releaseDUTs(duts, logger):
    if duts.keys()==None:
        return
    for name in duts.keys():
        dut = duts[name]
        logger.info('releasing dut: %s'%name)
        if dut :
            dut.SessionAlive=False
            if dut.logfile:
                dut.logfile.flush()
errorlogger = None
def concurrent(logpath, cmdConcurrent, report):
    import Queue,threading
    qResult=Queue.Queue()

    lstThread=[]
    def runCase(index, totalThread, LineNo,indexInSuite,failAction,logpath,cmd,qResult):
        #make dir
        caseStartTime=time.time()
        logdir = createLogDir(str(index), logpath)
        returncode, errormessage, benchfile,bench, dut_pool =run1case(cmd,'',None,None, logdir)
        caseEndTime=time.time()
        releaseDUTs(dut_pool)
        if returncode:
            #newRecord = [indexInSuite,failAction,cmd, errormessage,logdir, LineNo]
            qResult.put([LineNo,indexInSuite, failAction,index, 'thread %d/%d %s: '%(index,totalThread, logdir)+errormessage+'\n', logpath, caseStartTime,caseEndTime, cmd])
        else:
            qResult.put([LineNo,indexInSuite, failAction,index, None, logpath,caseStartTime,caseEndTime, cmd])

    lstThread=[]
    for line in cmdConcurrent:
        [fork, index, totalThread, LineNo,indexInSuite,failAction,logpath,cmd]= line
        logdir = createLogDir(str(indexInSuite), logpath)
        for i in range(0,fork):
            key = '%d-%d'%(LineNo,i)
            t = threading.Thread(target=runCase, args=[i,fork,LineNo,indexInSuite,failAction,logdir,cmd, qResult])
            lstThread.append(t)

    for t in lstThread:
        t.start()

    for t in lstThread:
        t.join()
    dictResult={}
    breakFlag =False
    caseFail=0
    casePass =0
    caseTotal=0
    lstFailCase=[]
    while not qResult.empty():
        LineNo,indexInSuite, failAction,index, errormessage, logdir ,startTime, endTime, cmd= qResult.get()
        if dictResult.has_key(LineNo):
            if failAction=='break' and errormessage!=None:
                breakFlag=True
            [index,caseResult,cmd, oldErrormessage,logdir, LineNo, duration, oldStartTime, oldEndTime, cmd] = dictResult[LineNo]
            if caseResult=='PASS' and errormessage!=None:
                caseResult='FAIL'
            newStartTime= min(oldStartTime,startTime)
            newEndTime =max(oldEndTime,endTime)
            dictResult[LineNo]=[index,caseResult,cmd, oldErrormessage+errormessage,logdir, LineNo, newEndTime-newStartTime,newStartTime,newEndTime]
        else:
            caseResult='FAIL'
            caseTotal+=1
            if errormessage==None:
                caseResult='PASS'
                casePass+=1
            else:
                caseFail+=1
                lstFailCase.append([concurrent, cmd])
                #NewRecord = [index-1,caseResult,caseline[2][1], errormessage,'../'+logdir, LineNo,ExecutionDuration,caseStartTime,caseEndTime ]
            dictResult[LineNo] = [indexInSuite,caseResult,cmd, errormessage,logdir, LineNo, endTime-startTime,startTime,endTime]
    keys=sorted(dictResult.keys())

    for k in keys:
        newRecord = dictResult[k]
        print(newRecord)
        report.append(newRecord)

    return caseTotal, casePass, caseFail, lstFailCase