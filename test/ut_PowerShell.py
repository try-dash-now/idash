# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
'''created @2015/10/12''' 

import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))

class test_Parser(unittest.TestCase):
    def test_PowerShell(self):
        from runner import case_runner, initDUT, createLogDir, createLogger
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logpath+='/PowerShell'
        logger = createLogger('PowerShell', logpath)
        casename = 'PowerShell_1'
        casefolder = createLogDir(casename,logpath)

        from common import bench2dict
        where= 'nohome'
        benchfile = './bench.csv'
        casefile = './powershell.csv'
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


if __name__ == '__main__':
    unittest.main()