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
            msg ='fun: %s\narg: %s\nkwargs: %s'%(str(fun), str(arg), str(kwargs))
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
            msg ='*logAction dump:\n\tFunction Name: \t\t%s\n\tArguments: \t\t%s\n\tKeyword Arguments: \t\t%s'%(str(fun), argstring, kwargstring)
            from common import DumpStack
            msg =msg +'\n-------------------------------------------------------------------------------'+DumpStack(e)
            msg = '*********************************ERROR DUMP*************************************\n'+msg.replace('\n', '\n*')+'*********************************EREOR END**************************************\n\n'
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
def createCaseLogDir(casename,logpath='./'):
    import re, datetime
    fullname = casename[:80]
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
            # from common import DumpStack
            # msg ='\n'*8+DumpStack(e)+'\n'
            # print(msg)
            # import os
            # msg = 'can\'t init dut(%s)\n'%(dutname)+msg
            # errormessage = msg
            # with open(os.getcwd()+'/error.txt','a+') as errorfile:
            #     errorfile.write(msg)
            # if logger:
            #     logger.error(msg)
            #global  gInitErrorMessage
            msg = 'can\'t init dut(%s)\n'%(dutname)
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
    if len(errormessage)!=0 or len(dictDUTs)==0:
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
def run(casename,duts, seqs ,mode):
        global  CASE_MODE
        def analyzeStep(casename, dut, commnad, expect, wait):
            funName = dut.defaultFunction
        if mode not in CASE_MODE:
            raise ValueError('case mode is wrong, should be one of %s'%(str(CASE_MODE)))

        def runSegment( casename, mode, modeset, duts, seq, segName):

            if mode in modeset:#{'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'}:
                segment=segName#'setup'
                stepindex= 1
                for dut, cmd,expect , due, lineno in seq:#self.seqSetup:
                    session = duts[dut]
                    session.stepCheck(casename, lineno, cmd, expect, due)
                    stepindex+=1
                    print lineno ,dut, cmd, expect, due

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
            runSegment(casename, mode, modeset[index], duts,seqlist[index],  segNamelist[index])
            index +=1


        return None


def case_runner(casename, dictDUTs, case_seq, mode='full'):
    m =mode
    if mode :
        m =str(mode).lower()
    response = run(casename, dictDUTs, case_seq, m)
    print(response)
    return  response

def loop(counter, stop_at_fail, cmd):
    i = 0
    flagFail = False
    msgError = ''
    while i <counter:
        try:
            i +=1
            import shlex
            cmdlist = shlex.split(cmd,comments=True)
            case_runner(*cmdlist)
        except:
            flagFail=True
            msgError +='%s: failed @%d of %d'%(cmd, i,counter)
            if stop_at_fail:
                break

    return  flagFail, msgError

def concurrent(cmdConcurrent):
    msgError =''
    def folder(cmd, times):
        ths = []
        import threading
        import shlex
        for i in range(0,times):

            cmdlist = shlex.split(cmd,comments=True)
            th =threading.Thread(target= case_runner,args=cmdlist )
            ths.append(th)
        for i in ths:
            i.start()
        for i in ths:
            i.join()
    msgConcurrent = ''
    for line in cmdConcurrent:
        cmd = line[0]
        times = line[1]
        try:
            folder(cmd, times )
        except:
            msgConcurrent +='%s: repeat %s failed\n'%(cmd,times)
def suite_runner(dictDUTs, case_seqs):

    pass
def releaseDUTs(duts):
    for name in duts.keys():
        dut = duts[name]
        if dut :
            dut.SessionAlive=False
errorlogger = None
