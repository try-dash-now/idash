__author__ = 'Sean Yu'
'''created @2015/9/30''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))
from winTelnet import winTelnet
class e7(winTelnet):
    def __init__(self,name,attr,logger, logpath, shareData):
        winTelnet.__init__(self, name,attr,logger, logpath, shareData)
        self.attribute['PROMPT']='>|#|>>>'
    def setTime(self, tm =None):
        if tm:
            self.send('set time %s'%str(tm))
        else:
            self.send(self.getValue('tm'))

