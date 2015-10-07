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
        if str(caserange).lower()=='all':
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
    logpath = './log'
    rangelist = sys.argv[2]
    arglist = sys.argv[3:]
    logpath = createLogDir(name, logpath)
    st = suiteParser(name, logpath)
    lstRange = GetRange(rangelist )
    suite= st.load(suitefile, arglist, lstRange)

    benchfile =''
    benchinfo ={}
    logger =None
    report = []
#    3, break, run_case_in_suite, rc.py2 home_case.csv home.csv full
#	9, concurrent, loop, 2 ,no_stop ,rc.py5 home_case.csv home.csv full
#	9, concurren,FailAction,FuncName,cmd =case, run_case_in_suite, rc.py7 home_case.csv home.csv full
    index = 1
    for caseline in suite:
        LineNo,FailAction,[FuncName,cmd ]=caseline
        casename='%d'%index
        logdir ='./log/'+suitefile+'/'+casename
        casename, benchinfo,logger, FailAction,logdir, cmd
        FuncName(casename, benchfile, benchinfo,logger, FailAction,logdir, cmd)




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
