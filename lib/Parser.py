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
class Parser(object):
    '''
    a case is a sequence operation
    '''
    name        = None # case name
    lstVar          = None #dict of Variable, list of variables,, after substitude()
    seqSetup       = None #steps in setup section, the steps could be executed, after substitude()
    seqRun         = None #steps in setup section, the steps could be executed, after substitude()
    seqTeardown    = None #steps in setup section, the steps could be executed, after substitude()
    logger      = None # logger of case, named as case_name.log
    logpath     = None # the case folder path
    mode        = None # string, case mode, one of {full,run, setup, tear, r,s, t, norun, nosetup, notear, nr, ns,nt}
    duts        = None # dict of DUTs
    dutnames    = None # set of DUT names
    def __init__(self,name, mode='full',logpath='./'):
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
            try:
                msg ='fun: %s\narg: %s\nkwargs: %s'%(str(fun), str(arg), str(kwargs))
                print(msg)
                response = fun(*arg, **kwargs)
                return  response
            except Exception as e:
                msg ='\tFunction Name: \t\t%s\n\tArguments: \t\t%s\n\tKeyword Arguments: \t\t%s'%(str(fun), str(arg), str(kwargs))
                from common import DumpStack
                msg ='\n'*8+DumpStack(e)+'\n'+msg
                print(msg)
                import os
                with open(os.getcwd()+'/error.txt','a+') as errorfile:
                    errorfile.write(msg)
                raise RuntimeError(msg)
            return inner
        return inner
    @logAction
    def __run(self, casename, mode):
        global  CASE_MODE
        def analyzeStep(casename, dut, commnad, expect, wait):
            funName = dut.defaultFunction
            pass
        if mode not in CASE_MODE:
            raise ValueError('case mode is wrong, should be one of %s'%(str(CASE_MODE)))

        def runSegment( casename, mode, modeset, seq, segName):

            if mode in modeset:#{'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'}:
                segment=segName#'setup'
                stepindex= 1
                for dut, cmd,expect , due, lineno in seq:#self.seqSetup:
                    session = self.duts[dut]
                    session.stepCheck(casename, lineno, cmd, expect, due)
                    stepindex+=1
                    print lineno ,dut, cmd, expect, due

        modeset =[
                    {'full', 'setup', 'norun', 'notear', 's', 'nr', 'nt', 'f'},
                    {'full', 'run', 'nosetup', 'notear', 'r', 'ns', 'nt', 'f'},
                    {'full', 'tear', 'norun', 'nosetup', 't', 'nr', 'ns', 'f'}

                  ]
        seqlist =[self.seqSetup,
                  self.seqRun,
                  self.seqTeardown
                  ]
        segNamelist =['setup', 'run', 'teardown']
        index = 0
        totalseg = len(seqlist)
        while index <totalseg:
            runSegment(casename, mode, modeset[index], seqlist[index], segNamelist[index])


        return None

    def execute(self, mode =None):
        m =self.mode
        if mode :
            m =str(mode).lower()
        response = self.__run(self.name, m)

    @logAction
    def __loadCsvCase(self, filename, global_vars):
        sdut    =   set([])
        lvar    =   []
        lsetup  =   []
        lrun    =   []
        ltear   =   []
        state = ('begin','var', 'setup','run', 'teardown', 'end' )
        def addVar(csv, varlist, lineno):
            lc = len(csv)
            if lc ==0:#nothing to do
                pass
            elif lc == 1:
                varname = csv[0].strip()
                if varname=='':
                    pass
                else:
                    varlist.append([varname, '', lineno])
            else:
                varname = csv[0].strip()
                lvar.append([varname, csv[1], lineno])
        def add2Segment(lineno, previousDut, csv, seg ,dutset):
            lc = len(csv)
            cmd =''
            exp ='.*'
            wait= '1'
            if lc == 0:
                pass
            else :
                dut= csv[0].strip()
                if dut=='':
                    dut=previousDut.strip()
                    if dut=='':
                        raise ValueError('Line %d:no Dut assgined, it should be one of dut name used in this case'%(lineno))
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
                        wait = csv[3].strip()
                        try:
                            float(wait)#test wait(string) could be convert to float, otherwise raise an exception
                        except:
                            raise ValueError('Line %d:wait(%s) should be a float number'%(lineno, csv[3]))
                    else:
                        wait = '0'
            dutset.add(dut)
            seg.append([dut, cmd, exp, wait, lineno])
            return  dut#current dut
        def segTest(lineno,global_vars, previousDut, curseg , linestring, var,setup, run, teardown, dutset):
            import re
            def substitude(global_var, local_vars, linestring):
                index = 0
                tmpline = linestring
                for gv in global_vars:
                    tmpline = re.sub('\$\s*\{\s*%d\s*\}'%index, gv, tmpline)
                    index+=1
                for ln, lv, no in local_vars:
                    tmpline = re.sub('\$\s*\{\s*%s\s*\}'%(ln), lv, tmpline)
                return tmpline
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
            from common import csvstring2array
            strcsv = substitude(global_vars,var,linestring)
            csv = csvstring2array(strcsv)[0]
            strcsv =linestring # ','.join(csv)

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
                    addVar(csv , var,lineno)
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
        with open(filename, 'r') as csvfile:
            LineNo =0
            dutname =None
            import re as sre
            reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
            cstate = 0
            predut = ''
            for line in csvfile.readlines():
                LineNo +=1
                cstate, predut = segTest(LineNo,global_vars, predut, cstate, line, lvar, lsetup,lrun, ltear,sdut)
                if cstate ==state.index('end'):
                    break

        return sdut, lvar, lsetup, lrun, ltear



    def load(self, filename, global_vars=[], filetype='csv_case'):
        '''
        read a file, and create a case, setup,run, teardown
        and record the relation between LineNumber of file and IndexOfList(setup, run,teardown
        file could be CSV file, now only CSV supported, future, it could be a url, database ...

        '''
        response =[]
        sdut, lvar, lsetup, lrun, ltear=None,None,None, None, None
        if filetype.lower() =='csv_case':
            sdut, lvar, lsetup, lrun, ltear=  self.__loadCsvCase(filename, global_vars)
        self.seqSetup=lsetup
        self.seqRun = lrun
        self.seqTeardown= ltear
        self.dutnames = sdut

        return  sdut, lvar, lsetup, lrun, ltear

