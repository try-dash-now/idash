# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/9/29 
'''


import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))
cmd = 'telnet 192.168.1.113'
#cmd = 'telnet cdc-dash'

from runner import *
class test_caseParser(unittest.TestCase):
    def test_0init(self):
        import shutil
        log = './log'
        if os.path.exists(log):
            shutil.rmtree(log)
    def test_createLogger(self):
        logpath = './log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logger = createLogger('runner_logger', logpath+'/ut_runner')
        logger.error('this is error message')
        logger.info('this is info message')
        logger.debug('this is debug message')


    def test_createLogDir(self):
        from runner import createLogDir
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        casefolder = createLogDir('case1',logpath)

    def tes1t_InitDUTs(self):
        from runner import initDUT
        logpath ='./log'
        from common import bench2dict
        bench =bench2dict('./bench.csv')
        duts= initDUT(bench,['lnx1', 'lnx2'])
        print(duts)

    def test_case_runner(self):
        from runner import case_runner, initDUT, createLogDir
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath+='/ut_runner'
        logger = createLogger('runner_logger', logpath)
        casename = 'test_case_runner_2_duts'
        casefolder = createLogDir(casename,logpath)

        from common import bench2dict
        where= 'nohome'
        benchfile = './bench.csv'
        casefile = './runner_case.csv'
        if where=='home':
            benchfile= './home.csv'
            casefile = './home_case.csv'

        bench =bench2dict(benchfile)


        from Parser import  caseParser
        mode = 'full'
        cs = caseParser(casename, mode, casefolder)

        sdut, lvar, lsetup, lrun, ltear =cs.load(casefile)
        ldut = list(sdut)
        errormessage =[]
        duts= initDUT(errormessage,bench,ldut,logger, casefolder)#['lnx1', 'lnx2']
        seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]
        case= case_runner(casename,duts,seq, mode)


        print(duts)
        for name in duts.keys():
            dut = duts[name]
            if dut :
                dut.SessionAlive=False
    def test_case_runner_init_dut_failed(self):
        from runner import case_runner, initDUT, createLogDir
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath+='/ut_runner'
        logger = createLogger('runner_logger', logpath)
        casename = 'test_case_runner_2_duts'
        casefolder = createLogDir(casename,logpath)

        from common import bench2dict
        benchfile = './bench.csv'
        benchfile= './home.csv'
        bench =bench2dict(benchfile)


        from Parser import  caseParser
        mode = 'full'
        cs = caseParser(casename, mode, casefolder)
        casefile = './runner_case.csv'
        sdut, lvar, lsetup, lrun, ltear =cs.load(casefile)
        ldut = list(sdut)
        ldut[0]='N1wrong'
        errormessage =[]
        #duts= initDUT(errormessage,bench,ldut,logger, casefolder)#['lnx1', 'lnx2']
        self.assertRaises(Exception, initDUT,errormessage,bench, ldut,logger, casefolder)
    def test_suiteLoad(self):
        from runner import case_runner, initDUT, createLogDir
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath+='/ut_runner'
        logger = createLogger('runner_logger', logpath)
        casename = 'test_suiteLoad'
        casefolder = createLogDir(casename,logpath)

        from common import bench2dict
        where= 'home'
        benchfile = './bench.csv'
        casefile = './suite_parser.csv'
        if where=='home':
            benchfile= './home.csv'
            casefile = './suite1.csv'

        bench =bench2dict(benchfile)


        from Parser import  suiteParser
        suite = suiteParser(casename, casefolder)

        st =suite.load(casefile)
        for i  in st:
            print(i)
#        ldut = list(sdut)
#        errormessage =[]
#        duts= initDUT(errormessage,bench,ldut,logger, casefolder)#['lnx1', 'lnx2']
#        seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]
#        case= case_runner(casename,duts,seq, mode)
#
#
#        print(duts)
#        for name in duts.keys():
#            dut = duts[name]
#            if dut :
#                dut.SessionAlive=False
if __name__ == '__main__':
    unittest.main()