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
#cmd = 'telnet 192.168.1.113'
cmd = 'telnet cdc-dash'
where ='home'
cs =None
class test_Parser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from winTelnet import winTelnet
        name= 'e7-20'
        where  = 'home'
        cmd = 'telnet cdc-dash'
        if where =='home':
            cmd = 'telnet 192.168.1.113'
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        global  logpath
        logpath='./log/ut_parser'

        import shutil
        if os.path.exists(logpath):
            shutil.rmtree(logpath)


        if not os.path.exists(logpath):
            os.mkdir(logpath)
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
        baseS.SessionAlive=False



    def setUp(self):
        pass
    def tes1t_Init(self):
        from Parser import  caseParser
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        global cs
        cs = caseParser('testcase',  mode, './log/ut_parser' )
    def tes1t_execute(self):
        from Parser import  caseParser
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = caseParser('testcase', mode, './log/ut_parser' )
        #cs.myrunner(cs.runcase, [mode])
        rsp = self.assertRaises(Exception, cs.execute, 'xxx')
        rsp = cs.execute('s')
        rsp = cs.execute('r')
        rsp = cs.execute('t')

    def tes1t_loadCsvCase(self):
        from Parser import  caseParser
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = caseParser('testParser',  mode, './log/ut_parser' )
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

        cmd = 'telnet cdc-dash'
        if where =='home':
            cmd = 'telnet 192.168.1.113'
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        logpath='./log/ut_parser'

        import shutil
        if not os.path.exists(logpath):
            os.mkdir(logpath)

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
        from Parser import caseParser
        setup =[]
        run =[]
        teardown=[]
        duts = {'winTel': baseS}
        mode = 'full'
        cs = caseParser('execute2', mode, './tmp1' )
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
        #cs.execute('full')
        print(dutname)
        print(varlist)
        print(setup)
        print(run)
        print(tear)
        baseS.SessionAlive =False
    def test_suiteParser(self):
        from Parser import suiteParser
        from runner import createLogDir
        suitefile = './suite1.csv'
        name = 'suite1_parser'
        logpath = './log'
        logpath = createLogDir(name, logpath)
        st = suiteParser(name, logpath)
        suite= st.load(suitefile)
        from runner import concurrent
        for i in suite:
            if i[2][0]!=concurrent:
                print(i)
            else:
                print(i)
                for ii in i[2][1]:
                    print('\t'+str(i[0])+' '+str(ii))


    @classmethod
    def tearDownClass(cls):
        cls.baseS.SessionAlive = False
        del cls.baseS

if __name__ == '__main__':
    unittest.main()