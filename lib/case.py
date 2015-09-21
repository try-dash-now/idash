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


    def __loadCsv(self, filename):
        sdut    =  set( [])
        lvar    =   {}
        lsetup  =   []
        lrun    =   []
        ltear   =   []
        state = ('begin','var', 'setup','run', 'teardown', 'end' )
        def addVar(csv, varlist):
            lc = len(csv)
            if lc ==0:#nothing to do
                pass
            elif lc == 1:
                varname = csv[0].strip()
                if varname=='':
                    pass
                else:
                    varlist.append([varname, ''])
            else:
                varname = csv[0].strip()
                varlist.update({varname: csv[1]})
        def add2Segment(lineno, previousDut, csv, seg ,dutset):
            lc = len(csv)
            cmd =''
            exp ='.*'
            wait= 1
            if lc == 0:
                pass
            else :
                dut= csv[0].strip()
                if dut=='':
                    dut=previousDut.strip()
                    if dut=='':
                        raise ValueError('Line %d:no Dut assgined, it should be one of dut name used in this case')
                if lc==1:
                    pass
                elif lc ==2:
                    cmd= csv[1]
                elif lc ==3:
                    cmd= csv[1]
                    exp = csv[2]
                else:
                    cmd= csv[1]
                    exp = csv[2]
                    if csv[3].strip()!='':
                        wait = float(csv[3])
            dutset.add(dut)
            seg.append([dut, cmd, exp, wait])
            return  dut
        def segTest(lineno,previousDut, curseg , csv, var,setup, run, teardown, dutset):
            seg = curseg
            curdut=previousDut
            import re as sre
            reCaseEnd   = sre.compile("^[\s]*#[\s]*END[\s]*",sre.I)
            reVar       = sre.compile("^[\s]*#[\s]*VAR[\s]*",sre.I)
            reSetup     = sre.compile("^[\s]*#[\s]*SETUP[\s]*",sre.I)
            reRun       = sre.compile("^[\s]*#[\s]*RUN[\s]*",sre.I)
            reTeardown  = sre.compile("^[\s]*#[\s]*TEARDOWN[\s]*",sre.I)
            #reOnFail    = sre.compile("^[\s]*#[\s]*ONFAIL[\s]*",sre.I)
            reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)

            strcsv = ','.join(csv)

            if sre.match(reCaseEnd, strcsv):
                seg =  state.index('end')
            elif sre.match(reVar, strcsv):
                seg = state.index('var')
            elif sre.match(reSetup, strcsv):
                seg = state.index('setup')
            elif sre.match(reRun, strcsv):
                seg = state.index('run')
            elif sre.match(reTeardown, strcsv):
                seg = state.index('teardown')
            elif sre.match(reComment, strcsv):
                pass
            else:
                if seg == state.index('begin'):
                    pass
                elif seg == state.index('var'):
                    addVar(csv , var)
                elif seg == state.index('setup'):
                    curdut = add2Segment(lineno, previousDut, csv, setup, dutset)
                elif seg == state.index('run'):
                    curdut = add2Segment(lineno, previousDut, csv, run, dutset)
                elif seg == state.index('teardown'):
                    curdut = add2Segment(lineno, previousDut, csv, teardown, dutset)
                elif seg == state.index('end'):
                    pass
                else:
                    raise ValueError('unknown state(%d) in CSV file, it should be one of %s'%(seg, str(state)))
            return seg, curdut

        from common import csvfile2array
        lines = csvfile2array(filename)
        LineNo =0
        dutname =None
        import re as sre
        reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
        cstate = 0
        predut = ''
        for line in lines:
            LineNo +=1
            col1 = line[0]
            cstate, predut = segTest(LineNo,predut, cstate, line, lvar, lsetup,lrun, ltear,sdut)
            if cstate ==state.index('end'):
                break

        return sdut, lvar, lsetup, lrun, ltear

    @logAction
    def load(self, filename, filetype='csv'):
        '''
        read a file, and create a case, setup,run, teardown
        and record the relation between LineNumber of file and IndexOfList(setup, run,teardown
        file could be CSV file, now only CSV supported, future, it could be a url, database ...

        '''
        sdut, lvar, lsetup, lrun, ltear=None,None,None, None, None
        if filetype.lower() =='csv':
            sdut, lvar, lsetup, lrun, ltear=  self.__loadCsv(filename)
        return  sdut, lvar, lsetup, lrun, ltear






