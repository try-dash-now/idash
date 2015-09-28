# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/9/18 
'''
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))

cs =None
class test_case(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from winTelnet import winTelnet
        name= 'e7-20'
        cmd = 'telnet 192.168.1.113'
        #cmd = 'telnet cdc-dash'
        #cmd = 'telnet 10.245.48.20'#great wall e7-20
        #cmd = 'telnet 10.245.69.106'#ryi
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        global  logpath
        logpath='./tmp1'

        import shutil
        if os.path.exists(logpath):
            shutil.rmtree(logpath)


        if not os.path.exists(logpath):
            os.mkdir('./tmp1')
        cls.logpath = logpath

        import logging
        logfile = logpath+os.sep+"tc.log"
        logging.basicConfig( level = logging.DEBUG)
        #from common import CLogger
        #self.logger = CLogger(self.Name)
        logger = logging.Logger(name,logging.DEBUG)
        hdrlog = logging.FileHandler(logfile)
        logger.setLevel(logging.DEBUG)
        hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
        logger.addHandler(hdrlog )

        cls.baseS = winTelnet(name,attr,logger , logpath)

        global  baseS, cs
        baseS = cls.baseS
        baseS.find('ogin:', 30)
        baseS.send('syu')
        baseS.find('assword', 30)
        baseS.send('yxw123')
        baseS.find('~', 30)



    def setUp(self):
        pass
    def tes1t_Init(self):
        from case import  case
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        global cs
        cs = case('testcase',  mode, './tmp1' )
    def tes1t_execute(self):
        from case import  case
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = case('testcase', mode, './tmp1' )
        #cs.myrunner(cs.runcase, [mode])
        rsp = self.assertRaises(Exception, cs.execute, 'xxx')
        rsp = cs.execute('s')
        rsp = cs.execute('r')
        rsp = cs.execute('t')

    def tes1t_loadCsvCase(self):
        from case import  case
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = case('testcase',  mode, './tmp1' )
        arg =[]
        gvars =['gv1', 'gv2', 'gv3',]

        resp =cs.load('./case2-novar.csv',gvars )
        dutname, varlist,setup, run, tear = resp
        print(dutname)
        print(varlist)
        print(setup)
        print(run)
        print(tear)


        resp =cs.load('./case1.csv',gvars )
        dutname, varlist,setup, run, tear = resp
        print(dutname)
        print(varlist)
        print(setup)
        print(run)
        print(tear)

    def test_execute2(self):
        from winTelnet import winTelnet
        name= 'e7-20'
        cmd = 'telnet 192.168.1.113'
        #cmd = 'telnet cdc-dash'
        #cmd = 'telnet 10.245.48.20'#great wall e7-20
        #cmd = 'telnet 10.245.69.106'#ryi
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        logpath='./tmp1'

        import shutil
        if not os.path.exists(logpath):
            os.mkdir('./tmp1')

        import logging
        logfile = logpath+os.sep+"execute2tc.log"
        logging.basicConfig( level = logging.DEBUG)
        #from common import CLogger
        #self.logger = CLogger(self.Name)
        logger = logging.Logger(name,logging.DEBUG)
        hdrlog = logging.FileHandler(logfile)
        logger.setLevel(logging.DEBUG)
        hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
        logger.addHandler(hdrlog )

        baseS = winTelnet(name,attr,logger , logpath)
        baseS.find('ogin:', 30)
        baseS.send('syu')
        baseS.find('assword', 30)
        baseS.send('yxw123')
        baseS.find('~', 30)
        from case import  case
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = case('execute2', mode, './tmp1' )
        arg =[]
        gvars =['winTel', 'whoami', 'ls','pwd']
        resp =cs.load('./case3.csv',gvars )
        dutname, varlist,setup, run, tear = resp
        #baseS.send('ls')
        #baseS.find('git', 30)

        #ref = cs.duts['winTel']
        #ref.send('ping localhost')
        #ref.send('pwd')
        #ref.find('syu', 10)
        #ref.send('ping localhost')
        #ref.send('c', Ctrl=True)
        cs.execute('full')
        print(dutname)
        print(varlist)
        print(setup)
        print(run)
        print(tear)
    @classmethod
    def tearDownClass(cls):
        cls.baseS.SessionAlive = False
        del cls.baseS

if __name__ == '__main__':
    unittest.main()