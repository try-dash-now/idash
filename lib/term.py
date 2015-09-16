__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''
a term is an interface to interoperate with Software/Device Under Test/Used
provides:
1. command sent to software/device
2. show the output, just the updated recently
3. searching given pattern from a given range, e.g. right after last command entered
'''

class term(object):
    '''
    streamOut:  string of Software/Device's output, __init__ will set it to ''
    idxSearch:  number, based on 0, default is 0, it's the index of streamOut, and point to where to find the pattern
                right after this index.
                function Send(will move it to the end of streamOut
                function Find will move idxSearch to index where is right after the pattern in streamOut
    idxUpdate:  number, 0-based, default is 0, point to index of streamOut, when the last call of function Print
                function Prind will move it to the end of streamOut
    attr     :  the attributes gave by caller
    logfile  :  the log file, which named as name.log
    Connect2SUTDone:
                bool, initial value is False, means didn't complete the process of Device log-in, after log-in, it should be set to True
    attribute   :
                dict, initial is None, and assigned in __init__ as {} or set to the given variable attr
    SessionAlive:
                bool, initial is True, when session is closing, set it to False
    '''
    streamOut   =   None
    idxSearch   =   0
    idxUpdate   =   0
    attr        =   None
    logfile     =   None
    Connect2DUTDone = False
    attribute   =   None
    SessionAlive =  True
    name         =  None #the term name, string
    logger       =  None #parent logger, passed to term, default is logger,no logger needed

    def __del__(self):
        self.SessionAlive=False

    def __init__(self, name, attr =None,logger=None, logpath= None):
        '''
        initializing the term
        name:       string, the term's name
        attr:       a dict, the attributes of term
        logger:     a logger instance, allow this term pass message to parent object
        logpath:    string, the path of the log file for this ter
        '''
        self.name       =   name
        self.logger     =   logger
        if attr:
            self.attribute =attr
        else:
            self.attribute = {}
        import os
        if not logpath:
            logpath = os.getcwd()
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
    def Save2File(self, data, filename=None):
        '''write the data to a given file
        if filename is None, the create a term_name.txt under current path of term logfile
        '''

        pass
    def CallFun(self,functionName,args=[], kwargs={}):
        functionName(*args, **kwargs)

    def formatMsg(self, msg):
        import datetime
        now =datetime.datetime.now()
        msg = '%s\t%s\t%s'%(now.isoformat().replace("T", ' '), self.name, msg)
        print(msg)
        return msg
    def info(self, msg):
        '''
        add info message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.info(msg)

    def error(self, msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.error(msg)
    def debug(self, msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.debug(msg)



