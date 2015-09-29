__author__ = 'Sean Yu'
'''created @2015/9/29''' 


def createLogger(name, logpath='./')
    #create  a unique folder for case, and logfile for case
    import os
    if not os.path.exists(logpath):
        logpath = os.getcwd()
    import re, datetime
    fullname = name[:80]+datetime.datetime.now().isoformat('_')
    name = re.sub('\W', '.', fullname)
    logpath = logpath+'/'+ name
    os.mkdir(logpath)
    import logging
    logfile = logpath+"/tc.log"
    logger = logging.Logger(name,logging.DEBUG)
    hdrlog = logging.FileHandler(logfile)
    hdrlog .setFormatter(logging.Formatter('%(asctime)s -%(levelname)s:    %(message)s'))
    logger.addHandler(hdrlog )
    return logger

def createCaseLogDir(casename, path='./'):
    pass

def initDUT(bench, dutnames, casepath='./'):
    pass

def case_runner(dictDUTs, case_seq, mode='full'):
    pass

def suite_runner(dictDUTs, case_seqs):
    pass

errorlogger = None
