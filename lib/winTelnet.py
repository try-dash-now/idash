__author__ = 'Sean Yu'
'''created @2015/9/14'''
'''a windows telnet session'''
from telnetlib import Telnet as spawn
import socket
import select
# Tunable parameters
DEBUGLEVEL = 0

# Telnet protocol defaults
TELNET_PORT = 23

# Telnet protocol characters (don't change)
IAC  = chr(255) # "Interpret As Command"
DONT = chr(254)
DO   = chr(253)
WONT = chr(252)
WILL = chr(251)
theNULL = chr(0)

SE  = chr(240)  # Subnegotiation End
NOP = chr(241)  # No Operation
DM  = chr(242)  # Data Mark
BRK = chr(243)  # Break
IP  = chr(244)  # Interrupt process
AO  = chr(245)  # Abort output
AYT = chr(246)  # Are You There
EC  = chr(247)  # Erase Character
EL  = chr(248)  # Erase Line
GA  = chr(249)  # Go Ahead
SB =  chr(250)  # Subnegotiation Begin


# Telnet protocol options code (don't change)
# These ones all come from arpa/telnet.h
BINARY = chr(0) # 8-bit data path
ECHO = chr(1) # echo
RCP = chr(2) # prepare to reconnect
SGA = chr(3) # suppress go ahead
NAMS = chr(4) # approximate message size
STATUS = chr(5) # give status
TM = chr(6) # timing mark
RCTE = chr(7) # remote controlled transmission and echo
NAOL = chr(8) # negotiate about output line width
NAOP = chr(9) # negotiate about output page size
NAOCRD = chr(10) # negotiate about CR disposition
NAOHTS = chr(11) # negotiate about horizontal tabstops
NAOHTD = chr(12) # negotiate about horizontal tab disposition
NAOFFD = chr(13) # negotiate about formfeed disposition
NAOVTS = chr(14) # negotiate about vertical tab stops
NAOVTD = chr(15) # negotiate about vertical tab disposition
NAOLFD = chr(16) # negotiate about output LF disposition
XASCII = chr(17) # extended ascii character set
LOGOUT = chr(18) # force logout
BM = chr(19) # byte macro
DET = chr(20) # data entry dutinal
SUPDUP = chr(21) # supdup protocol
SUPDUPOUTPUT = chr(22) # supdup output
SNDLOC = chr(23) # send location
TTYPE = chr(24) # dutinal type
EOR = chr(25) # end or record
TUID = chr(26) # TACACS user identification
OUTMRK = chr(27) # output marking
TTYLOC = chr(28) # dutinal location number
VT3270REGIME = chr(29) # 3270 regime
X3PAD = chr(30) # X.3 PAD
NAWS = chr(31) # window size
TSPEED = chr(32) # dutinal speed
LFLOW = chr(33) # remote flow control
LINEMODE = chr(34) # Linemode option
XDISPLOC = chr(35) # X Display Location
OLD_ENVIRON = chr(36) # Old - Environment variables
AUTHENTICATION = chr(37) # Authenticate
ENCRYPT = chr(38) # Encryption option
NEW_ENVIRON = chr(39) # New - Environment variables
# the following ones come from
# http://www.iana.org/assignments/telnet-options
# Unfortunately, that document does not assign identifiers
# to all of them, so we are making them up
TN3270E = chr(40) # TN3270E
XAUTH = chr(41) # XAUTH
CHARSET = chr(42) # CHARSET
RSP = chr(43) # Telnet Remote Serial Port
COM_PORT_OPTION = chr(44) # Com Port Control Option
SUPPRESS_LOCAL_ECHO = chr(45) # Telnet Suppress Local Echo
TLS = chr(46) # Telnet Start TLS
KERMIT = chr(47) # KERMIT
SEND_URL = chr(48) # SEND-URL
FORWARD_X = chr(49) # FORWARD_X
PRAGMA_LOGON = chr(138) # TELOPT PRAGMA LOGON
SSPI_LOGON = chr(139) # TELOPT SSPI LOGON
PRAGMA_HEARTBEAT = chr(140) # TELOPT PRAGMA HEARTBEAT
EXOPL = chr(255) # Extended-Options-List
NOOPT = chr(0)

from dut import dut
import threading
import os
class winTelnet(dut):#, spawn
    streamOutLock =None

    def __del__(self):
        self.SessionAlive= False
        import time
        time.sleep(0.1)
        if self.sock:
            self.write('quit')
            self.sock.close()
    def __init__(self, name, attr =None,logger=None,  logpath= None, shareData=None):
        dut.__init__(self, name,attr,logger, logpath , shareData)

        host=""
        port=23
        import re as sre
        reHostOnly=  sre.compile('\s*telnet\s+([\d.\w\-_]+)\s*',sre.I)
        reHostPort = sre.compile('\s*telnet\s+([\d.\w]+)\s+(\d+)', sre.I )

        command = self.attribute.get('CMD')
        m1=sre.match(reHostOnly, command)
        m2=sre.match(reHostPort, command)
        if m2:
            host= m2.group(1)
            port= int(m2.group(2))
        elif m1:
            host= m1.group(1)

        #import socket
        #timeout = 30
        #self.sock = socket.create_connection((host, port), timeout)
        self.debuglevel = DEBUGLEVEL
        self.host = host
        self.port = port
        timeout=0.5
        self.timeout = timeout
        self.sock = None
        self.rawq = ''
        self.irawq = 0
        self.cookedq = ''
        self.eof = 0
        self.iacseq = '' # Buffer for IAC sequence.
        self.sb = 0 # flag for SB and SE sequence.
        self.sbdataq = ''
        self.option_callback = None
        self._has_poll = hasattr(select, 'poll')
        if host is not None:
            self.open(str(host), port, timeout)
        self.lockStreamOut =threading.Lock()
        self.lockRelogin =threading.Lock()
        self.streamOut=''
        th =threading.Thread(target=self.ReadDataFromSocket)
        th.start()
        self.debuglevel=0

    def rawq_getchar(self):
        """Get next char from raw queue.

        Block if no data is immediately available.  Raise EOFError
        when connection is closed.

        """
        if not self.rawq:
            self.fill_rawq()
            if self.eof:
                raise EOFError
        c = self.rawq[self.irawq]
        self.irawq = self.irawq + 1
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        return c

    def write(self, buffer):
        """Write a string to the socket, doubling any IAC characters.

        Can block if the connection is blocked.  May raise
        socket.error if the connection is closed.

        """
        buffer =buffer.encode(encoding='utf-8')
        if IAC in buffer:
            buffer = buffer.replace(IAC, IAC+IAC)
        self.msg("send %r", buffer)
        if self.sock:
            self.sock.sendall(buffer)
        super(winTelnet,self).write()

    def msg(self, msg, *args):
        """Print a debug message, when the debug level is > 0.

        If extra arguments are present, they are substituted in the
        message using the standard string formatting operator.

        """
        if self.debuglevel > 0:
            print 'Telnet(%s,%s):' % (self.host, self.port),
            if args:
                print msg % args
            else:
                print msg
    def fill_rawq(self):
        """Fill raw queue from exactly one recv() system call.

        Block if no data is immediately available.  Set self.eof when
        connection is closed.

        """
        if self.sock==0 or self.sock==None:
            return
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        # The buffer size should be fairly small so as to avoid quadratic
        # behavior in process_rawq() above

        buf = self.sock.recv(50)
        self.msg("recv %r", buf)
        self.eof = (not buf)
        self.rawq = self.rawq + buf


    def process_rawq(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.

        """
        buf = ['', '']
        try:
            while self.rawq:
                c = self.rawq_getchar()
                if not self.iacseq:
                    if c == theNULL:
                        continue
                    if c == "\021":
                        continue
                    if c != IAC:
                        buf[self.sb] = buf[self.sb] + c
                        continue
                    else:
                        self.iacseq += c
                elif len(self.iacseq) == 1:
                    # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
                    if c in (DO, DONT, WILL, WONT):
                        self.iacseq += c
                        continue

                    self.iacseq = ''
                    if c == IAC:
                        buf[self.sb] = buf[self.sb] + c
                    else:
                        if c == SB: # SB ... SE start.
                            self.sb = 1
                            self.sbdataq = ''
                        elif c == SE:
                            self.sb = 0
                            self.sbdataq = self.sbdataq + buf[1]
                            buf[1] = ''
                        if self.option_callback:
                            # Callback is supposed to look into
                            # the sbdataq
                            self.option_callback(self.sock, c, NOOPT)
                        else:
                            # We can't offer automatic processing of
                            # suboptions. Alas, we should not get any
                            # unless we did a WILL/DO before.
                            self.msg('IAC %d not recognized' % ord(c))
                elif len(self.iacseq) == 2:
                    cmd = self.iacseq[1]
                    self.iacseq = ''
                    opt = c
                    if cmd in (DO, DONT):
                        self.msg('IAC %s %d',
                            cmd == DO and 'DO' or 'DONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(IAC + WONT + opt)
                    elif cmd in (WILL, WONT):
                        self.msg('IAC %s %d',
                            cmd == WILL and 'WILL' or 'WONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(IAC + DONT + opt)
        except EOFError: # raised by self.rawq_getchar()
            self.iacseq = '' # Reset on EOF
            self.sb = 0
            pass
        self.cookedq = self.cookedq + self.removeSpecChar(buf[0])
        self.sbdataq = self.sbdataq + buf[1]
    def removeSpecChar(self, inputString):

#^@   \x00 \000   0
#^A   \x01 \001   1
#^B   \x02 \002   2
#^C   \x03 \003   3
#^D   \x04 \004   4
#^E   \x05 \005   5
#^F   \x06 \006   6
#^G   \x07 \007   7
#^H   \x08 \010   8
#^I   \x09 \011   9
#^J   \x0a \012  10
#^K   \x0b \013  11
#^L   \x0c \014  12
#^M   \x0d \015  13
#^N   \x0e \016  14
#^O   \x0f \017  15
#^P   \x10 \020  16
#^Q   \x11 \021  17
#^R   \x12 \022  18
#^S   \x13 \023  19
#^T   \x14 \024  20
#^U   \x15 \025  21
#^V   \x16 \026  22
#^W   \x17 \027  23
#^X   \x18 \030  24
#^Y   \x19 \031  25
#^Z   \x1a \032  26
#^[   \x1b \033  27
#^\   \x1c \034  28
#^]   \x1d \035  29
#^^   \x1e \036  30
        inputString = inputString.replace(chr(0x08), '')
        inputString = inputString.replace(chr(0x03), '^C')
        inputString = inputString.replace(chr(0x04), '^D')
        inputString = inputString.replace(chr(0x18), '^X')
        return inputString
    def open(self, host, port=0, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """Connect to a host.

        The optional second argument is the port number, which
        defaults to the standard telnet port (23).

        Don't try to reopen an already connected instance.
        """
        self.eof = 0
        if not port:
            port = TELNET_PORT
        self.host = host
        self.port = port
        self.timeout = timeout

        self.sock = socket.create_connection((host, port), timeout)
    def ReadDataFromSocket(self):
        import time, os
        maxInterval = 60*5
        if self.timestampCmd ==None:
            self.timestampCmd= time.time()
        fail_counter = 0
        while self.SessionAlive:
            self.lockStreamOut.acquire()
            try:
                #if not self.sock:
                #    self.relogin()
                if self.sock:
                    if (time.time()-self.timestampCmd)>maxInterval:
                        self.write(chr(0x08))
                        self.timestampCmd = time.time()
                else:
                    raise Exception('[Errno 10053] An established connection was aborted by the software in your host machine')
                self.fill_rawq()
                self.cookedq=''
                self.process_rawq()
                self.checkLine(self.cookedq)
                self.streamOut+=self.cookedq
                if self.logfile and self.cookedq.__len__()!=0:
                    self.logfile.write(self.cookedq)
                    self.logfile.flush()
                fail_counter = 0
            except Exception, e:
                fail_counter+=1
                if self.debuglevel:
                    print('\nReadDataFromSocket Exception %d:'%(counter)+e.__str__()+'\n')
                #self.lockStreamOut.release()
                if str(e)!='timed out':
                    if str(e) =='[Errno 10053] An established connection was aborted by the software in your host machine' or '[Errno 9] Bad file descriptor'==str(e) or str(e) =='[Errno 10054] An existing connection was forcibly closed by the remote host':
                        #self.lockStreamOut.acquire()

                        try:
                            if self.sock:
                                #self.write('quit\r\n')
                                self.sock.close()
                                self.sock = 0
                                self.eof = 1
                                self.iacseq = ''
                                self.sb = 0
                            self.open(self.host,self.port,self.timeout)
                            if self.autoReloginFlag:
                                th =threading.Thread(target=self.relogin)
                                th.start()


                        except Exception as e:
                            print('\nReadDataFromSocket Exception2 %d:'%(fail_counter)+e.__str__()+'\n')
                    else:
                        print("ReadDataFromSocket Exception: %s"%(str(e)))
                        import traceback
                        msg = traceback.format_exc()
                        print(msg)
                        self.error(msg)
            self.lockStreamOut.release()







    def show(self):
        '''return the delta of streamOut from last call of function Print,
        and move idxUpdate to end of streamOut'''
        newIndex = self.streamOut.__len__()
        result = self.streamOut[self.idxUpdate  :  newIndex+1]
        self.idxUpdate= newIndex
        #print('print::%d'%result.__len__())

        if result!='':
            result= self.colorString(result)
            print('\t%s'%(result.replace('\n', '\n\t')))
        return result


    def relogin(self):
        #time.sleep(3)
        self.lockRelogin.acquire()
        try:
            if self.counterRelogin>0:
                self.lockRelogin.release()
                return
            self.counterRelogin+=1
            self.loginDone=False
            if self.sock:
                #self.write('quit\n\r\n')
                self.sock.close()
                self.sock = 0
                self.eof = 1
                self.iacseq = ''
                self.sb = 0
            self.open(self.host,self.port,self.timeout)
            import time
            time.sleep(1)
            self.login()
            self.counterRelogin-=1
            self.loginDone=True
        except Exception as e:
            self.counterRelogin-=1
            self.lockRelogin.release()
            raise  e
        self.lockRelogin.release()


