__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''a windows telnet session'''
from telnetlib import Telnet as spawn
from term import term
import threading
class winTelnet(term, spawn):
    sock =None
    lenRawq=0
    def __init__(self, name, attr =None, logpath= None):
        term.__init__(self, name,attr,logpath)

        host=""
        port=23
        import re as sre
        reHostOnly=  sre.compile('\s*telnet\s+([\d.\w\-_]+)\s*',sre.I)
        reHostPort = sre.compile('\s*telnet\s+([\d.\w]+)\s+(\d+)', sre.I )
        command = attr.get('CMD')
        m1=sre.match(reHostOnly, command)
        m2=sre.match(reHostPort, command)
        if m1:
            host= m1.groups(1)[0]
        elif m2:
            host= m2.groups(1)[0]
            port= m2.groups(2)[0]
        import socket
        timeout = 30
        self.sock = socket.create_connection((host, port), timeout)
        spawn.__init__(self, str(host), port)
        th =threading.Thread(target=self.ReadDataFromSocket)
        th.start()

    def ReadDataFromSocket(self):
        while 1:
            self.fill_rawq()
            len = self.rawq.__len__()
            if len > self.lenRawq:
                self.logfile.write(self.rawq[self.lenRawq:])

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
