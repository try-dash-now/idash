#! /usr/bin/env python
#  -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/10/7 
'''


import os, sys
from pprint import pprint
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
if __name__ == "__main__":
    #sr.py suite_file range [arg1 arg2 ...]
    import re,datetime
    from Parser import suiteParser
    from runner import createLogDir

    suitefile =sys.argv[1]
    name = '-'.join(sys.argv[1:])
    name = re.sub('[^\w\-_]','-',name)[:60]+' '+datetime.datetime.now().isoformat(':').replace(':','')
    name = re.sub('-+', '-', name)
    name = re.sub('^-*', '', name)
    def  GetRange(caserange='all'):
        if str(caserange).strip().lower()=='all':
            caserange = 'all'
        else:
            caserange = str(caserange).strip()
            caserange = str(caserange).split(',')
            drange = []
            for i in caserange:
                if str(i).find('-')!=-1:
                    s,e =str(i).split('-')
                    i = list(range(int(s)-1,int(e)))
                else:
                    i =[int(i)-1]
                drange =drange+i
            caserange= sorted(drange)
        CaseRange=caserange
        return CaseRange
    suitelogdir = '../../log'
    rangelist = sys.argv[2]
    arglist = sys.argv[3:]
    if not os.path.exists(suitelogdir):
        os.mkdir(suitelogdir)

    suitelogdir = createLogDir(name, suitelogdir)
    st = suiteParser(name, suitelogdir)
    lstRange = GetRange(rangelist )
    statsTotalCase, suite= st.load(suitefile, arglist, lstRange)

    benchfile =''
    benchinfo ={}
    from runner import createLogger
    logger = createLogger('suite.txt', suitelogdir)
    logger.info('suite name\t%s'%(sys.argv[1]))
    logger.info('suite range\t%s'%(sys.argv[2]))

    index = 1
    for i in sys.argv[3:]:
        logger.info('arg%d\t%s'%(index, i))
        index+=1
    report = []
    dut_pool={}
#    3, break, run_case_in_suite, rc.py2 home_case.csv home.csv full
#	9, concurrent, loop, 2 ,no_stop ,rc.py5 home_case.csv home.csv full
#	9, concurren,FailAction,FuncName,cmd =case, run_case_in_suite, rc.py7 home_case.csv home.csv full
    index = 1
    from runner import run_case_in_suite , releaseDUTs , initDUT,case_runner, createLogDir, array2html, run1case

    import time, re
    returncode =1
    errormessage =''
    suiteStartTime = time.time()
    suiteEndTime = time.time()
    statsPass =0
    statsFail =0
    lstFailCase = []

    htmlstring = array2html(suitefile,rangelist,','.join(arglist), statsTotalCase,statsFail+statsPass,statsPass,statsFail, statsTotalCase-statsFail-statsPass,report, suiteStartTime, suiteEndTime)
    reportfilename = '../../log/%s.html'%(name)
    with open(reportfilename, 'wb') as f:
        f.write(htmlstring.encode(encoding='utf_8', errors='strict'))
    try:
        for caseline in suite:
            breakFlag=False
            caseStartTime = time.time()
            LineNo,FailAction,[FuncName,cmd ]=caseline
            logger.info('to run case: index %d, name: %s, failAction: %s'%(LineNo,cmd, FailAction))
            from runner import concurrent
            print cmd
            if FuncName == run_case_in_suite:
                casename ='%d-%s'%(caseline[0], re.sub('[^\w\-_.]','-',cmd[:80]))#index

            elif FuncName == concurrent:
                casename ='%d-%s'%(caseline[0], re.sub('[^\w\-_.]','-',cmd[0][4][:80]))#index
            casename = re.sub('-+','-',casename)
            casename = re.sub('^-*','',casename)
            index+=1
            import os
            logpath = suitelogdir#+"/%s"%casename
            logger.info('creating logdir: %s'%logpath)
            if not os.path.exists(logpath):
                os.mkdir(logpath)

            shareData ={}
            if FuncName == run_case_in_suite:
                suite_dir_name = os.path.basename(logpath)
                logdir = '%s/%s'%(logpath,casename)
                if not os.path.exists(logdir):
                    os.mkdir(logdir)
                #logdir =createLogDir(casename, logpath)# logpath#


                returncode = 0
                logger.info('running case: %s'%cmd)

                returncode , errormessage ,benchfile, benchinfo, dut_pool = run1case(casename, cmd, benchfile, benchinfo, dut_pool, logdir, logger ,shareData)
                caseEndTime = time.time()
                ExecutionDuration = caseEndTime-caseStartTime
                caseResult = 'PASS'

                if returncode:
                    logger.error('FAIL\t%s'%cmd)
                    logger.error(errormessage)
                    caseResult ='FAIL'
                    lstFailCase.append(caseline)
                    statsFail+=1
                else:
                    logger.info('PASS\t%s'%cmd)
                    statsPass+=1
                logdir = '%s/%s'%(suite_dir_name, casename)
                NewRecord = [index-1,caseResult,caseline[2][1], errormessage,logdir, LineNo,ExecutionDuration,caseStartTime,caseEndTime ]
                print("RESULT:")
                pprint(NewRecord)


                #reportname, ArgStr, CaseRangeStr, TOTAL,CASERUN, CASEPASS,CASEFAIL, CASENOTRUN, Report,htmllogdir
                report.append(NewRecord)
                if returncode:
                    if FailAction.strip().lower()=='break':
                        breakFlag=True

            elif FuncName == concurrent:
                conCaseTotal, conCasePass, conCaseFail, conReport, conLstFailCase , breakFlag=concurrent(index-1, logpath, caseline[2][1],report, logger, shareData)
                statsPass+=conCasePass
                statsFail+=conCaseFail
                for x in conLstFailCase:
                    lstFailCase.append(x)

            print('Pass:',statsPass, 'Fail', statsFail)
            suiteEndTime = time.time()
            htmlstring = array2html(suitefile,rangelist,','.join(arglist), statsTotalCase,statsFail+statsPass,statsPass,statsFail, statsTotalCase-statsFail-statsPass,report, suiteStartTime, suiteEndTime)
            reportfilename = '../../log/%s.html'%(name)
            with open(reportfilename, 'wb') as f:
                f.write(htmlstring.encode(encoding='utf_8', errors='strict'))

            if breakFlag:
                break
            casename='%d'%index
            logdir ='../../log/'+suitefile+'/'+casename
    except KeyboardInterrupt:
        try:
            print('Pass:',statsPass, 'Fail', statsFail)
            suiteEndTime = time.time()
            htmlstring = array2html(suitefile,rangelist,','.join(arglist), statsTotalCase,statsFail+statsPass,statsPass,statsFail, statsTotalCase-statsFail-statsPass,report, suiteStartTime, suiteEndTime)
            reportfilename = '../../log/%s.html'%(name)
        except:
            pass





    #if dut_pool.__len__()!={}:
    releaseDUTs(dut_pool, logger)

    print('#'*80)
    print('Pass:',statsPass, 'Fail', statsFail)
    os._exit(0)

