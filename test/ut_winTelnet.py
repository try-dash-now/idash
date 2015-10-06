__author__ = 'Sean Yu'
'''created @2015/9/14''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
#pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))


logpath = './log'

cmd = 'telnet 192.168.1.113'
#cmd = 'telnet cdc-dash'
import shutil

if os.path.exists(logpath):
    shutil.rmtree(logpath)


class Test_winTerm(unittest.TestCase):

    def test_Login2Linux(self):
        from winTelnet import winTelnet
        name= 'linux'
        import os

        #cmd = 'telnet 192.168.1.113'
        #cmd = 'telnet cdc-dash'
        #cmd = 'telnet 10.245.48.20'#great wall e7-20
        #cmd = 'telnet 10.245.69.106'#ryi
        attr={'TIMEOUT':180,'LOGIN': '../bench/lnx.login','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        logger=None
        global logpath
        if not os.path.exists(logpath):
            os.mkdir(logpath)
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
        baseS = winTelnet(name,attr,logger , logpath)
        baseS.login()

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

        newpath= logpath+'/cas1_wintelnet'
        if not os.path.exists(newpath):

            os.mkdir( newpath)

        baseS.openLogfile(newpath)

        baseS.send('c',Ctrl=True)

        self.assertRaises(Exception, baseS.find, 'abc', 0.01)

        baseS.SessionAlive=False
        print 'done'

    def tes1t_Login2E7(self):
        name = 'e7'
        cmd = 'telnet 10.245.3.16'
        attr = {'TIMEOUT':180,'LOGIN': '../bench/e7.login','CMD':cmd, 'LINEEND':'\r\n', 'EXP':'name:' }
        from winTelnet import winTelnet
        logger = None
        logpath = './log/winTelnet_Login2E7'
        e7 = winTelnet(name,attr,logger , logpath)
        e7.login()
        e7.__del__()
        print 'done'







if __name__ == '__main__':
    unittest.main()