__author__ = 'Sean Yu'
'''created @2015/9/29''' 

import os

def createLogger(name, logpath='./'):
    #create  a unique folder for case, and logfile for case
    if not os.path.exists(logpath):
        os.mkdir(logpath)
    import logging
    logfile = logpath+"/%s.log"%(name)
    logger = logging.Logger(name,logging.DEBUG)
    hdrlog = logging.FileHandler(logfile)
    hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
    logger.addHandler(hdrlog )
    return logger

def createCaseLogDir(casename,logpath='./'):
    import re, datetime
    fullname = casename[:80]
    name = re.sub('\W', '.', fullname)
    tm = datetime.datetime.now().isoformat('_')
    tm =  re.sub('\W', '.', tm)
    name = name+'-'+tm
    logpath = logpath+'/'+ name
    if not os.path.exists(logpath):
        os.mkdir(logpath)

def initDUT(bench, dutnames, logger=None, casepath='./'):

    def connect2dut(dutname, dut_attr, logger=None,path='./'):
        if dut_attr["SUT"].strip() =='':
            if os.name!='nt':
                raise  ImportError('need implment default session for non-NT')#sutattr['SUT'] ='Session'
            else:
                dut_attr['SUT'] ='winTelnet'

        classname = dut_attr["SUT"]
        ModuleName = __import__(classname)
        ClassName = ModuleName.__getattribute__(classname)
        ses= ClassName(dutname, dut_attr,logger=logger ,logpath = path)
        ses.login()
        return  ses
    import threading
    dutobjs=[]

    for dutname in dutnames:
        th = threading.Thread(target= connect2dut, args =[dutname, bench[dutname],logger, casepath])
        dutobjs.append(th)
    for th in dutobjs:
        th.start()

    for th in dutobjs:
        th.join(60*5)

    return  dutobjs


def case_runner(dictDUTs, case_seq, mode='full'):
    pass

def suite_runner(dictDUTs, case_seqs):
    pass

errorlogger = None
