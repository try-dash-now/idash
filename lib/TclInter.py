__author__ = 'Sean Yu'
'''created @2015/7/3'''
from  Tkinter import Tk,Tcl
from baseSession import baseSession
class TclInter(baseSession):
    tclInter=None
    def __init__(self, name,attrs,logger=None, logpath=None):
        baseSession.__init__(self, name, attrs, logger, logpath)
    def __del__(self):
        try:
            if self.tclInter is not None:
                self.tclInter.eval('''
    rename  original_puts puts
    ''')
        except:
            pass

    def openTcl(self):
        if self.tclInter is not None:
            self.tclInter.quit()
        self.tclInter = Tcl( None, None, 'Tk', 0)
        self.tclInter.eval('''
rename puts original_puts
proc puts {args} {
    if {[llength $args] == 1} {
        return "=> [lindex $args 0]"
    } else {
        eval original_puts $args
    }
}
''')

    def send(self, command , Ctrl=False, Alt=False ):
        if self.tclInter is None:
            self.OpenTcl()
        command =command.strip()
        print('tcl command: %s'%command)
        self.output =self.tclInter.eval(command)
        output ="%s\n%s\n"%(command, self.output)
        self.seslog.write(output)
        self.seslog.flush()
        print(output)
        return  self.output
    def find(self,pattern, wait =None, noWait=False):
        import re
        p =re.compile(pattern, re.I|re.M)
        m =re.search(p, self.output)
        if m:
            pass
        else:
            msg = 'not found pattern: %s'%pattern
            raise Exception(msg)
