__author__ = 'Sean Yu'
'''created @2015/9/30''' 
import unittest
import os
import sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
sys.path.append(os.path.sep.join([pardir,'lib']))
from winTelnet import winTelnet
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
        for item in tmp:
            import re
            reDslPortRange = re.compile('\s*([\d/]+v)(\d+)\*-\s*(\d+)\s*', re.IGNORECASE|re.DOTALL)
            m = re.search(reDslPortRange,item)

            if m:
                prefix= m.group(1)
                s = int(m.group(2))
                e= int(m.group(3))
                for i in range(s, e):
                    lstIgnoreDsls.append('%s%d'%i)
            else:
                lstIgnoreDsls.append(item.strip())

        try:
            dictIgnoreDsls = self.getValue(var_name)
            dictIgnoreDsls[nodeName]= lstIgnoreDsls
            self.setValue()
        except:
            self.setValue(var_name, {nodeName: lstIgnoreDsls})

    def vdsl_getMaxReachTime(self, totalDslLines, name='MaxReachTime'):
        import math
        Exponent =math.ceil(math.log(totalDslLines,2))
        maxReachTime = math.pow(2, Exponent)+180.0
        self.setValue(name, maxReachTime)
        return maxReachTime
    def vdsl_startReachTimeTest(self, var_name='reachTimeStartTime'):
        import datetime
        self.setValue(var_name, datetime.datetime.now())
    def vdsl_CheckReachTime(self, cmd='show dsl-port', startTimeName='reachTimeStartTime' ,MaxReachTimeName='MaxReachTime', varName_DslInfo = 'reachTime' ):
        extratWaitTime= 60 #seconds
        import datetime
        now = datetime.datetime.now()
        startTime = self.getValue(startTimeName)
        MaxReachTime = sefl.getValue(MaxReachTimeName)
        #1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)

        if (now-startTime) <(MaxReachTime+extratWaitTime):
            output = self.singleStep(cmd, '.+>', 60)
            lines = output.split('\n')
            for line in lines:
                self.vdsl_checkSingleLine(line, now, varName_DslInfo)

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
        str =line# '1/v1     vdsl2/a (*v) 32.654M/96.876M 7.0/7.4     Showtime (2d22h13m20s/1)'
        port=str[0:8].strip()
        mode=str[9:21].strip()
        rate=str[22:37].strip()
        import re
        reRate=re.compile('([\d.]+)M/([\d.]+)M')
        rate_us=0
        rate_ds=0
        mRate = re.match(reRate,rate)
        if mRate:
            rate_us=int(mRate.group(1))
            rate_ds=int(mRate.group(2))
        snr=str[38:49].strip()
        reSNR=re.compile('([\d.]+)/([\d.]+)')
        mSNR = re.match(reSNR,snr)
        snr_ds,snr_us=0,0
        if mRate:
            snr_us=float(mSNR.group(1))
            snr_ds=float(mSNR.group(2))
        status=str[50:].strip()
        reStatus=re.compile('([\w.]+)/\(([\d\w]+)/(\d+)\)')
        mStatus = re.match(reStatus,status)
        status_status,status_time,status_retrain='','',0
        if mRate:
            status_status   =   mStatus.group(1)
            status_time     =   mStatus.group(2)
            status_retrain  =   int(mStatus.group(3))

        lineResult= [port, mode, rate_us, rate_ds, snr_us, snr_ds,status_status, status_time,status_retrain]
        return lineResult







