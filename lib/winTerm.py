__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''a windows telnet session'''
from telnetlib import Telnet as spawn
from term import term

class winTerm(spawn, term):
    def __init__(self, name, attr =None, logpath= None):
        import os
        log = os.path.abspath(logpath)
        log= '%s%s%s'%(log,os.path.sep,'%s.log'%name)
        self.logfile = open(log, "wb")
    def Send(self, cmd):
        '''send a command to Software/Device, add a line end
        move idxSearch to the end of streamOut
        '''
        pass
    def Find(self, pattern, timeout = 1.0):
        '''find a given patten within given time(timeout)
        if pattern found, move idxSearch to index where is right after the pattern in streamOut
        return the content which matched the pattern
        otherwise return None
        '''
        pass
    def Print(self):
        '''return the delta of streamOut from last call of function Print,
        and move idxUpdate to end of streamOut'''
        pass
