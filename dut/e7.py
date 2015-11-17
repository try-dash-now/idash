__author__ = 'Sean Yu'
'''created @2015/9/30''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))
from winTelnet import winTelnet
class e7(winTelnet):
    def __init__(self,name,attr,logger, logpath):
        winTelnet.__init__(self, name,attr,logger, logpath)
        self.attribute['PROMPT']='>|#|>>>'

