# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/9/18 
'''
import traceback
log=''
def logCall(logger, fun):
    def inner(*arg, **kwargs):
        logger += str(arg)
        logger += str(kwargs)
        return fun(*arg, **kwargs)
    return inner
CASE_MODE = set(['full', 'f',
                 'setup', 's',
                 'run', 'r',
                 'tear', 't', 'teardown',
                 'nosetup', 'ns',
                 'norun', 'nr',
                 'notear', 'noteardown', 'nt',
                 ])

def error(msg,  logger=None, casefail=True):
    print(msg)
    if logger:
        logger.error(msg)
    if casefail:
        raise ValueError(msg)
class case(object):
    '''
    a case is a sequence operation
    '''
    name        = None # case name
    dicVar          = None #dict of Variable
    seqSetup       = None #steps in setup section
    seqRun         = None #steps in setup section
    seqTeardown    = None #steps in setup section
    logger      = None # logger of case, named as case_name.log
    logpath     = None # the case folder path
    mode        = None # string, case mode, one of {full,run, setup, tear, r,s, t, norun, nosetup, notear, nr, ns,nt}
    duts        = None # dict of DUTs
    state = ('searchingVAR', 'searchingSetup','searchingRun', 'searchingTeardown', 'searchingEnd' )
    def __init__(self,name, duts, setup=[], run=[], tear=[], mode='full',logpath='./'):
        '''
            name: string, the case's name, just letter, number and _, -, max length is 80
            duts: dict of terms/connection/sessions, on_dutA, on_dutB are instance(sessions connected to dutA, dutB...   can send commands to DUT, and check response
                {
                    on_dutA: instance_of_dutA,
                    on_dutB: instance_of_dutB,
                }
            setup, run, tear:
                list, default
                each one (setup, run, tear ) format as below
                [
                    [on_dutA, action1, expect_pattern, within_given_due_time],
                    ...
                    [on_dutB, actionN, expect_pattern, within_given_due_time]
                ]
            mode: string, could be one of [full, setup, run, teardown, nosetup, norun, notear], otherwise it's full
            logpath: string, default is current folder

        '''

        #create  a unique folder for case, and logfile for case
        import os
        if not os.path.exists(logpath):
            logpath = os.getcwd()
        import re, datetime
        fullname = name[:80]+datetime.datetime.now().isoformat('_')
        self.name = re.sub('\W', '.', fullname)
        logpath = logpath+'/'+ self.name
        print("case folder created: %s"%logpath)
        os.mkdir(logpath)
        self.logpath= logpath
        import logging
        logfile = logpath+"/tc.log"
        self.logger = logging.Logger(self.name,logging.DEBUG)
        hdrlog = logging.FileHandler(logfile)
        hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
        self.logger.addHandler(hdrlog )
        self.logger.info("case folder created: %s"%logpath)

        m = mode.lower()
        modeset = {'full', 'f', 'run', 'r', 'setup', 's', 'tear', 't', 'norun', 'nr', 'nosetup', 'ns', 'notear', 'nt'}
        if m not in modeset:
            errormessage = 'mode(%s) is wrong,it should be one of %s, not case-sensitive '%(mode, str(modeset))
            self.error(errormessage)
        self.mode = m
        self.duts =duts
        self.openDutLogfile()
        self.seqSetup =setup
        self.seqRun = run
        self.seqTeardown =tear

    def openDutLogfile(self):
        for dut_name in self.duts.keys():
            self.duts[dut_name].openLogfile(self.logpath)
            self.logger.info("DUT %s redirected to case folder"%dut_name)
    def error(self,msg,  casefail=True):
        print(msg)
        if self.logger:
            self.logger.error(msg)
        if casefail:
            raise ValueError(msg)
    def logAction(fun):
        def inner(*arg, **kwargs):
            CaseFail=True
            try:
                msg ='fun: %s\narg: %s\nkwargs: %s'%(str(fun), str(arg), str(kwargs))
                print(msg)
                response = fun(*arg, **kwargs)
                return  (not CaseFail,response)
            except Exception as e:
                msg = traceback.format_exc()
                msg +='\tfun: %s\n\targ: %s\n\tkwargs: %s'%(str(fun), str(arg), str(kwargs))
                return (CaseFail,msg)
            return inner
        return inner
    @logAction
    def __run(self, mode):
        global  CASE_MODE

        if mode not in CASE_MODE:
            raise ValueError('case mode is wrong, should be one of %s'%(str(CASE_MODE)))
        if mode in {'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'}:
            for dut, cmd,expect , due in self.seqSetup:
                print dut, cmd, expect, due
        if mode in {'full', 'run', 'nosetup', 'notear', 'r', 'ns', 'nt', 'f'}:
            for dut, cmd,expect , due in self.seqRun:
                print dut, cmd, expect, due
        if mode in {'full', 'tear', 'norun', 'nosetup', 't', 'nr', 'ns', 'f'}:
            for dut, cmd,expect , due in self.seqTeardown:
                print dut, cmd, expect, due
        return None

    def execute(self, mode =None):
        m =self.mode
        if mode :
            m =str(mode).lower()

        CaseFail, response = self.__run(m)
        if CaseFail:
            self.error(response, True)

    def __csvAddVar(self, listOfLine):
        lline = len(listOfLine)
        var = {}
        if lline==0:
            pass
        elif lline==1:
            if len(listOfLine[0].strip()):
                var = {listOfLine[0]:''}
        else:
            if len(listOfLine[0].strip()):
                var =  {listOfLine[0]:listOfLine[1]}

        self.dicVar.update(var)
    def __csvAddCmd(self, lineNo, listCmd, stage):
        lcmd = len(listCmd)
        def proceedCmd(previousDUT,  cmd, target):
            lenOfCmd =len(listCmd)
            if lenOfCmd  ==0:
                pass
            elif lenOfCmd == 1:
                if len(cmd[0].strip())>0:
                    target.append([cmd[0], '', '.*', 1])
            elif lenOfCmd ==2:
                if len(cmd[0].strip())>0:
                    target.append([cmd[0], '', '.*', 1])

        if stage == self.state.index('searchingRun'):
            #add command to seqSetup
        elif  stage == self.state.index('searchingTeardown'):
            #add command to seqRun
        elif stage == self.state.index('searchingEnd'):
            #add command to seqTeardown

    def __loadCsv(self, filename):
        lsut    =   []
        lvar    =   {}
        lsetup  =   []
        lrun    =   []
        ltear   =   []
        import re as sre
        reCaseEnd   = sre.compile("^[\s]*#[\s]*!---[\s]*",sre.I)
        reVar       = sre.compile("^[\s]*#[\s]*VAR[\s]*",sre.I)
        reSetup     = sre.compile("^[\s]*#[\s]*SETUP[\s]*",sre.I)
        reRun       = sre.compile("^[\s]*#[\s]*RUN[\s]*",sre.I)
        reTeardown  = sre.compile("^[\s]*#[\s]*TEARDOWN[\s]*",sre.I)
        reOnFail    = sre.compile("^[\s]*#[\s]*ONFAIL[\s]*",sre.I)
        reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)

        from common import csvfile2array
        lines = csvfile2array(filename)
        state = self.state #('searchingVAR', 'searchingSetup','searchingRun', 'searchingTeardown', 'searchingEnd' )
        stage = 0
        LineNo =0

        for line in lines:
            LineNo +=1
            col1 = line[0]
            if sre.match(reComment):#ignore comment line
                continue


            if not sre.match(reVar, col1):#not find "#var", continue searching segment VAR
                continue
            else:#find '#VAR', start to find one of #setup, #run, #teardown
                if stage<state.index('searchingSetup'):# just find #VAR
                    stage+=1
                else:# found VAR, searching end of segment VAR
                    ms = sre.match(reSetup, col1)
                    mr = sre.match(reRun, col1)
                    mt = sre.match(reTeardown, col1)
                    if not ( ms or mr or mt ):#
                        self.__csvAddVar(line)
                    else:# find the end of VAR
                        if stage ==state.index('searchingSetup'):
                            if ms:
                                stage = state.index('searchingRun')
                            elif mr:
                                stage = state.index('searchingTeardown')
                            elif mt:
                                stage = state.index('searchingEnd')
                        else:#searching next stage
                            if stage==



    def load(self, filename, filetype='csv'):
        '''
        read a file, and create a case, setup,run, teardown
        and record the relation between LineNumber of file and IndexOfList(setup, run,teardown
        file could be CSV file, now only CSV supported, future, it could be a url, database ...

        '''

        if filetype.lower() =='csv':
            self.__loadCsv(filename)






