#! /usr/bin/env python
# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/10/6 
this is the case runner
'''

import math
import os, sys,traceback,datetime,time,re,pprint
import threading
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)

from common import  csvfile2array
if __name__ == "__main__":
    returncode = 0
    caseFail=0
    CaseErrorMessage =''
    try:
        import sys
        benchfile, cfa1_name ,        cfa2_name , cable_length1, cable_length2, cable_length3 =sys.argv[1:7]
        #cr.py casefile benchfile segment [arg1 arg2 ...argN] logpath
        if len(sys.argv)>7:
            defaultlogdir= sys.argv[-1]
        else:
            defaultlogdir ='./log'

        from runner import case_runner, initDUT, createLogDir      ,createLogger

        if not os.path.exists(defaultlogdir):
            os.mkdir(defaultlogdir)
        #defaultlogdir+='/ut_runner'
        casename = 'blv_loop_len'
        casefolder = createLogDir(casename,defaultlogdir)
        logger = createLogger(casename, casefolder)


        from common import bench2dict
        #benchfile = './bench.csv'
        bench =bench2dict(benchfile)


        #ldut = list(['sbb62','sbb62debug1'])
        #e7_name, e7debug_name, cfa1_name, cfa2_name = ldut


        def set_cfa(cfa, length, port_range='1:24', waittime =120):
#        try 3: Set CL VG1 1c 2c 3c 4c 5c	Set CL VG1 1c 2c 3c 4c 5c
#try 3: Set length 1:24 ${cableLength}	Length ${cableLength} saved for channel
#try 3: show length 1:24	~#
            #cfa.singleStep('Set CL VG1 1c 2c 3c 4c 5c', 'Set CL VG1 1c 2c 3c 4c 5c', waittime)
            cfa.singleStep('Set length %s %s'%(port_range, str(length)), 'Length %s saved for channel'%str(length), waittime)
            cfa.singleStep('show length 1:24', '~#',waittime)

        ldut = [cfa1_name,cfa2_name]
        errormessage =[]
        duts= initDUT(errormessage,bench, ldut,logger, casefolder)
        cfa1    = duts[cfa1_name]
        cfa2    = duts[cfa2_name]
        range1, range2, range3 ,range4= '1:16', '17:24','1:8','9:24'
        set_cfa(cfa1, cable_length1, range1 )
        set_cfa(cfa1, cable_length2, range2)
        set_cfa(cfa2, cable_length2, range3)
        set_cfa(cfa2, cable_length3, range4)



        for dut in duts:
            dut = duts[dut]
            caseFail +=dut.FailFlag
            CaseErrorMessage += '%s: %s%s'%(dut.name,dut.ErrorMessage,'\n')


        from runner import releaseDUTs
        releaseDUTs(duts, logger)
        if caseFail:
            with open('%s/case_error.txt'%casefolder, 'a+') as ef:
                ef.write(CaseErrorMessage)
            print(CaseErrorMessage)
            raise Exception(CaseErrorMessage)
        else:
            print ("\r\n---------------------------------- CASE PASS ----------------------------------")
            os._exit(0)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print ("\r\n---------------------------------- CASE FAIL ----------------------------------")
        with open('%s/case_error.txt'%casefolder, 'a+') as ef:
            ef.write(CaseErrorMessage)

        os._exit(1)

        #exit(1)