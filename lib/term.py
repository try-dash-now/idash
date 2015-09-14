__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''
a term is an interface to interoperate with Software/Device Under Test/Used
provides:
1. command sent to software/device
2. show the output, just the updated recently
3. searching given pattern from a given range, e.g. right after last command entered
'''

class term(object)
    '''
    streamOut:  string of Software/Device's output, __init__ will set it to ''
    idxSearch:  number, based on 0, default is 0, it's the index of streamOut, and point to where to find the pattern
                right after this index.
                function Send(will move it to the end of streamOut
                function Find will move idxSearch to index where is right after the pattern in streamOut
    idxUpdate:  number, 0-based, default is 0, point to index of streamOut, when the last call of function Print
                function Prind will move it to the end of streamOut
    attr     :  the attributes gave by caller
    logfile  :  the log file, which named as name.log'''
    streamOut   = None
    idxSearch   =   0
    idxUpdate   =   0
    attr        = None
    logfile     = None
    def __init__(self, name, attr =None, logpath= None):
        '''
        initializing the term
        name:       string, the term's name
        attr:       a dict, the attributes of term
        logpath:    string, the path of the log file for this ter
        '''
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




