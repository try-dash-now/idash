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
        #cr.py casefile benchfile segment [arg1 arg2 ...argN] logpath
        cable_length =sys.argv[1]
        #cr.py casefile benchfile segment [arg1 arg2 ...argN] logpath
        if len(sys.argv)>2:
            defaultlogdir= sys.argv[-1]
        else:
            defaultlogdir ='./log'

        from runner import case_runner, initDUT, createLogDir      ,createLogger

        if not os.path.exists(defaultlogdir):
            os.mkdir(defaultlogdir)
        #defaultlogdir+='/ut_runner'
        casename = 'tr249_reachTime'
        casefolder = defaultlogdir#createLogDir(casename,defaultlogdir)
        logger = createLogger(casename, casefolder)


        from common import bench2dict
        benchfile = './bench.csv'
        bench =bench2dict(benchfile)

        ldut = list(['sbb93','sbb93debug1','cfa81','cfa82'])
        e7_name, e7debug_name, cfa1_name,cfa2_name = ldut
        ldut = list(['sbb93','sbb93debug1'])
        e7_name, e7debug_name = ldut
        debug_cmd = '''
/xdsl/bcm getvectcounters 46
/xdsl/vec getpacketcounters
/xdsl/bcm getcounters 46 0
/xdsl/obj logshowtimedrop 46
        '''
        cmd_turn_on_debug_trace = '''
        /log/stl -t XRPT +s all
/log/stl -t XPRX +s all
/log/stl -t XPOL +s all
/log/stl -t X0TH +s all
/log/stl -t X1PC +s all
/log/stl -t X2BO +s all
/log/stl -t XBCC  +s all

/log/stl -t X2GH +s all
/log/stl -t X3GH +s all
/log/stl -t X4GH +s all
/log/stl -t X5GH +s all
/log/stl -t X6GH +s all
/log/stl -t X7GH +s all
/log/stl -t X8GH +s all
/log/stl -t X9GH +s all
/log/stl -t XAGH +s all

/log/stl -t X2CH +s all
/log/stl -t X3CH +s all
/log/stl -t X4CH +s all
/log/stl -t X5CH +s all
/log/stl -t X6CH +s all
/log/stl -t X7CH +s all
/log/stl -t X8CH +s all
/log/stl -t X9CH +s all
/log/stl -t XACH +s all

/log/stl -t X2NH +s all
/log/stl -t X3NH +s all
/log/stl -t X4NH +s all
/log/stl -t X5NH +s all
/log/stl -t X6NH +s all
/log/stl -t X7NH +s all
/log/stl -t X8NH +s all
/log/stl -t X9NH +s all
/log/stl -t XANH +s all

/log/stl -t X2EH +s all
/log/stl -t X3EH +s all
/log/stl -t X4EH +s all
/log/stl -t X5EH +s all
/log/stl -t X6EH +s all
/log/stl -t X7EH +s all
/log/stl -t X8EH +s all
/log/stl -t X9EH +s all
/log/stl -t XAEH +s all


/xdsl/bcm getvectcounters 46
/xdsl/vec getpacketcounters
/xdsl/bcm getcounters 46 0
/xdsl/obj logshowtimedrop 46
        '''

        ignore_ports =[]#[17,38]
        errormessage =[]
        lock_share_data = threading.Lock()
        gn_reach_rate='reach_rate'


        gn_reach_time = 'reach_time'
        gn_dsl_info = 'dsl_info'
        gn_dsl_info_b = 'dsl_info_before_test'
        g_SHAREDATA ={
            gn_reach_time:{},
            gn_dsl_info:{},
            gn_dsl_info_b:{},
            }
        #duts= initDUT(errormessage,bench,ldut,logger, casefolder)#['lnx1', 'lnx2']

        duts= initDUT(errormessage,bench, ldut,logger, casefolder)

        e7      = duts[e7_name]
        e7debug = duts[e7debug_name]
        #cfa1    = duts[cfa1_name]
        #cfa2    = duts[cfa2_name]

        g_REACH_TIME={}
        def getValue(name=None):
            global lock_share_data
            lock_share_data.acquire()
            global g_SHAREDATA
            if name in g_SHAREDATA:
                tmp = g_SHAREDATA[name]
            else:
                tmp = None
            lock_share_data.release()
            return tmp

        def setValue(name, value):
            global lock_share_data
            lock_share_data.acquire()
            global g_SHAREDATA
            g_SHAREDATA[name]=value
            lock_share_data.release()


        def enter(dut, cmds,exp='.*' ,waittime=10) :
            cmdlines = cmds.split('\n')
            for cmd in cmdlines:
                lstcmd = cmd.split(',')
                len_cmd= lstcmd.__len__()
                waittime = 10
                tcmd=lstcmd[0]
                if len_cmd==1:
                    pass
                elif len_cmd==2:
                    exp = lstcmd[1]
                elif len_cmd>2:
                    exp = lstcmd[1]
                    waittime=lstcmd[2]
                dut.singleStep(tcmd, exp, waittime)
        def disable_enable_port(dut, card,ignore_ports, waittime=10, checkSuccess=True):
            for port in range(1,49,1):
                cmd = 'disable dsl-port %s/v%d'%(str(card), port)
                dut.singleStep(cmd, 'success', waittime)
            time.sleep(30)
            for port in range(1,49,1):
                if port in ignore_ports:
                    pass
                else:
                    cmd = 'enable dsl-port %s/v%d'%(str(card), port)
                    if checkSuccess:
                        dut.singleStep(cmd, 'success', waittime)
                    else:
                        dut.write(cmd+'\r\n')
                        dut.show()
            dut.singleStep('\r\n','.*',1)
        def get_time(dut):
            '''
            Tue Dec 22 00:10:39 2015
            '''
            pat = '(\w+)\s+(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\d{4})'
            local_time = datetime.datetime.now()
            output =dut.singleStep('show time',pat ,180)
            month =['', 'Jan','Feb','Mar', 'Apr', 'May', 'Jun', 'Jul','Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            mo = re.search(pat, output)
            y = int(mo.group(7))
            m = month.index(mo.group(2))
            d = int(mo.group(3))
            H = int(mo.group(4))
            M = int(mo.group(5))
            S = int(mo.group(6))
            dut_time = datetime.datetime(y,m, d, H, M, S,0)
            delta_btn_local_dut = local_time-dut_time
            delta_btn_local_dut_in_second= delta_btn_local_dut.total_seconds()
            return dut_time, local_time, delta_btn_local_dut_in_second
        def get_max_reach_time(total_port):
            Exponent =math.ceil(math.log(total_port,2))
            maxReachTime = math.pow(2, Exponent)+180.0
            return maxReachTime
        #major ALARM for DSL port "1/v17" at 2015/12/16 20:53:14.21:
        #Alarm CLEARED for DSL port "1/v12" at 2015/12/10 03:19:51.66


        def parseDslEvent(dut_name, line, patRaise, patClear):
            isEventFound =False
            isClear =False
            isRaise =False
            portName =''
            mRaise =re.search(patRaise,line)
            mClear =re.search(patClear,line)
            event_time = None
            if mClear:
                isClear=True
                isEventFound = True
                portName= '%s:%s'%(dut_name, '%sv%02d'%(mClear.group(2),int(mClear.group(3))))
                gdict = mClear.groupdict()
                for k in gdict:
                    gdict[k]= int(gdict[k])
                event_time = datetime.datetime(gdict['year'],gdict['month'],gdict['day'],gdict['hour'],gdict['minute'],gdict['second'],gdict['microsecond'])
            elif mRaise:
                isRaise=True
                isEventFound = True
                portName= '%s:%s'%(dut_name, '%sv%02d'%(mRaise.group(2),int(mRaise.group(3))))
                gdict = mRaise.groupdict()
                for k in gdict:
                    gdict[k]= int(gdict[k])
                event_time = datetime.datetime(gdict['year'],gdict['month'],gdict['day'],gdict['hour'],gdict['minute'],gdict['second'],gdict['microsecond'])
            return isEventFound,isClear, isRaise,portName, event_time
        def get_reach_time(dut, dutdebug, total_port, start_time, delta_time ,reach_rate_goal=100, ignore_ports=[], max_wait_round=3):
            max_reach_time= get_max_reach_time(total_port)
            max_wait_time = max_wait_round*max_reach_time
            now = datetime.datetime.now()
            duration= now-start_time
            duration = duration.total_seconds()
            checking =True
            tmp_reach_rate= 0.
            index_of_first_all_leave= 0
            patEventRaise = re.compile('(major ALARM) for DSL port "([0-9/]+)v(\d+)" at (?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)\s+(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+).(?P<microsecond>\d+):', re.IGNORECASE)
            patEventClear = re.compile('(Alarm CLEARED) for DSL port "([0-9/]+)v(\d+)" at (?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)\s+(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+).(?P<microsecond>\d+):', re.IGNORECASE)
            global gn_dsl_info,gn_dsl_info_b,gn_reach_time, gn_reach_rate,debug_cmd
            index_of_last_search = 0
            pre_reach_rate= 0.
            #dut.send('\r\n')
            dut.singleStep('\r\n','>',180)
            pre_time_stamp=now
            if dutdebug:
                pre_time_stamp= now
                enter(dutdebug, debug_cmd)
            raise_again_ports=[]
            while checking:
                now = datetime.datetime.now()
                if dutdebug:
                    if (now -pre_time_stamp).total_seconds()>10:
                        pre_time_stamp= now
                        enter(dutdebug, debug_cmd)
                output = dut.get_search_buffer()
                #print(output)
                tmp_total_show_time_port = 0
                if len(output)>0:
                    g_reach_time = getValue(gn_reach_time)
                    lines = output.split('\r\n')
                    for line in lines:
                        found, is_clear, is_raise, portName ,event_time =  parseDslEvent(dut.name, line , patEventRaise, patEventClear)
                        if found:
                            if is_raise:
                                if portName not in raise_again_ports:
                                    raise_again_ports.append(portName)
                                    dut.setFail('%s: %s LOS raised, after DSL port enabled\n'%(dut.name,portName))
                            elif is_clear:
                                if portName in g_reach_time:#
                                    new_duration = (event_time-start_time).total_seconds()+ delta_time
                                    if g_reach_time[portName]!=new_duration:
                                        dut.setFail('%s %s: clear LOS again, last arrive duration %f, new %f\n'%(dut.name, portName,g_reach_time[portName], new_duration ))
                                else:
                                    if portName not in ignore_ports:
                                        g_reach_time[portName]=(event_time-start_time).total_seconds()+ delta_time
                                        setValue(gn_reach_time,g_reach_time)
                    tmp_total_show_time_port = len(g_reach_time)
                #dut.send('\r\n')

                tm_last_check=now
                duration= now-start_time
                duration = duration.total_seconds()
                if duration > max_wait_time:
                    checking =False
                tmp_reach_rate = tmp_total_show_time_port*100.0/total_port

                if pre_reach_rate!=tmp_reach_rate:
                    pre_reach_rate= tmp_reach_rate

                    tmp = getValue(gn_reach_rate)
                    tmp +='%.1f,%.1f\n'%(tmp_reach_rate,duration)
                    setValue(gn_reach_rate, tmp)
                if tmp_reach_rate>=reach_rate_goal:
                    checking =False
                if tmp_total_show_time_port==total_port:
                    checking =False

            g_reach_time = getValue(gn_reach_time)
            tmp_total_show_time_port=len(g_reach_time)
            deviation =2.0
            if tmp_total_show_time_port==total_port and duration< (max_reach_time+1.0):
                pass
            else:
                dut.setFail('total %d/%d reach time %.1fs exceeded target(%.1f) for %.1f'%(tmp_total_show_time_port,total_port,duration, float(max_reach_time),reach_rate_goal))



        def get_train_rate_data(dut, cmd='show dsl-port', ignore_ports=[]):
            output = dut.singleStep(cmd, '---.+>', 180)
            dut_name=dut.name
            result={}
            lines = output.split('\r\n')
            for line in output.split('\n'):
                tmp =parse_dsl_info(dut_name, line)
                if tmp:
                    port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain= tmp
                    result[port]= tmp[1:]
            return result
        def save_dsl_info(dut,filename, data):

            dslInfo =data
            dslLines = sorted(dslInfo.keys())
            msg=''
            for dsl in dslLines:
                info = dslInfo[dsl]
                info.insert(0,dsl)
                msg+=','.join([x for x in info])+'\n'
            dirpath = os.path.dirname(filename)
            if dirpath=='':
                dirpath = os.path.dirname(dut.logfile.name)
                filename = dirpath+'/'+filename
            dut.write2file(msg,filename)


        def parse_dsl_info(dut_name, line):
            '''
            CalixE7>show dsl-port
            Port     Mode         Rate (Us/Ds)    SNR (Us/Ds) Status (Cur. Time/Retrains)
            -------- ------------ --------------- ----------- --------------------------------
            1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)
            '''

            pValidLine= re.compile('^\d+[/\d]v\d+')
            if re.match(pValidLine, line):
                pass
            else:
                return  None
            str = re.sub('\s+', ' ', line)
            item = str.split(' ')
            if item[2].find('*')!=-1:
                pass
            else:
                item.insert(2,' ')
            #str =line# '1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)'


            port=item[0]#str[0:8].strip()
            lport =re.split('v', port)
            if lport[-1].__len__()==1:
                lport[-1]='0'+lport[-1]

            port='%s:%s'%(dut_name, 'v'.join(lport))
            mode=' '.join(item[1:3])#str[9:21].strip()
            rate= item[3].strip() # str[22:37].strip()
            reRate=re.compile('([\d.]+)(M|K)/([\d.]+)(M|K)')
            rate_us='0'
            rate_ds='0'
            mRate = re.match(reRate,rate)
            if mRate:
                base=1.
                if mRate.group(2)=='K':
                    base=1024.
                rate_us='%f'%(float(mRate.group(1))/base)
                base=1.
                if mRate.group(4)=='K':
                    base=1024.
                rate_ds='%f'%(float(mRate.group(3))/base)
            snr=item[4]#str[38:49].strip()
            snr_ds,snr_us =snr.split('/')
            snr_us=snr_us.strip()
            snr_ds=snr_ds.strip()
            status=' '.join(item[5:])#str[50:].strip()
            reStatus=re.compile('([\w.]+)\s*\(([\d\w]+)/(\d+)\)')
            mStatus = re.match(reStatus,status)
            status_status,status_time,status_retrain='','','0'
            if mStatus:
                status_status   =   mStatus.group(1)
                status_time     =   mStatus.group(2)
                status_retrain  =   mStatus.group(3)

            lineResult= [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain]
            return lineResult

        def compare_train_data(dut, scoreFile='score.csv', non_vectoring_file=None, vectoring_file=None):
            basename = os.path.dirname(dut.logfile.name)
            if vectoring_file:
                pass
            else:
                vectoring_file = basename+'/dsl_info_after_test.csv'
            if non_vectoring_file:
                pass
            else:
                non_vectoring_file = basename+'/raw_fext.csv'
            #non_vectoring_file = os.path.basename(non_vectoring_file)
            vect    = csvfile2array(vectoring_file)
            nvect   = csvfile2array(non_vectoring_file)
            msgMode=''
            msgRate_us=''
            msgRate_ds=''
            msgSnr_us=''
            msgSnr_ds=''
            msgStatus_retrain=''
            lstPortName=[]
            lstVScore=[]
            #lstNVScore=[]
            portOfV=[]
            vscore=[]
            lstVTimeSpan = []
            for i in range(0, vect.__len__()):
                portOfV.append(vect[i][0])
                vscore.append(float(vect[i][-1]))
            minVscore ='0'#str(min(vscore)-5.0)

            if vect.__len__()< nvect.__len__():
                dut.setFail('train up ports are not equal between vectoring(%d) and non-vectoring(%d)'%(vect.__len__(),nvect.__len__()))
            for ni in range(0,nvect.__len__()):
                nport,nmode, nrate_us, nrate_ds, nsnr_us, nsnr_ds,nstatus_status, nstatus_time,nstatus_retrain =nvect[ni][0:9]
                lstPortName.append(nport)
                #lstNVScore.append(nline_score)

                try:
                    i = portOfV.index(nport)
                    port,mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain, line_score, line_timeSpan , reachTime=vect[i][0:12]
                    lstVTimeSpan.append(line_timeSpan)
                    lstVScore.append(line_score)

                    if float(rate_us)>float(nrate_us):
                        msgRate_us+='%s,RATE US, VECTOR, %s, FEXT, %s, \tPASS\n'%(port,rate_us, nrate_us)
                    else:
                        msgRate_us+='%s,RATE US, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_us, nrate_us)
                        dut.setFail('%s,RATE US, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_us, nrate_us))
                    if float(rate_ds)>float(nrate_ds):
                        msgRate_ds+='%s,RATE DS, VECTOR, %s, FEXT, %s, \tPASS\n'%(port,rate_ds, nrate_ds)
                    else:
                        msgRate_ds+='%s,RATE DS, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_ds, nrate_ds)
                        dut.setFail('%s,RATE DS, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_ds, nrate_ds))

                    if status_retrain!='0':
                        dut.setFail('%s retrain is %s FAIL\n'%(port,status_retrain))
                        msgStatus_retrain+='%s retrain is %s FAIL\n'%(port,status_retrain)

                    else:
                        msgStatus_retrain+='%s retrain is %s PASS\n'%(port,status_retrain)

                    if mode.find('(*v)')!=-1:
                        msgMode+='%s mode is %s PASS\n'%(port,mode)
                    else:
                        msgMode+='%s mode is %s FAIL\n'%(port,mode)
                        dut.setFail('%s mode is not in vectoring group %s\n'%(port,mode))
                except Exception as e:
                    print(e)
                    dut.setFail("can't find port %s in Vectoring test result"%(nport))
                    lstVTimeSpan.append('-9999')
                    lstVScore.append(minVscore)
                    msgMode+='%s mode is Known FAIL\n'%(nport)
                    msgStatus_retrain+='%s retrain is known FAIL\n'%(nport)
                    msgRate_ds+='%s,RATE DS, VECTOR, Known, FEXT, %s, \tFAIL\n'%(nport, nrate_ds)
                    msgRate_us+='%s,RATE US, VECTOR, Known, FEXT, %s, \tFAIL\n'%(nport, nrate_us)
            fileResult= basename+'/result.csv'
            dut.logger.info(msgMode)
            dut.logger.info(msgSnr_us)
            dut.logger.info(msgSnr_ds)
            dut.logger.info(msgRate_us)
            dut.logger.info(msgRate_ds)
            msg_reach_rate = getValue(gn_reach_rate)
            dut.write2file(msg_reach_rate, fileResult)
            dut.logger.info(msg_reach_rate)
            data = 'PORT,%s\nVECTOR,%s\n'%(','.join(lstPortName+lstPortName),','.join(lstVScore+lstVTimeSpan))
            dut.write2file(data, scoreFile)
            dut.write2file(data+"\n", fileResult)
            dut.write2file(msgMode+"\n", fileResult)
            dut.write2file(msgSnr_us+"\n", fileResult)
            dut.write2file(msgSnr_ds+"\n", fileResult)
            dut.write2file(msgRate_us+"\n", fileResult)
            dut.write2file(msgRate_ds+"\n", fileResult)


        cmd_stop_all= '''
set sess page dis alarm ena event ena
debug
/xdsl/api stopline all
/xdsl/bcm cfg extra all ginp.reincfg 164 164
'''
        cmd_start_all='''
/xdsl/api startline all
exit
'''
        #line = '1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)'
        #parse_dsl_info('sbb62', line)
        #cable_length= 1000
        #file_name_bench_mark= './%s_raw_fext_%d_benchMark.csv'%(e7.name, cable_length )
        #file_name_score = './%s_score_%d.csv'%(e7.name,cable_length)
        #compare_train_data(e7,file_name_score, file_name_bench_mark, './dsl_info_after_test.csv')

        defaultTime = 120
        total_port = 48
        max_reach_time=244
        setValue(gn_reach_rate, 'ReachRate(%),duration(s)\n')
        enter(e7debug, cmd_turn_on_debug_trace)
        if False:

            disable_enable_port(e7, card='1', ignore_ports=ignore_ports)
            max_reach_time = get_max_reach_time(total_port)
            time.sleep(max_reach_time)#
        #tm_start_dut_2, tm_start_local_2, tm_delta_e7_2 =get_time(e7_2)
        #tm_start_dut_3, tm_start_local_3, tm_delta_e7_3 =get_time(e7_3)
        dsl_info_before_test = get_train_rate_data(e7 )
        file_name_dsl_info_before_test = 'dsl_info_before_test.csv'
        save_dsl_info(e7,file_name_dsl_info_before_test,dsl_info_before_test)
        new_way = False
        if new_way:
            enter(e7,cmd_stop_all)
            wait_before_start_all= 30
            time.sleep(wait_before_start_all)
            enter(e7,cmd_start_all)
            tm_start_dut, tm_start_local, tm_delta_e7 =get_time(e7)
            time.sleep(5)
            e7.singleStep('\r\n','major ALARM for DSL port.+>|>',60)
            e7.send('\r\n')
        else:
            tm_start_dut, tm_start_local, tm_delta_e7 =get_time(e7)
            disable_enable_port(e7,1,[],waittime=10,checkSuccess=False)
            cmd_stop_all= '''
set sess page dis alarm ena event ena
debug
/xdsl/retrain 1 48
/xdsl/bcm cfg extra all ginp.reincfg 164 164
exit
'''
            enter(e7,cmd_stop_all)
            #wait_before_start_all= 30
            #time.sleep(wait_before_start_all)
            #enter(e7,cmd_start_all)
            tm_start_dut, tm_start_local, tm_delta_e7 =get_time(e7)
            time.sleep(5)
            e7.singleStep('\r\n','major ALARM for DSL port.+>|>',60)
            e7.send('\r\n')

        thread_e7_1 = threading.Thread(target=get_reach_time, args=[e7, None, 48, tm_start_local, tm_delta_e7 ,100, [],3] )
#th =threading.Thread(target=inner_vdsl_CheckReachTime, args=[totalDslUnderTest , cmd,reachRate,resultFile, startTimeName ,MaxReachTimeName, varName_DslInfo , ignoreList, StopSignalName])
 #      start()

        check_thread =[]
        check_thread.append(thread_e7_1)
        for th in check_thread:
            th.start()
        for th in check_thread:
            th.join()
        msg_reach_rate = getValue(gn_reach_rate)
        print (msg_reach_rate)
        print ( pprint.pformat(getValue(gn_reach_time)))
        time.sleep(60)
        dsl_info = get_train_rate_data(e7)

        reachtime = getValue(gn_reach_time)
        for portName in dsl_info:
            dsl_info[portName][-1]=str(max(int(dsl_info[portName][-1]) - int(dsl_info_before_test[portName][-1])-1,0))
            if portName in reachtime:
                rt = reachtime[portName]
                score = max_reach_time-rt
                bscore = 1 if score>0 else 0
                dsl_info[portName].append(str(bscore))
                dsl_info[portName].append(str(rt))
                dsl_info[portName].append(str(score))

        save_dsl_info(e7,'dsl_info_after_test.csv',dsl_info)
        file_name_dsl_info_after_test = 'dsl_info_after_test.csv'
        #cable_length= '1000'
        file_name_bench_mark= './%s_raw_fext_%s_benchMark.csv'%(e7.name, cable_length )
        file_name_score = './%s_score_%s.csv'%(e7.name,cable_length)
        #save_dsl_info(e7,file_name_dsl_info_after_test,dsl_info)
        compare_train_data(e7,file_name_score, file_name_bench_mark)


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
            ef.write('\n'+traceback.format_exc()+'\n')

        os._exit(1)  #exit(1)