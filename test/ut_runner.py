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
class test_Parser(unittest.TestCase):
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


    def test_createCaseLogDir(self):
        from runner import createCaseLogDir
        logpath ='./log'
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        casefolder = createCaseLogDir('case1',logpath)

    def test_InitDUTs(self):
        from runner import initDUT
        logpath ='./log'
        from common import bench2dict
        bench =bench2dict('./bench.csv')
        duts= initDUT(bench,['lnx1', 'lnx2'])
        print(duts)





if __name__ == '__main__':
    unittest.main()