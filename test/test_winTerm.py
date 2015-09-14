__author__ = 'Sean Yu'
'''created @2015/9/14''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))


array2csvfile(a, 'c://logs/abc.csv')
class Test_winTerm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        name= 'e7-20'
        cmd = 'telnet 10.245.75.20'
        cmd = 'telnet 10.245.48.20'#great wall e7-20
        #cmd = 'telnet 10.245.69.106'#ryi
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        global  logpath
        logpath='./tmp1'

        import shutil
        global logpaht
        if os.path.exists(logpath):
            shutil.rmtree(logpath)


        if not os.path.exists(logpath):
            os.mkdir('tmp1')
        cls.logpath = logpath
        cls.baseS = E7(name,attr,logger,logpath)
        global  baseS
        baseS = cls.baseS



    def setUp(self):
        from IxNetwork import IxNetwork
        self.ixN = IxNetwork('ixiaNetwork', {'IP': '192.168.37.112', 'version': '7.30'}, logpath='./tmp1')
        #self.ixN = IxNetwork('ixiaNetwork', {'IP': '10.245.69.107'})
        self.ixN.OpenTcl()
        self.ixN.loadConfigFile('../case/GW/ixiaCFG/GW.ixncfg')
        #self.ixN.stopTraffic()
        #self.ixN.stopAllProtocols()

    @classmethod
    def tearDownClass(cls):

        del cls.baseS

        #cls._connection.destroy()
    def txest_RobustONT64(self):

        self.ixN.startAllProtocols()
        self.ixN.clearStats()
        self.ixN.startTraffic()
        baseS.getOntRangeTime('20/8', 300 , wait= 60)
        self.ixN.stopTraffic()
        self.ixN.stopAllProtocols()
        #result = self.ixN.getStatsItem("Flow Statistics", "Loss Duration Time")
        self.ixN.CheckMcastPktLossDuration(5*60)
        casefail = self.ixN.FailFlag+baseS.FailFlag
        msg =[]
        if casefail:
            if not self.ixN.ErrorMessage:
                self.ixN.ErrorMessage=[]
            if not baseS.ErrorMessage:
                baseS.ErrorMessage=[]
            msg = ['ixiaNetwork']+self.ixN.ErrorMessage+['E7']+baseS.ErrorMessage

        baseS.Write2Csv(msg, 'result.csv')

        self.assertEqual(baseS.FailFlag , False)
    def test_RobustONT64(self):
        # self.ixN.startAllProtocols()
        # self.ixN.startTraffic()
        # self.ixN.stopTraffic()

        #result = self.ixN.getStatsItem("Flow Statistics", "Loss Duration Time")
        self.ixN.CheckMcastPktLossDuration(5*60)
        casefail = self.ixN.FailFlag+baseS.FailFlag
        msg =[]
        if casefail:
            if not self.ixN.ErrorMessage:
                self.ixN.ErrorMessage=[]
            if not baseS.ErrorMessage:
                baseS.ErrorMessage=[]
            msg = ['ixiaNetwork']+self.ixN.ErrorMessage+['E7']+baseS.ErrorMessage

        baseS.Write2Csv(msg, 'result.csv')

        self.assertEqual(baseS.FailFlag , False)


if __name__ == '__main__':
    unittest.main()