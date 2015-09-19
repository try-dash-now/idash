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
    setup       = None #steps in setup section
    run         = None #steps in setup section
    teardown    = None #steps in setup section
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
        self.setup =setup
        self.run = run
        self.teardown =tear

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
            for dut, cmd,expect , due in self.setup:
                print dut, cmd, expect, due
        if mode in {'full', 'run', 'nosetup', 'notear', 'r', 'ns', 'nt', 'f'}:
            for dut, cmd,expect , due in self.run:
                print dut, cmd, expect, due
        if mode in {'full', 'tear', 'norun', 'nosetup', 't', 'nr', 'ns', 'f'}:
            for dut, cmd,expect , due in self.teardown:
                print dut, cmd, expect, due
        return None

    def execute(self, mode =None):
        m =self.mode
        if mode :
            m =str(mode).lower()

        CaseFail, response = self.__run(m)
        if CaseFail:
            self.error(response, True)

