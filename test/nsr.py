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
    from Parser import suiteParser
    from runner import createLogDir
    suitefile =sys.argv[1]
    name = '-'.join(sys.argv[1:])
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
    logger =None
    report = []
    dut_pool={}
#    3, break, run_case_in_suite, rc.py2 home_case.csv home.csv full
#	9, concurrent, loop, 2 ,no_stop ,rc.py5 home_case.csv home.csv full
#	9, concurren,FailAction,FuncName,cmd =case, run_case_in_suite, rc.py7 home_case.csv home.csv full
    index = 1
    from runner import run_case_in_suite , releaseDUTs , initDUT,case_runner, createLogDir

    def run1case(benchfile, benchinfo, dut_pool ):
        errormessage = ''
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

                if case_benchfile!=benchfile:
                    from common import bench2dict
                    bench =bench2dict(case_benchfile)
                    benchfile = case_benchfile
                    releaseDUTs(dut_pool)
                    dut_pool ={}
                from Parser import  caseParser
                cs = caseParser(casename, case_mode, logdir)
                sdut, lvar, lsetup, lrun, ltear =cs.load(casefile, case_args)
                ldut = list(sdut)
                newduts= []
                for nd in ldut:
                    if dut_pool.has_key(nd):
                        continue
                    else:
                        newduts.append(nd)
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

                returncode= case_runner(casename,dut_pool,seq, case_mode)


            else:
                import subprocess
                pp =None
                if cmd.startswith('\w+.py') :
                    exe_cmd ='python '+ cmd+" "+logdir
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
            import traceback
            errormessage = '%s\n%s'%(e.__str__(),traceback.format_exc())
        return  returncode, errormessage, benchfile,benchinfo, dut_pool
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
        casename ='%d'%index
        index+=1
        import os
        logpath = suitelogdir+"/%s"%casename
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        logdir = createLogDir(casename, logpath)

        if FuncName == run_case_in_suite:

            import re
            patDash  = re.compile('\s*(python |python[\d.]+ |python.exe |)\s*cr.py\s+(.+)\s*', re.DOTALL|re.IGNORECASE)
            m =  re.match(patDash, cmd)
            returncode = 0
            returncode , errormessage ,benchfile, benchinfo, dut_pool = run1case(benchfile, benchinfo, dut_pool )
        caseEndTime = time.time()
        ExecutionDuration = caseEndTime-caseStartTime
        caseResult = 'PASS'

        if returncode:
            caseResult ='FAIL'
            lstFailCase.append(caseline)
            statsFail+=1
        else:
            statsPass+=1

        NewRecord = [index,caseResult,caseline, errormessage,logdir, LineNo]
        print("RESULT:", NewRecord)
        print('Pass:',statsPass, 'Fail', statsFail)
        report.append(NewRecord)
        if returncode:
            if FailAction.strip().lower()=='break':
                break
            else:
                continue

        casename='%d'%index
        logdir ='./log/'+suitefile+'/'+casename
        casename, benchinfo,logger, FailAction,logdir, cmd


    #if dut_pool.__len__()!={}:
    releaseDUTs(dut_pool)


    from runner import concurrent
    parseResult = ''
    for i in suite:
        if i[2][0]!=concurrent:
            print(i)
            parseResult+='%d, %s, %s, %s\n'%(i[0], i[1], i[2][0].func_name, ' ,'.join([str(x) for x in i[2][1:]]))
        else:
            print(i)
            for ii in i[2][1]:
                print('\t'+str(i[0])+' '+str(ii))
                parseResult+='\t%d, %s, %s, %s\n'%(i[0],i[2][0].func_name,ii[0].func_name, ' ,'.join([str(x) for x in ii[1:]]) )
    print(parseResult)
    os._exit(0)

