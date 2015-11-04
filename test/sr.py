#! /usr/bin/env python
#  -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/10/7 
'''


import os, sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)
if __name__ == "__main__":
    #sr.py suite_file range [arg1 arg2 ...]
    import re
    from Parser import suiteParser
    from runner import createLogDir
    suitefile =sys.argv[1]
    name = '-'.join(sys.argv[1:])
    name = re.sub('[^\w\-_]','-',name)
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
    suitelogdir = './log'
    rangelist = sys.argv[2]
    arglist = sys.argv[3:]
    if not os.path.exists(suitelogdir):
        os.mkdir(suitelogdir)

    suitelogdir = createLogDir(name, suitelogdir)
    st = suiteParser(name, suitelogdir)
    lstRange = GetRange(rangelist )
    suite= st.load(suitefile, arglist, lstRange)

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
    from runner import run_case_in_suite , releaseDUTs , initDUT,case_runner, createLogDir

    def run1case(benchfile, benchinfo, dut_pool ):
        errormessage = ''
        caselogger = createLogger('caselog.txt', logdir)
        try:
            import re
            patDash  = re.compile('\s*(python |python[\d.]+ |python.exe |)\s*cr.py\s+(.+)\s*', re.DOTALL|re.IGNORECASE)
            m =  re.match(patDash, cmd)
            returncode = 0
            if m:

                argstring = m.group(2)
                import shlex
                lstArg = shlex.split(argstring)
                #0-case.csv, 1-bench, 2-mode, 4...-2- args
                casefile = lstArg[0]
                case_benchfile = lstArg[1]
                case_mode       = lstArg[2]
                case_args= lstArg
                case_args.insert(0,'cr.py')
                bench = benchinfo
                if case_benchfile!=benchfile:
                    from common import bench2dict
                    caselogger.info('loading a new bench:%s'%case_benchfile)
                    bench =bench2dict(case_benchfile)
                    benchfile = case_benchfile
                    caselogger.info('releasing duts in old dut_pool')
                    releaseDUTs(dut_pool, logger)
                    dut_pool ={}
                from Parser import  caseParser
                caselogger.info('loading case: %s'% casename)
                cs = caseParser(casename, case_mode, logdir, caselogger)
                sdut, lvar, lsetup, lrun, ltear =cs.load(casefile, case_args)
                ldut = list(sdut)
                newduts= []
                oldduts = []
                for nd in ldut:
                    if dut_pool.has_key(nd):
                        oldduts.append(nd)
                    else:
                        newduts.append(nd)

                for od in oldduts:
                    dut_pool[od].openLogfile(logdir)
                errormessage =[]
                duts= initDUT(errormessage,bench,newduts,logger, logdir)

                for k in duts.keys():
                    dut_pool[k]=duts[k]

                for key in duts.keys():
                    if dut_pool.has_key(key):
                        continue
                    else:
                        dut_pool[key]= duts[key]

                seq = [cs.seqSetup, cs.seqRun, cs.seqTeardown]
                caselogger.info('starting to run case: %s'%cmd)
                returncode, STRerrormessage= case_runner(casename,dut_pool,seq, case_mode, caselogger)

                if returncode:
                    caselogger.error('Case Failed:%s'%STRerrormessage)
                    errormessage.append(STRerrormessage)
                else:
                    caselogger.info('Case PASS')

            else:
                import subprocess
                pp =None

                if cmd.startswith('[\w_-]+.py') :
                    exe_cmd ='python '+ cmd+" "+logdir
                    caselogger.info('running case: %s'%exe_cmd)
                    pp = subprocess.Popen(args = exe_cmd ,shell =True)

                import time
                ChildRuning = True
                first =True
                while ChildRuning:
                    if pp.poll() is None:
                        interval = 1
                        if first:
                            first=False
                        time.sleep(interval)
                    else:
                        ChildRuning = False

                returncode = pp.returncode

        except Exception as e:

            if returncode ==0:
                returncode =1

            import traceback
            errormessage = '%s\n%s'%(e.__str__(),traceback.format_exc())
            caselogger.error('Case FAIL')
            caselogger.error(errormessage)
        return  returncode, errormessage, benchfile,bench, dut_pool

    def array2html(reportname, ArgStr, CaseRangeStr, TOTAL,CASERUN, CASEPASS,CASEFAIL, CASENOTRUN, Report):
        PPASS = '%.0f'%((CASEPASS*100.0)/CASERUN*1.0)+'''%'''
        PFAIL = '%.0f'%((CASEFAIL*100.0)/CASERUN*1.0)+'''%'''
        CASENOTRUN  = TOTAL - CASEPASS-CASEFAIL
        PNOTRUN = '%.0f'%((CASENOTRUN*100.0) /TOTAL*1.0)+'''%'''


        response ="""
    <HTML>
    <HEAD>
    <TITLE>Suite Test Report</TITLE>
    </HEAD>
    <BODY>
    <table cellspacing="1" cellpadding="2" border="1">
    <tr><td>SUITE NAME</td><td>ARGURMENTS</td><td>CASE RANGE</td></tr>
    <tr><td>%s</td><td>%s</td><td>%s</td></tr>
    </table>
    <br><br>

    <table cellspacing="1" cellpadding="2" border="1">
    <tr>
    <td>TOTAL CASE</td><td bgcolor="#00FF00">PASS</td><td bgcolor="#FF0000">FAIL</td><td bgcolor="#0000FF">NOT RUN</td>
    </tr>
    <tr>
    <td>%d</td><td bgcolor="#00FF00" >%d</td><td bgcolor="#FF0000">%d</td><td  bgcolor="#0000FF">%d</td>
    </tr>
    <tr>
    <td> </td><td>%s</td><td>%s</td><td>%s</td>
    </tr>
    </table>
    <BR>
    <BR>
    <table cellspacing="1" cellpadding="2" border="1">
    """%(reportname, CaseRangeStr, ArgStr ,TOTAL, CASEPASS, CASEFAIL, CASENOTRUN, PPASS,PFAIL,PNOTRUN)

        response = response+ '''<tr><td>No.</td><td>Result</td><td>Case Name</td><td>Duration(s)</td><td>Line No</td><td>Error Message</td></tr>'''
        #NewRecord = [index,caseResult,caseline[2][1], errormessage,logdir, LineNo]
        for result in Report:
            index,caseResult,caseLine, errormessage,logdir, LineNo ,ExecutionDuration=result
            if errormessage ==[]:
                errormessage =''
            else:
                errormessage = ''.join([x for x in errormessage])
            errormessage = re.search('\*ERROR MESSAGE:(.*?)\*Traceback',errormessage,re.IGNORECASE|re.DOTALL)
            if errormessage:
                errormessage= errormessage.group(1).replace('*\t','')
            bgcolor="#00FF00"
            if caseResult=='FAIL':
                bgcolor = "#FF0000"

            response = response +"""<tr>
            <td>%d</td>
            <td bgcolor="%s"><a target="+BLANK" href="%s">%s</td>
            <td><a target="+BLANK" href="%s">%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            </tr>
    """%(index,bgcolor,logdir,caseResult,logdir,caseLine, ExecutionDuration, LineNo, errormessage)




        return response+"""</table>
    <br />
    <br />
    </body></html>"""






    import time
    returncode =1
    errormessage =''
    suiteStartTime = time.time()
    statsPass =0
    statsFail =0
    lstFailCase = []
    for caseline in suite:
        caseStartTime = time.time()
        LineNo,FailAction,[FuncName,cmd ]=caseline
        logger.info('to run case: index %d, name: %s, failAction: %s'%(LineNo,cmd, FailAction))

        casename ='%d'%caseline[0]#index
        index+=1
        import os
        logpath = suitelogdir+"/%s"%casename
        logger.info('creating logdir: %s'%logpath)
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logdir = createLogDir(casename, logpath)

        if FuncName == run_case_in_suite:

            import re
            patDash  = re.compile('\s*(python |python[\d.]+ |python.exe |)\s*cr.py\s+(.+)\s*', re.DOTALL|re.IGNORECASE)
            m =  re.match(patDash, cmd)
            returncode = 0
            logger.info('running case: %s'%cmd)
            returncode , errormessage ,benchfile, benchinfo, dut_pool = run1case(benchfile, benchinfo, dut_pool )
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

        NewRecord = [index-1,caseResult,caseline[2][1], errormessage,'../'+logdir, LineNo,ExecutionDuration]
        print("RESULT:", NewRecord)
        print('Pass:',statsPass, 'Fail', statsFail)
        #reportname, ArgStr, CaseRangeStr, TOTAL,CASERUN, CASEPASS,CASEFAIL, CASENOTRUN, Report,htmllogdir
        report.append(NewRecord)
        htmlstring = array2html(suitefile,rangelist,','.join(arglist), suite.__len__(),statsFail+statsPass,statsPass,statsFail, suite.__len__()-statsFail-statsPass,report)
        reportfilename = './log/%s.html'%(name)
        with open(reportfilename, 'wb') as f:
            f.write(htmlstring.encode(encoding='utf_8', errors='strict'))
        if returncode:
            if FailAction.strip().lower()=='break':
                break
            else:
                continue

        casename='%d'%index
        logdir ='./log/'+suitefile+'/'+casename



    #if dut_pool.__len__()!={}:
    releaseDUTs(dut_pool, logger)


    from runner import concurrent
    parseResult = ''
    for i in suite:
        if i[2][0]!=concurrent:
            #print(i)
            parseResult+='%d, %s, %s, %s\n'%(i[0], i[1], i[2][0].func_name, ' ,'.join([str(x) for x in i[2][1:]]))
        else:
            #print(i)
            for ii in i[2][1]:
                #print('\t'+str(i[0])+' '+str(ii))
                parseResult+='\t%d, %s, %s, %s\n'%(i[0],i[2][0].func_name,ii[0].func_name, ' ,'.join([str(x) for x in ii[1:]]) )
    #print(parseResult)
    #print(report)
    print('Pass:',statsPass, 'Fail', statsFail)
    os._exit(0)

