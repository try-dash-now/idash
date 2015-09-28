__author__ = 'Sean Yu'
'''created @2015/9/14''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))


logpath = './tmp1'
class Test_winTerm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from winTelnet import winTelnet
        name= 'e7-20'
        #cmd = 'telnet 192.168.1.113'
        cmd = 'telnet cdc-dash'
        #cmd = 'telnet 10.245.48.20'#great wall e7-20
        #cmd = 'telnet 10.245.69.106'#ryi
        attr={'TIMEOUT':180,'LOGIN': 'e7support,assword:,30\nadmin,>,30','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        global logpath
        logpath='./tmp1'

        import shutil

        if os.path.exists(logpath):
            shutil.rmtree(logpath)
        if os.path.exists('./tmp2'):
            shutil.rmtree('tmp2')


        if not os.path.exists(logpath):
            os.mkdir('tmp1')
            os.mkdir('tmp2')
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
        global  baseS
        baseS = cls.baseS



    def setUp(self):
        pass
    def test_Login(self):
        baseS.find('ogin:', 30)
        baseS.send('syu')
        baseS.find('assword', 30)
        baseS.send('yxw123')
        baseS.find('~', 30)

        baseS.info('login done')
        baseS.debug('this is a test debug message')
        baseS.error('error message example')
        baseS.send('ping localhost')
        import time
        c = 30
        while c:
            print(baseS.show())
            c-=1
            time.sleep(0.1)
        baseS.find('.*')

        newpath= './tmp2'
        if not os.path.exists('./tmp2'):

            os.mkdir( newpath)

        baseS.openLogfile(newpath)

        baseS.send('c',Ctrl=True)

        self.assertRaises(Exception, baseS.find, 'abc', 0.01)

        baseS.SessionAlive=False
        print 'done'


    @classmethod
    def tearDownClass(cls):
        del cls.baseS






if __name__ == '__main__':
    unittest.main()