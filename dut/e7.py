__author__ = 'Sean Yu'
'''created @2015/9/30''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))
from winTelnet import winTelnet
import re
import math
import pprint,traceback
import time,datetime
import threading
import copy
from common import csvfile2array
class e7(winTelnet):
    def __init__(self,name,attr,logger, logpath, shareData):
        winTelnet.__init__(self, name,attr,logger, logpath, shareData)
        self.attribute['PROMPT']='>|#|>>>'
    def setTime(self, tm =None):
        if tm:
            self.send('set time %s'%str(tm))
        else:
            self.send(self.getValue('tm'))

    def vdsl_setIgnoreLines(self,IgnoreRange,nodeName=None, var_name='IgnoreDSLs'):
        if not nodeName:
            nodeName= self.name
        tmp = IgnoreRange.strip().split(',')
        lstIgnoreDsls=[]
        reDslPortRange = re.compile('\s*([\d/]+v)(\d+)\s*-\s*(\d+)\s*', re.IGNORECASE|re.DOTALL)
        def reFormPort(port):
            if port.find(':')!=-1:
                port ='%s:%s'%(self.name, port.strip())
            lport =re.split('v', port)
            if lport[-1].__len__()==1:
                lport[-1]='0'+lport[-1]
            return 'v'.join(lport)
        for i in tmp:
            m = re.search(reDslPortRange,i)
            if m:
                prefix= m.group(1)
                s = int(m.group(2))
                e= int(m.group(3))
                for i in range(s, e):
                    port = reFormPort('%s:%s%d'%(nodeName,prefix,i))
                    lstIgnoreDsls.append(port)
            else:
                lstIgnoreDsls.append(nodeName+':'+reFormPort(i.strip()))

        try:
            tmpIgnoreDsls = self.getValue(var_name)
            for iport in lstIgnoreDsls:
                if iport not in tmpIgnoreDsls:
                    tmpIgnoreDsls.append(iport)
            self.setValue(var_name, tmpIgnoreDsls)
        except:
            self.setValue(var_name, lstIgnoreDsls)

    def vdsl_getMaxReachTime(self, totalDslLines, name='MaxReachTime'):
        #import math
        Exponent =math.ceil(math.log(totalDslLines,2))
        maxReachTime = math.pow(2, Exponent)+180.0+1.
        self.setValue(name, maxReachTime)
        return maxReachTime
    def vdsl_setStartTimeOfReachTest(self, var_name='reachTimeStartTime', StopSignalName='reachTimeCheck'):
        import datetime
        self.setValue(var_name, datetime.datetime.now())
        self.setValue(StopSignalName, {})
    def vdsl_checkReachTime(self, totalDslUnderTest , cmd='show dsl-port',reachRate=100.0,resultFile=None, startTimeName='reachTimeStartTime' ,MaxReachTimeName='MaxReachTime', varName_DslInfo = 'reachTime' , ignoreListName='IgnoreDSLs', StopSignalName='reachTimeCheck'):
        #self.vdsl_setStartTimeOfReachTest(startTimeName, StopSignalName)
        ignoreList =self.getValue(ignoreListName)
        def inner_vdsl_CheckReachTime(totalDslUnderTest , cmd,reachRate,resultFile, startTimeName ,MaxReachTimeName, varName_DslInfo , ignoreList, StopSignalName):
            try:
                extratWaitTime= 60 #seconds
                #import datetime
                now = datetime.datetime.now()
                startTime    =  self.getValue(startTimeName)
                MaxReachTime =  datetime.timedelta(seconds=self.getValue(MaxReachTimeName))
                IgnoreDsls   =  ignoreList
                if not IgnoreDsls:
                    IgnoreDsls=[]
                #1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)
                stop=False
                tmpReachRate=0
                targReachRate = math.ceil(reachRate)
                preReachRate=tmpReachRate
                msgReachRate='ReachRate(%),TimeSpan(s)\n'
                preTimeStamp=now
                localDslInfo=None
                #major ALARM for DSL port "1/v17" at 2015/12/16 20:53:14.21:
                #Alarm CLEARED for DSL port "1/v12" at 2015/12/10 03:19:51.66

                patEventRaise=re.compile('(major ALARM) for DSL port "([0-9/v]+)" at ([0-9/:. ]+):', re.IGNORECASE)
                patEventClear=re.compile('(Alarm CLEARED) for DSL port "([0-9/v]+)" at ([0-9/:. ]+):', re.IGNORECASE)
                def parseDslEvent(line, patRaise, patClear):
                    isEventFound =False
                    isClear =False
                    isRaise =False
                    portName =''
                    mRaise =re.match(patRaise,line)
                    mClear =re.match(patClear,line)
                    if mClear:
                        isClear=True
                        isEventFound = True
                        portName= '%s:%s'%(self.name, mRaise.group(2))
                    elif mRaise:
                        isRaise=True
                        isEventFound = True
                        portName= '%s:%s'%(self.name, mRaise.group(2))
                    return isEventFound,isClear, isRaise,portName

                def updateDslSpanTimeAndScore(name_shareData, port, span_time, max_span_time):
                    dsl_info =self.getValue(name_shareData)
                    if dsl_info.has_key(port):
                        #port existed
                        self.setFail('port %s cleared again!')

                self.send('')#reset the search index to the end
                counter=0
                while not stop:
                    #Alarm CLEARED for DSL port "1/v12" at 2015/12/10 03:19:51.66
                    counter +=1
                    preTimeStamp=now
                    now = datetime.datetime.now()
                    duration = now-startTime
                    self.send('#try %d, duration(s):%f'%(counter,duration.total_seconds()))
                    self.singleStep('show time', '.+>', 180)
                    debug_cmd = [
                        'debug card 1',

                        '/xdsl/bcm getvectcounters 46',
                        '/xdsl/vec getpacketcounters',
                        #'/xdsl/vec getcounters 46 0',
                        '/xdsl/bcm getcounters 46 0',

                        '/xdsl/obj logshowtimedrop 46',
                        'exit'
                    ]
                    for tcmd in debug_cmd:
                        try:
                            self.singleStep(tcmd, '>',10)
                        except:
                            pass
                    output = self.singleStep(cmd, '---.+>', 180)#------
                    for tcmd in debug_cmd:
                        try:
                            self.singleStep(tcmd, '>',10)
                        except:
                            pass
                    lines = output.split('\r\n')
                    for line in lines:
                        line = self.__vdsl_getSingleLineInfo(line)
                        if line:
                            tmpShowTime =MaxReachTime.total_seconds()-duration.total_seconds()
                            if tmpShowTime>0:
                                tmpScore=1
                            else:
                                tmpScore=0
                            line.append(tmpScore)#line score, the first dsl lines get high score
                            line.append(tmpShowTime)#add time span of line which reach 'showtime' in seconds
                            tmpLine=copy.deepcopy(line)
                            try:
                                self.__vdsl_checkLineStatus(tmpLine, duration.total_seconds(),IgnoreDsls, varName_DslInfo)
                            except Exception as e:
                                self.setFail(traceback.format_exc())
                            del tmpLine
                            del tmpScore
                    tmpTotalShowTimeLines= self.getValue(varName_DslInfo)
                    if tmpTotalShowTimeLines:
                        self.logger.info('VDSL TR-249:%d DSL lines reached ShowTime '%tmpTotalShowTimeLines.__len__())
                        tmpReachRate=math.ceil( tmpTotalShowTimeLines.__len__()*100.0/totalDslUnderTest)


                    if tmpReachRate>= targReachRate:
                        msgReachRate+='%f,%f\n'%(tmpReachRate,duration.total_seconds())
                        stop=True
                        deviation = now-preTimeStamp
                        if duration.total_seconds()>=(MaxReachTime.total_seconds()+deviation.total_seconds()):
                            msg = '\nTimeSpan %fs exceeded %f for %f%s train rate, interval is %fs between last 2 checkpoints\n%s'%(duration.total_seconds(), MaxReachTime.total_seconds(), tmpReachRate, '%',deviation.total_seconds() ,msgReachRate)
                            self.setFail(msg)
                    elif int(preReachRate)!=int(tmpReachRate):
                        msgReachRate+='%f,%f\n'%(tmpReachRate,duration.total_seconds())
                        preReachRate=tmpReachRate
                    multiple_of_wait_time=5
                    if duration.total_seconds()>=(MaxReachTime.total_seconds()*multiple_of_wait_time):
                        msgReachRate+='%f,%f\n'%(tmpReachRate,duration.total_seconds())
                        stop=True
                        if duration.total_seconds()>=MaxReachTime.total_seconds():
                            deviation = now-preTimeStamp
                            msg = '\nTimeSpan %fs exceeded %f for %f%s train rate, interval is %fs between last 2 checkpoints\n%s'%(duration.total_seconds(), MaxReachTime.total_seconds(), tmpReachRate, '%',deviation.total_seconds(), msgReachRate )
                            self.setFail(msg)
                    elif duration.total_seconds()>MaxReachTime.total_seconds():
                        pass

                self.logger.info('VDSL TR-249: test duration:'+pprint.pformat(duration.total_seconds()))
                if not resultFile:
                    dirname = os.path.dirname(self.logfile.name)
                    resultFile= dirname+'/result.csv'

                self.write2file(msgReachRate+'\n',filename=resultFile)
                self.logger.info('VDSL TR-249:\n'+ pprint.pformat(tmpTotalShowTimeLines))
                import time
                print('start to sleep %d seconds, make sure no retrain for each lines'%extratWaitTime)
                time.sleep(extratWaitTime)

                output = self.singleStep(cmd, '.+>', 180)
                lines= output.split('\n')
                localDslInfo=self.getValue(varName_DslInfo)
                for line in lines:
                    lstLine = self.__vdsl_getSingleLineInfo(line)
                    if lstLine:
                        port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain=lstLine
                        port = '%s:%s'%(self.name, port)
                        if localDslInfo.has_key(port):
                            if status_status.find('Showtime')!=-1:
                                pass
                            else:
                                msg = '%s status changed from Showtime to %s'%( port, status_status)
                                self.setFail(msg)
                            if status_retrain!=localDslInfo[port][8]:
                                msg = '%s retrain time changed from %d to %d'%(port, localDslInfo[port][8],status_retrain)
                                self.setFail(msg)
                deviation = now-preTimeStamp
            except Exception as e:
                self.setFail(e.__str__()+'\n'+traceback.format_exc())


        th =threading.Thread(target=inner_vdsl_CheckReachTime, args=[totalDslUnderTest , cmd,reachRate,resultFile, startTimeName ,MaxReachTimeName, varName_DslInfo , ignoreList, StopSignalName])
        th.start()
        self.updateValue(StopSignalName,{self.name: th})
        time.sleep(1)


    def __vdsl_isPortInIgnoreList(self, port, ignoreList, node=None):
        if node:
            pass
        else:
            node =self.name
        tmpPort = '%s:%s'%(node,port)
        if tmpPort in ignoreList:
            return True
        else:
            return False

    def vdsl_wait_reachTimeCheck_stop(self, totalNodes=1, StopSignalName = 'reachTimeCheck'):
        n= self.getValue(StopSignalName)
        interval=5
        while n.__len__()<totalNodes:
            time.sleep(interval)
            n= self.getValue(StopSignalName)
        for k in n.keys():
            n[k].join()



    def vdsl_dumpDslInfo(self, filename, nameDslInfo='reachTime'):

        dslInfo =self.getValue(nameDslInfo)
        dslLines = sorted(dslInfo.keys())
        msg=''
        for dsl in dslLines:
            info = dslInfo[dsl]
            info.insert(0,dsl)
            msg+=','.join([pprint.pformat(x).replace("'",'') for x in info])+'\n'
        dirpath = os.path.dirname(filename)
        if dirpath=='':
            dirpath = os.path.dirname(self.logfile.name)
            filename = dirpath+'/'+filename
        self.write2file(msg,filename)
    def vdsl_compareReachTimeResult(self, vectoring_file=None, non_vectoring_file=None, scoreFile='score.csv'):
        basename = os.path.dirname(self.logfile.name)
        if vectoring_file:
            pass
        else:
            vectoring_file = basename+'/raw_vector.csv'
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
        lstNVScore=[]
        portOfV=[]
        vscore=[]
        lstVTimeSpan = []
        for i in range(0, vect.__len__()):
            portOfV.append(vect[i][0])
            vscore.append(float(vect[i][-1]))
        minVscore ='0'#str(min(vscore)-5.0)

        if vect.__len__()< nvect.__len__():
            self.setFail('train up ports are not equal between vectoring(%d) and non-vectoring(%d)'%(vect.__len__(),nvect.__len__()))
        for ni in range(0,nvect.__len__()):
            nport,nreachTime, nmode, nrate_us, nrate_ds, nsnr_us, nsnr_ds,nstatus_status, nstatus_time,nstatus_retrain, nline_score, nline_timeSpan=nvect[ni]
            lstPortName.append(nport)
            lstNVScore.append(nline_score)

            try:
                i = portOfV.index(nport)
                port,reachTime, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain , line_score, line_timeSpan =vect[i]
                lstVTimeSpan.append(line_timeSpan)
                lstVScore.append(line_score)

                if float(rate_us)>float(nrate_us):
                    msgRate_us+='%s,RATE US, VECTOR, %s, FEXT, %s, \tPASS\n'%(port,rate_us, nrate_us)
                else:
                    msgRate_us+='%s,RATE US, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_us, nrate_us)
                    self.setFail('%s,RATE US, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_us, nrate_us))
                if float(rate_ds)>float(nrate_ds):
                    msgRate_ds+='%s,RATE DS, VECTOR, %s, FEXT, %s, \tPASS\n'%(port,rate_ds, nrate_ds)
                else:
                    msgRate_ds+='%s,RATE DS, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_ds, nrate_ds)
                    self.setFail('%s,RATE DS, VECTOR, %s, FEXT, %s, \tFAIL\n'%(port,rate_ds, nrate_ds))

                if status_retrain!='0':
                    self.setFail('%s mode is %s FAIL\n'%(port,nstatus_retrain))
                    msgStatus_retrain+='%s retrain is %s FAIL\n'%(port,status_retrain)

                else:
                    msgStatus_retrain+='%s retrain is %s PASS\n'%(port,status_retrain)

                if mode.find('(*v)')!=-1:
                    msgMode+='%s mode is %s PASS\n'%(port,mode)
                else:
                    msgMode+='%s mode is %s FAIL\n'%(port,mode)
                    self.setFail('%s mode is not in vectoring group %s\n'%(port,mode))
            except Exception as e:
                print(e)
                self.setFail("can't find port %s in Vectoring test result"%(nport))
                lstVTimeSpan.append('-9999')
                lstVScore.append(minVscore)
                msgMode+='%s mode is Known FAIL\n'%(nport)
                msgStatus_retrain+='%s retrain is known FAIL\n'%(nport)
                msgRate_ds+='%s,RATE DS, VECTOR, Known, FEXT, %s, \tFAIL\n'%(nport, nrate_ds)
                msgRate_us+='%s,RATE US, VECTOR, Known, FEXT, %s, \tFAIL\n'%(nport, nrate_us)
        fileResult= basename+'/result.csv'
        self.logger.info(msgMode)
        self.logger.info(msgSnr_us)
        self.logger.info(msgSnr_ds)
        self.logger.info(msgRate_us)
        self.logger.info(msgRate_ds)
        data = 'PORT,%s\nVECTOR,%s\n'%(','.join(lstPortName+lstPortName),','.join(lstVScore+lstVTimeSpan))
        self.write2file(data, scoreFile)
        self.write2file(data+"\n", fileResult)
        self.write2file(msgMode+"\n", fileResult)
        self.write2file(msgSnr_us+"\n", fileResult)
        self.write2file(msgSnr_ds+"\n", fileResult)
        self.write2file(msgRate_us+"\n", fileResult)
        self.write2file(msgRate_ds+"\n", fileResult)


    def __vdsl_insertNewShowTimeDslLine(self,port, info, tableName = 'reachTime'):
        dictReachTime={port:info}
        try:
            dslInfo=self.getValue(tableName)
            if dslInfo.has_key(port):
                pass
            else:
                dictReachTime =self.updateValue(tableName, dictReachTime)
        except:
            self.setValue(tableName,dictReachTime)
        return  dictReachTime.__len__()

    def __vdsl_checkLineStatus(self, line,timeStamp, ignoreList,  reachTime_var_name='reachTime'):
        [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain, line_score , line_span_time] =line
        totalShowTimeLines=0
        port='%s:%s'%(self.name, port)
        if status_status.find('Showtime')!=-1:
            line[0]=timeStamp
            if not ignoreList:
                ignoreList=[]
            if port in ignoreList:
                totalShowTimeLines=self.getValue(reachTime_var_name).__len__()
            else:
                totalShowTimeLines=self.__vdsl_insertNewShowTimeDslLine(port, line, reachTime_var_name)
        return  totalShowTimeLines

    def __vdsl_getSingleLineInfo(self, line):
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

        port='v'.join(lport)
        mode=' '.join(item[1:3])#str[9:21].strip()
        rate= item[3].strip() # str[22:37].strip()
        reRate=re.compile('([\d.]+)(M|K)/([\d.]+)(M|K)')
        rate_us=0
        rate_ds=0
        mRate = re.match(reRate,rate)
        if mRate:
            base=1.
            if mRate.group(2)=='K':
                base=1024.
            rate_us=float(mRate.group(1))/base
            base=1.
            if mRate.group(4)=='K':
                base=1024.
            rate_ds=float(mRate.group(3))/base
        snr=item[4]#str[38:49].strip()
        snr_ds,snr_us =snr.split('/')
        snr_us=float(snr_us.strip())
        snr_ds=float(snr_ds.strip())
        status=' '.join(item[5:])#str[50:].strip()
        reStatus=re.compile('([\w.]+)\s*\(([\d\w]+)/(\d+)\)')
        mStatus = re.match(reStatus,status)
        status_status,status_time,status_retrain='','',0
        if mStatus:
            status_status   =   mStatus.group(1)
            status_time     =   mStatus.group(2)
            status_retrain  =   int(mStatus.group(3))

        lineResult= [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain]
        return lineResult







