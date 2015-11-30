__author__ = 'Sean Yu'
'''created @2015/9/29''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
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
            import pprint as pp
            argstring = pp.pformat(arglist)
            #for a in arglist:
            #    argstring +='\n\t\t'+str(a)
            kwargstring = ''
            kwargstring = pp.pformat(kwargs)
            #for k,v in kwargs:
            #    kwargstring += '\n\t\t%s: %s'%(str(k),str(v))
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
import threading
gPathLocker = threading.Lock()
@logAction
def createLogDir(name,logpath='./'):
    global  gPathLocker
    gPathLocker.acquire()
    import os
    old_logpath=logpath
    def listDir(path):
        folders = []
        while 1:
            path, folder = os.path.split(path)

            if folder != "":
                folders.insert(0, folder)
            else:
                if path != "":
                    folders.insert(0,path)
                break
        return  folders
    old_cwd= os.getcwd()
    old_cwd = listDir(old_cwd)
    logpath = listDir(os.path.abspath(logpath))


    import re, datetime
    fullname = name[:60]
    removelist = '\-_.'
    pat = r'[^\w'+removelist+']'
    name = re.sub(pat, '', fullname)
    tm = datetime.datetime.now().isoformat('_')
    tm =  re.sub(pat, '', tm)
    fullname = name+'-'+tm
    for dir in logpath:
        print(os.getcwd())
        if os.path.exists(dir):
            print(os.getcwd())
            os.chdir(dir)
            print(os.getcwd())
        else:
            errormsg= 'dir: %s does not exist, please create it first'%dir
            for dir in old_cwd:
                os.chdir(dir)
                print(os.getcwd())
            print(errormsg)
            gPathLocker.release()
            raise Exception(errormsg)

    if not os.path.exists(fullname):
        print(len(fullname))
        if len(fullname)>30:
            pass
        os.mkdir(fullname)
    logpath.append(fullname)
    print("old_cwd:",old_cwd)
    for dir in old_cwd:
        os.chdir(dir)
        print(os.getcwd())
    gPathLocker.release()
    return old_logpath+'/'+fullname

@logAction
def openDutLogfile(duts, logpath, logger):
    for dut_name in duts.keys():
        duts[dut_name].openLogfile(logpath)
        logger.info("DUT %s redirected to case folder"%dut_name)

@logAction
def initDUT(errormessage ,bench, dutnames, logger=None, casepath='./'):
    dictDUTs={}

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
            msg = '\ncan\'t init dut(%s)\n%s\n'%(dutname, e.__str__())
            InitErrorMessage+=msg
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

        cs = caseParser(casename, mode, logdir, logger)
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
    if duts==None or duts.keys()==None:
        return
    for name in duts.keys():
        dut = duts[name]
        logger.info('releasing dut: %s'%name)
        if dut :
            dut.SessionAlive=False
            if dut.logfile:
                dut.logfile.flush()
errorlogger = None
def concurrent(startIndex, logpath, cmdConcurrent, report, suiteLogger):
    import Queue,threading
    qResult=Queue.Queue()

    lstThread=[]
    import time,re
    def runCase(index, totalThread, indexInSuite,LineNo,allFailIsFail,failAction,logpath,casename,suitelogger, cmd,qResult):
        LineNo =int(LineNo)
        indexInSuite=int(indexInSuite)
        caseStartTime=time.time()
        logdir = createLogDir(str(index+1)+"-"+ re.sub('[^\w\-._]','-',cmd)[:80], logpath)
        returncode, errormessage, benchfile,bench, dut_pool =run1case(casename, cmd,'',None,None, logdir, suiteLogger)
        caseEndTime=time.time()
        releaseDUTs(dut_pool, suiteLogger)
        if returncode:
            qResult.put(['FAIL', LineNo,indexInSuite, failAction,index, 'thread %d/%d %s: '%(index+1,totalThread, logdir)+errormessage+'\n', '../'+logpath, caseStartTime,caseEndTime, cmd,allFailIsFail])
        else:
            qResult.put(['PASS', LineNo,indexInSuite, failAction,index, '','../'+logpath,caseStartTime,caseEndTime, cmd, allFailIsFail])

    lstThread=[]
    indexInSuite =startIndex
    for line in cmdConcurrent:
        [fork, LineNo,failAction,action, cmd, allFailIsFail]= line
        logdir = createLogDir(str(indexInSuite)[:80], logpath)#logpath #logpath #
        for i in range(0,fork):
            #key = '%d-%d'%(LineNo,i)
            casename ='%d-%s'%(indexInSuite, re.sub('[^\w\-_.]','-',cmd[:80]))
            t = threading.Thread(target=runCase, args=[i,fork, indexInSuite,LineNo,allFailIsFail,failAction,logdir,casename, suiteLogger,cmd, qResult])
            lstThread.append(t)
        indexInSuite+=1

    for t in lstThread:
        t.start()

    for t in lstThread:
        t.join()
    dictResult={}
    breakFlag =False
    while not qResult.empty():
        caseResult, LineNo,indexInSuite, failAction,index, errormessage, logdir ,startTime, endTime, cmd, allFailIsFail= qResult.get()
        if dictResult.has_key(LineNo):

            #True, LineNo,indexInSuite, failAction,index, 'thread %d/%d %s: '%(index,totalThread, logdir)+errormessage+'\n', logpath, caseStartTime,caseEndTime, cmd
            [ indexInSuite,oldCaseResult, cmd,oldErrormessage, logdir, LineNo,duration, oldStartTime, oldEndTime, failAction] = dictResult[LineNo]
            if allFailIsFail:
                if caseResult=='PASS' or oldCaseResult=='PASS':
                    caseResult='PASS'
                else:
                    caseResult='FAIL'
            else:
                if caseResult=='FAIL' or oldCaseResult=='FAIL':
                    caseResult='FAIL'

            newStartTime= min(oldStartTime,startTime)
            newEndTime =max(oldEndTime,endTime)
            if oldErrormessage:
                if errormessage:
                    errormessage=oldErrormessage+'\n'+errormessage
                else:
                    errormessage=oldErrormessage
            dictResult[LineNo]=[indexInSuite,caseResult,cmd, errormessage,logdir, LineNo, newEndTime-newStartTime,newStartTime,newEndTime, failAction]
        else:
            dictResult[int(LineNo)] = [indexInSuite,caseResult,cmd, errormessage,logdir, LineNo, endTime-startTime,startTime,endTime, failAction]
    keys=sorted(dictResult.keys())


    caseFail=0
    casePass =0
    caseTotal=0
    lstFailCase=[]



    for k in keys:
        newRecord = dictResult[k]
        caseResult=newRecord[1]
        cmd = newRecord[2]
        failAction= newRecord[9]
        caseTotal+=1
        if caseResult=='PASS':
            casePass+=1
        else:
            caseFail+=1
            if failAction=='break':
                breakFlag=True
            lstFailCase.append([concurrent, cmd])
        print(newRecord)
        report.append(newRecord[:-1])

    return caseTotal, casePass, caseFail, report, lstFailCase, breakFlag

def run1case(casename, cmd,benchfile, benchinfo, dut_pool, logdir, logger ):
    errormessage = ''
    caselogger = createLogger('caselog.txt', logdir)
    bench = benchinfo
    try:
        import re
        patDash  = re.compile('\s*(python |python[\d.]+ |python.exe |)\s*cr.py\s+(.+)\s*', re.DOTALL|re.IGNORECASE)
        m =  re.match(patDash, cmd)
        returncode = 0
        if m:

            argstring = m.group(2)
            import shlex
            lstArg = shlex.split(argstring)
            #0-case.csv, 1-bench, 2-mode, 4...-2- args
            casefile = lstArg[0]
            case_benchfile = lstArg[1]
            case_mode       = lstArg[2]
            case_args= lstArg
            case_args.insert(0,'cr.py')

            if case_benchfile!=benchfile:
                from common import bench2dict
                caselogger.info('loading a new bench:%s'%case_benchfile)
                bench =bench2dict(case_benchfile)
                benchfile = case_benchfile
                caselogger.info('releasing duts in old dut_pool')
                releaseDUTs(dut_pool, logger)
                dut_pool ={}
            from Parser import  caseParser
            caselogger.info('loading case: %s'% casename)
            cs = caseParser(casename, case_mode, logdir, caselogger)
            sdut, lvar, lsetup, lrun, ltear =cs.load(casefile, case_args)
            ldut = list(sdut)
            newduts= []
            oldduts = []
            for nd in ldut:
                if dut_pool.has_key(nd):
                    oldduts.append(nd)
                    dut_pool[nd].FailFlag    =False # the flag means in Session's perspective view, case failed
                    dut_pool[nd].ErrorMessage=None # to store the error message
                else:
                    newduts.append(nd)

            for od in oldduts:
                dut_pool[od].openLogfile(logdir)
            errormessage =[]
            duts= initDUT(errormessage,bench,newduts,logger, logdir)

            for k in duts.keys():
                dut_pool[k]=duts[k]

            for key in duts.keys():
                if dut_pool.has_key(key):
                    continue
                else:
                    dut_pool[key]= duts[key]

            seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]
            caselogger.info('starting to run case: %s'%cmd)
            returncode, STRerrormessage= case_runner(casename,dut_pool,seq, case_mode, caselogger)

            if returncode:
                caselogger.error('Case Failed:%s'%STRerrormessage)
                errormessage.append(STRerrormessage)
            else:
                caselogger.info('Case PASS')

        else:
            import subprocess
            pp =None

            import re
            patPython = re.compile('\s*(python\s+|python.exe\s+|)([\w_-]+.py)', re.IGNORECASE)
            m=re.match(patPython, cmd)
            if m :
                newcmd =m.group(2)
                exe_cmd ='python '+ cmd+" "+logdir
                caselogger.info('running case: %s'%exe_cmd)
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

    except Exception as e:

        if returncode ==0:
            returncode =1

        import traceback
        errormessage = '%s\n%s'%(e.__str__(),traceback.format_exc())
        caselogger.error('Case FAIL')
        caselogger.error(errormessage)
    return  returncode, errormessage, benchfile,bench, dut_pool


def array2html(reportname, ArgStr, CaseRangeStr, TOTAL,CASERUN, CASEPASS,CASEFAIL, CASENOTRUN,Report, suiteStartTime,suiteEndTime):
    import time
    if CASERUN==0 :#or TOTAL==0:
        CASERUN=1
    if TOTAL==0:
        TOTAL=1

    PPASS = '%.0f'%((CASEPASS*100.0)/CASERUN*1.0)+'''%'''
    PFAIL = '%.0f'%((CASEFAIL*100.0)/CASERUN*1.0)+'''%'''
    CASENOTRUN  = TOTAL - CASEPASS-CASEFAIL
    PNOTRUN = '%.0f'%((CASENOTRUN*100.0) /TOTAL*1.0)+'''%'''

    import datetime
    response ="""
<HTML>
<HEAD>
<TITLE>Suite Test Report</TITLE>
</HEAD>
<BODY>
<table cellspacing="1" cellpadding="2" border="1">
<tr><td>Start Time</td><td>End Time</td><td>Duration(H:M:S)</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td></tr>
</table>
<br>
<table cellspacing="1" cellpadding="2" border="1">
<tr><td>SUITE NAME</td><td>ARGURMENTS</td><td>CASE RANGE</td></tr>

<tr><td>%s</td><td>%s</td><td>%s</td></tr>
</table>
<br><br>

<table cellspacing="1" cellpadding="2" border="1">
<tr>
<td>TOTAL CASE</td><td bgcolor="#00FF00">PASS</td><td bgcolor="#FF0000">FAIL</td><td bgcolor="#0000FF">NOT RUN</td>
</tr>
<tr>
<td>%d</td><td bgcolor="#00FF00" >%d</td><td bgcolor="#FF0000">%d</td><td  bgcolor="#0000FF">%d</td>
</tr>
<tr>
<td> </td><td>%s</td><td>%s</td><td>%s</td>
</tr>
</table>
<BR>
<BR>
<table cellspacing="1" cellpadding="2" border="1">
"""%(time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(suiteStartTime)), time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(suiteEndTime)),str(datetime.timedelta(seconds=suiteEndTime-suiteStartTime)),reportname, CaseRangeStr, ArgStr ,TOTAL, CASEPASS, CASEFAIL, CASENOTRUN, PPASS,PFAIL,PNOTRUN)

    response = response+ '''<tr><td>No.</td><td>Result</td><td>Case Name</td><td>Duration(s)</td><td>StartTime</td><td>EndTime</td><td>Line No</td><td>Error Message</td></tr>'''
    #NewRecord = [index,caseResult,caseline[2][1], errormessage,logdir, LineNo]
    import re
    for result in Report:
        index,caseResult,caseLine, errormessage,logdir, LineNo ,ExecutionDuration, caseStartTime,caseEndTime=result
        caseStartTime =time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(caseStartTime))
        caseEndTime =time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(caseEndTime))
        if errormessage ==[]:
            errormessage ='-'
        else:
            if type(errormessage)==type([]):
                errormessage = ''.join([x for x in errormessage])

        if errormessage:
            errormessage = re.search('\*ERROR MESSAGE:(.*?)\*Traceback',errormessage,re.IGNORECASE|re.DOTALL)
        if errormessage:
            errormessage= errormessage.group(1).replace('*\t','')
        bgcolor="#00FF00"
        if caseResult=='FAIL':
            bgcolor = "#FF0000"

        response = response +"""<tr>
        <td>%d</td>
        <td bgcolor="%s"><a target="+BLANK" href="%s">%s</td>
        <td><a target="+BLANK" href="%s">%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        </tr>
"""%(index,bgcolor,logdir,caseResult,logdir,caseLine, ExecutionDuration,caseStartTime,caseEndTime, LineNo, errormessage)

    return response+"""</table>
<br />
<br />
</body></html>"""

