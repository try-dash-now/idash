__author__ = 'Sean Yu'
'''created @2015/10/26'''
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

class test_IxiaNetwork(unittest.TestCase):

    def test_Ixia(self):







if __name__ == '__main__':
    unittest.main()
