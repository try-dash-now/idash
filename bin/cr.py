#! /usr/bin/env python
# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/10/6 
this is the case runner
'''
import os, sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
if __name__ == "__main__":
    returncode = 0
    try:
        import sys
        #cr.py casefile benchfile segment [arg1 arg2 ...argN] logpath
        defaultlogdir ='../../log'
        argvlen= len(sys.argv)
        if argvlen>5:
            pass
        elif argvlen== 4:
            sys.argv.append(defaultlogdir)
        elif argvlen ==3:
            sys.argv.append("FULL")
            sys.argv.append(defaultlogdir)
        else:
            returncode = True
            errormessage = '''cr.py casefile benchfile segment [arg1 arg2 ...argN] logpath
            casefile:   full path name, otherwise in ./
            benchfile:  the test bench file, full path, otherwise in ./
            segment:    segment of case, not case sensitive, it's one of [full, setup, run, teardown, nosetup, noteardown, f, s, r , t, ns, nr, nt]
            argX   :    argment(s) for substituting in case file
            logpath:    full path name for log, default is ./log/
            '''
            print(errormessage)
        from runner import case_runner, initDUT, createLogDir      ,createLogger
        if os.path.exists(sys.argv[-1]):
            pass
        else:
            sys.argv.append(defaultlogdir)
        if not os.path.exists(defaultlogdir):
            os.mkdir(defaultlogdir)
        defaultlogdir=sys.argv[-1]
        basename_casename = os.path.basename(sys.argv[1])
        casefolder = createLogDir(basename_casename,defaultlogdir)
        logger = createLogger(basename_casename, casefolder)


        from common import bench2dict
        benchfile = sys.argv[2]
        bench =bench2dict(benchfile)


        from Parser import  caseParser
        mode = sys.argv[3]
        case_file_name =os.path.abspath(sys.argv[1])
        cs = caseParser(case_file_name, mode, casefolder)
        casefile = case_file_name
        sdut, lvar, lsetup, lrun, ltear =cs.load(casefile, sys.argv)
        ldut = list(sdut)
        errormessage =[]
        sharedata ={}
        #duts= initDUT(errormessage,bench,ldut,logger, casefolder)#['lnx1', 'lnx2']
        duts= initDUT(errormessage,bench, ldut,logger, casefolder, sharedata)
        seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]

        caseFail, CaseErrorMessage= case_runner(case_file_name,duts,seq, mode, logger,sharedata)

        from runner import releaseDUTs
        releaseDUTs(duts, logger)
        if caseFail:
            with open('%s/case_error.txt'%casefolder, 'a+') as ef:
                ef.write(CaseErrorMessage)
            print(CaseErrorMessage)
            raise Exception(CaseErrorMessage)
        else:
            print('log: "@%s"'%os.path.abspath(casefolder))
            print ("\r\n---------------------------------- CASE PASS ----------------------------------")
            os._exit(0)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print('log: <@%s>'%os.path.abspath(casefolder))
        print ("\r\n---------------------------------- CASE FAIL ----------------------------------")
        os._exit(1)
        #exit(1)