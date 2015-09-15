__author__ = 'Sean Yu'
'''created @2015/9/14''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))



class Test_winTerm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from winTelnet import winTelnet
        name= 'e7-20'
        cmd = 'telnet 192.168.1.111'
        cmd = 'telnet cdc-dash'
        #cmd = 'telnet 10.245.48.20'#great wall e7-20
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
        cls.baseS = winTelnet(name,attr,logpath)
        global  baseS
        baseS = cls.baseS



    def setUp(self):
        pass
    def test_Send(self):
        baseS.Send('')
        import time
        time.sleep(10)

    @classmethod
    def tearDownClass(cls):

        del cls.baseS

        #cls._connection.destroy()




if __name__ == '__main__':
    unittest.main()