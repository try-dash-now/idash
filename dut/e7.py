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
import pprint
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
            lport =re.split('v', port)
            if lport[-1].__len__()==1:
                lport[-1]='0'+lport[-1]
            return 'v'.join(lport)
        for item in tmp:
            m = re.search(reDslPortRange,item)

            if m:
                prefix= m.group(1)
                s = int(m.group(2))
                e= int(m.group(3))
                for i in range(s, e):
                    port = reFormPort('%s:%s%d'%(nodeName,prefix,i))
                    lstIgnoreDsls.append(port)
            else:
                lstIgnoreDsls.append(nodeName+':'+reFormPort(item.strip()))

        try:
            tmpIgnoreDsls = self.getValue(var_name)
            tmpIgnoreDsls+= lstIgnoreDsls
            self.setValue(var_name, tmpIgnoreDsls)
        except:
            self.setValue(var_name, lstIgnoreDsls)

    def vdsl_getMaxReachTime(self, totalDslLines, name='MaxReachTime'):
        #import math
        Exponent =math.ceil(math.log(totalDslLines,2))
        maxReachTime = math.pow(2, Exponent)+180.0
        self.setValue(name, maxReachTime)
        return maxReachTime
    def vdsl_setStartTimeOfReachTest(self, var_name='reachTimeStartTime'):
        import datetime
        self.setValue(var_name, datetime.datetime.now())
    def vdsl_CheckReachTime(self, totalDslUnderTest , cmd='show dsl-port',reachRate=100.0, startTimeName='reachTimeStartTime' ,MaxReachTimeName='MaxReachTime', varName_DslInfo = 'reachTime' , ignoreList='IgnoreDSLs'):
        extratWaitTime= 1 #seconds
        import datetime
        now = datetime.datetime.now()
        startTime    =  self.getValue(startTimeName)
        MaxReachTime =  datetime.timedelta(seconds=self.getValue(MaxReachTimeName))
        IgnoreDsls   =  self.getValue(ignoreList)

        #1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)
        stop=False
        tmpReachRate=0
        targReachRate = math.ceil(reachRate)
        while not stop:
            output = self.singleStep(cmd, '.+>', 60)
            now = datetime.datetime.now()
            lines = output.split('\n')
            for line in lines:
                line = self.vdsl_getSingleLineInfo(line)
                if line:
                    self.vdsl_checkLineStatus(line, now, varName_DslInfo)
            tmpTotalShowTimeLines= self.getValue('reachTime')
            if tmpTotalShowTimeLines:
                self.logger.info('VDSL TR-249:%d DSL lines reached ShowTime '%tmpTotalShowTimeLines.__len__())
                tmpReachRate=math.ceil( tmpTotalShowTimeLines.__len__()*100/totalDslUnderTest)

            duration = now-startTime
            if duration<MaxReachTime:
                pass
            else:
                stop =True
            if tmpReachRate>= targReachRate:
                stop=True
                self.logger.info('VDSL TR-249: achieved %f%s reach Rate after %f seconds:'%(tmpReachRate,'%',duration.total_seconds()))

            self.logger.info('VDSL TR-249: test duration:'+pprint.pformat(duration.total_seconds()))


        self.logger.info('VDSL TR-249:\n'+ pprint.pformat(tmpTotalShowTimeLines))
        import time
        print('start to sleep %d seconds, make sure no retrain for each lines'%extratWaitTime)
        time.sleep(extratWaitTime)





    def __vdsl_insertNewShowTimeDslLine(self,port, info, tableName = 'reachTime'):
        try:
            dictReachTime =self.getValue(tableName)
            dictReachTime[port]=info
            self.setValue(tableName, dictReachTime)
        except:
            dictReachTime={port:info}
            self.setValue(tableName,dictReachTime)
        return  dictReachTime.__len__()

    def vdsl_checkLineStatus(self, line,timeStamp,  reachTime_var_name='reachTime'):
        [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain] =line
        totalShowTimeLines=0
        if status_status.find('Showtime')!=-1:
            line[0]=timeStamp
            totalShowTimeLines=self.__vdsl_insertNewShowTimeDslLine('%s:%s'%(self.name, port), line, reachTime_var_name)
        return  totalShowTimeLines


    def vdsl_getSingleLineInfo(self, line,  var_name='reachTimeInfo'):
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
        str =line# '1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)'

        port=str[0:8].strip()
        lport =re.split('v', port)
        if lport[-1].__len__()==1:
            lport[-1]='0'+lport[-1]
        port='v'.join(lport)
        mode=str[9:21].strip()
        rate=str[22:37].strip()
        reRate=re.compile('([\d.]+)M/([\d.]+)M')
        rate_us=0
        rate_ds=0
        mRate = re.match(reRate,rate)
        if mRate:
            rate_us=float(mRate.group(1))
            rate_ds=float(mRate.group(2))
        snr=str[38:49].strip()
        reSNR=re.compile('([\d.]+)/([\d.]+)')
        mSNR = re.match(reSNR,snr)
        snr_ds,snr_us=0,0
        if mSNR:
            snr_us=float(mSNR.group(1))
            snr_ds=float(mSNR.group(2))
        status=str[50:].strip()
        reStatus=re.compile('([\w.]+)\s*\(([\d\w]+)/(\d+)\)')
        mStatus = re.match(reStatus,status)
        status_status,status_time,status_retrain='','',0
        if mStatus:
            status_status   =   mStatus.group(1)
            status_time     =   mStatus.group(2)
            status_retrain  =   int(mStatus.group(3))

        lineResult= [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain]
        return lineResult







