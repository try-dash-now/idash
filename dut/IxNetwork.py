'''
@author: speng
'''
'''
2015/7/2 Sean,
        add logging of IxNetwork
        redirect tcl 'puts'
        derive IxNetwork from a common Tcl class
'''

import os
import sys
import re
import time

pardir = os.path.dirname(os.path.realpath(os.getcwd()))
# pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir, 'lib']))
sys.path.append(os.path.sep.join([pardir, 'dut']))
print('\n'.join(sys.path))
#
from TclInter import TclInter


class IxNetwork(TclInter):
    iphost = None  # ""

    def __init__(self, name, attrs, logger=None, logpath=None):  # '10.245.34.201'
        TclInter.__init__(self, name, attrs, logger, logpath)
        self.msg = []
        if attrs.get('IP'):
            self.iphost = attrs['IP']
        if attrs.get("version"):
            self.version = attrs["version"]
        self.streamOut =''

    def openTcl(self):
        super(IxNetwork, self).openTcl()
        # self.tclInter.eval('package require  base64')
        self.tclInter.eval('source ../dut/ixia_tcl_lib.tcl')
        cwd = os.path.abspath('../dut').replace('\\', '/')  #os.getcwd().replace('\\','/')
        IxTclNetwork_path = '"' + cwd + '/IxTclNetwork' + '"'
        self.send('set_tcl_env ' + IxTclNetwork_path + ' ' + self.iphost + ' ' + self.version)
        self.find('::ixNet::OK')

        #         self.tcl.eval('lappend auto_path ' + IxTclNetwork_path)
        #         self.tcl.eval('package require IxTclNetwork')
        #         return '::ixNet::OK' == self.tcl.eval('ixNet connect ' + host_ip + ' -port 8009 -version 6.0')

    def getColumnInView(self, viewName, colName):
        cmd = 'read_Stats "%s" "%s"'%(viewName, colName)
        result = self.send(cmd)


        patList =re.compile('^\{(.*)\}$', re.DOTALL)
        result = re.match(patList, result).group(1)

        import shlex
        result= shlex.split(result)
        return result
    def checkRange(self,viewName,rawName,colName, maxLimit, minLimit=0):
        result = self.getColumnInView(viewName, colName)
        print('checkRange:', result)
        headline = self.getTrafficName()
        index = headline.index(rawName)
        print(rawName, 'index:', index)
        checkValue = float(result[index])
        if float(minLimit)<= checkValue and checkValue<=float(maxLimit):
            pass
        else:
            self.FailFlag =True
            if self.ErrorMessage ==None:
                self.ErrorMessage =''
            self.ErrorMessage +='view(%s) row(%s) item(%s) is %s, out of range [%s, %s]'%(viewName,rawName,colName, checkValue, minLimit, maxLimit)

    # ryi7/31/2015 begin
    def getStatsItem(self, viewName="Flow Statistics", item="Loss %"):
        name_list = []
        item_list = []
        # the variable item is aimed to get specified item in viewName,such as get "Rx Frames" statistics in "Traffic Item Statistics" page
        item_str = self.send('read_Stats "%s" "%s"' % (viewName, item)) #tclInter.eval('read_Stats "%s" "%s"' % (viewName, item))
        name_str = self.send('read_Name "%s" "%s"' % (viewName, item))
        if viewName == "Flow Statistics":
            name_str = name_str[2:-2]
            if '} {' in name_str:
                name_list = name_str.split('} {')
            else:
                name_list.append(name_str)
        else:
            name_str = ''.join(name_str.split('}'))
            name_str = ''.join(name_str.split('{'))
            name_list = name_str.split()
            #name_list.append(name_str)
        if '}'in item_str:
            test = ''.join(item_str.split('{'))
            item_str = ''.join(test.split('}'))
            item_list = item_str.split()
        else:
            item_list.append(item_str)
        int_type = ["Tx Frames", "Rx Frames", "Frames Delta", "Rx Bytes", "Store-Forward Min Latency (ns)",
                    "Store-Forward Min Latency (ns)", "Store-Forward Max Latency (ns)"]
        float_type = ["Loss %", "Tx Frame Rate", "Rx Frame Rate", "Tx Rate (Bps)",
                      "Rx Rate (Bps)", "Tx Rate (bps)", "Rx Rate (bps)", "Tx Rate (Kbps)",
                      "Rx Rate (Kbps)", "Tx Rate (Mbps)", "Rx Rate (Mbps)", "Packet Loss Duration (ms)"]
        if item in float_type:
            for i in range(len(item_list)):
                item_list[i] = float(item_list[i])
        elif item in int_type:
            for i in range(len(item_list)):
                item_list[i] = int(item_list[i])
        name = self.getTrafficName()
        start = 0
        end = 0
        finalDict = []
        for i in range(len(name)):
            while end < len(name_list):
                if name_list[end].find(name[i]) == -1:
                    finalDict.append(item_list[start:end])
                    start = end
                    break
                else:
                    end += 1
                    if end == len(name_list):
                        finalDict.append(item_list[start:end])
        return finalDict

    def startAllProtocols(self):
        print "start protocols..."
        #self.logfile.write("Info:start protocols...\n")
        status = self.send('ixNetStartAllProtocols')  #tclInter.eval('ixNetStartAllProtocols')
        time.sleep(1)
        if status.find('0') == 0:
            print "protocols started"
            #self.logfile.write("Info:protocol already started\n")
        else:
            self.msg.append("fail to start all protocols")
            #self.logfile.write("Fail:fail to start all protocol\n")
        return 0

    def stopAllProtocols(self):
        print "stop protocols..."
        #self.logfile.write("Info:stop protocols...\n")
        self.send('ixNetStopAllProtocols')  #tclInter.eval('ixNetStopAllProtocols')
        time.sleep(1)
        status = self.checkStatus()
        if status == "stopped":
            print "Protocol already stopped"
            #self.logfile.write("Info:Protocol already stopped\n")
        else:
            self.msg.append("fail to stop all protocols")
            #self.logfile.write("Fail:fail to stop all protocols\n")
        return 0

        # def startTraffic(self):
        #     print "apply statistics..."
        #     #self.logfile.write("Info:apply statistics...\n")
        #     #tmp = self.clearStats()
        #     #if tmp == True:
        #        # print "clearing statistics done"
        #     #time.sleep(1)
        #     self.send('ixNetApplyTraffic')#.tclInter.eval('ixNetApplyTraffic')
        #     print "start traffic..."
        #     #self.logfile.write("Info:start traffic...\n")
        #     status = self.checkStatus()
        #     if status == "stopped":
        #         self.send('start_traffic')#.tclInter.eval('start_traffic')
        #         time.sleep(5)
        #         #self.logfile.write("Info:traffic start done\n")
        #     elif status == "started":
        #         print "already started"
        #         #self.logfile.write("Info:traffic already started\n")
        #     elif status == "unapplied":
        #         print "traffic has not been generated"
        #         #self.logfile.write("Debug:traffic has not been generated"+'\n')
        #     return

    #ryi 7/16/2015 end

    # speng 7/21/2015 begin
    def loadConfigFile(self, configFileName='../lib/ixiaConfigFiles/ixia_7.30.tcl'):
        """
        load configurarion .tcl file or .ixncfg file
        .ixncfg file is preferred because loading .ixncfg file is much faster and less likely to cause ixiaNetwork to collapse
        raises exception if loading fails
        :param tclScriptName: file name of the .tcl file or .ixncfg file to load
        """
        pat = re.compile(r'\.(tcl|ixncfg)$', re.IGNORECASE)
        match = pat.search(configFileName)
        if match is None:
            raise Exception("config file must be a .tcl or .ixncfg file")

        suffix = match.group().lower()
        if suffix == '.tcl':
            print "loading tcl script from {} ...".format(configFileName)
            msg = 'source {}'.format(configFileName)
            result = self.tclInter.eval('source {}'.format(configFileName))
        elif suffix == '.ixncfg':
            print "loading ixncfg file from {} ...".format(configFileName)
            result = self.tclInter.eval('ixNetLoadIxncfgFile "{}"'.format(configFileName))

        if '0' != result:
            raise Exception("loading config file failed: " + result)
        print "success"
        return 0

    def regenerateTraffic(self):
        if self.checkStatus() == "started":
            print "Unable to regenerate a started/transmitting trafficItem"
            return 1
        if "" == self.tclInter.eval('get_traffic_items'):
            print "traffic items do not exist"
            return 1
        self.send('regenerate_traffic')
        return 0

    # speng 7/21/2015 end

    def startTraffic(self):
        if self.checkStatus() == "unapplied":
            if "" == self.tclInter.eval('get_traffic_items'):
                print "traffic items do not exist"
                return 1
            print "applying traffic..."
            res = self.send('ixNetApplyTraffic')
            if "::ixNet::OK" in res:
                print("success")
        if self.checkStatus() != "started":
            print "starting traffic..."
            self.send('start_traffic')  # tclInter.eval('start_traffic')
            # while self.checkStatus() != "started":
            #     self.tclInter.eval('after 50')
            print "success"
            return 0
        # if self.checkStatus() == "stopped":
        #     return 1


    def stopTraffic(self):
        print "stopping traffic..."
        status = self.checkStatus()
        if status == "stopped":
            print "already stopped"
            return 0
        if status == "started":
            self.send('stop_traffic')  # tclInter.eval('stop_traffic')
            while "stopped" != self.tclInter.eval('check_status'):
                self.tclInter.eval('after 100')
            print "traffic stopped"
            return 0
        if status == "unapplied":
            print "traffic is unapplied"
            return 1
        return 1


    def clearStats(self):
        if '::ixNet::OK' == self.send('clear_stats'):  # tclInter.eval('clear_stats')
            return 0
        else:
            return 1

    def checkStatus(self):
        return self.tclInter.eval('check_status')

    #ryi7/17/2015 begin
    def checkIxnResult(self):
        '''if failure flag is true, then case failed write error message to log file'''
        if self.FailFlag == True:
            self.logfile.write("!!!!!!!!!!!!!!!!!!!!!!case fail in ixNetwork!!!!!!!!!!!!!!!!!!!!!!!" + '\n')
            for i in range(len(self.ErrorMessage)):
                self.logfile.write("Fail:[" + str(i + 1) + ']:' + self.ErrorMessage[i] + '\n')
        else:
            self.logfile.write("!!!!!!!!!!!!!!!!!!!!!!case pass in ixNetwork!!!!!!!!!!!!!!!!!!!!!!!" + '\n')
        #ryi 7/17/2015 end


    def cacul_delta(self, d2, d1):
        return [d2[i] - d1[i] for i in range(len(d1))]

    #ryi 7/28/2015
    def checkTrafficAllBack(self, threshold=300.0):
        interval = 20
        index = 20
        flag = True
        while interval <= threshold:
            tmp = self.getStatsItem(viewName="Flow Statistics", item="Packet Loss Duration (ms)")
            minNum = min(tmp)
            if minNum == 0.0:
                flag = False
                time.sleep(15)
                interval = interval + index
            else:
                flag = True
                break
        if flag:
            pass
        else:
            msg = "streams are not all back!Case fail!"
            self.setFailFlag(msg)
            self.Write2Csv(msg)

    def getFlowName(self, row, viewName="Flow Statistics"):
        name = self.send('getFlowName "%s" "%s"' % (viewName, int(row)))
        return name
    #ryi 7/28/2015 end

    #ryi 7/29/2015 begin
    def CheckMcastPktLossDuration(self, threshold=300.0):
        PktLossDurationList = self.getStatsItem("Flow Statistics", "Packet Loss Duration (ms)")  #[0,3.5,4.8,3.5,4.8,43.5,0]
        name = self.getTrafficName()
        num = 0
        for item in range(len(PktLossDurationList)):
            tmp = []
            msg = ''
            result = []
            row = []
            zeroStreamName = []
            badStreamName = []
            tmp = PktLossDurationList[item]
            for i in range(len(tmp)):
                if tmp[i] <= 0.0:
                    row.append(i)
            if len(row) != 0:
                for j in range(len(row)):
                    zeroStreamName.append([str(i) + ":" + self.getFlowName(row[j], "Flow Statistics")])
                    time.sleep(0.5)
            import datetime
            print("item:", item)
            print('PktLossDurationList:',PktLossDurationList)
            maxNum = max(PktLossDurationList[item])
            minNum = min(PktLossDurationList[item])
            averNum = float((sum(PktLossDurationList[item])) / len(PktLossDurationList[item]))
            result.append([str(datetime.timedelta(seconds=minNum / 1000.)),
                           str(datetime.timedelta(seconds=averNum / 1000.)),
                           str(datetime.timedelta(seconds=maxNum / 1000.))])
            threshold = threshold * 1000
            if maxNum > threshold:  #or averNum > threshold or minNum > threshold:
                msg = [name[num], ' FAIL']

                for i in range(len(PktLossDurationList[item])):
                    if PktLossDurationList[item][i] > threshold:
                        badStreamName.append([str(i) + ":" + self.getFlowName(i, "Flow Statistics") , str(PktLossDurationList[item][i]) ])
                report2 = [['stream recover time longer than threshold(%f):'%(threshold/1000.0)]]+badStreamName
                self.setFailFlag(report2)
            else:
                msg = [name[num], ' PASS']
            print msg

            report = [
                        msg,
                        ['Service Recovery Time'],
                        ['Shortest', 'Average', 'Longest']
                    ]+result
            if len(row) != 0:
                report4 = [['stream never comes back:']]+zeroStreamName
                report = report + report4
                self.setFailFlag(report)

            if len(badStreamName) != 0:
                report = report + report2
            import os
            path = os.path.dirname(self.logfile.name)
            path = os.path.dirname(path)
            path = os.path.dirname(path)
            self.Write2Csv(report,'PacketLoss.csv',path)
            num += 1
        return 0

    def getTrafficName(self):
        name = self.send('getTrafficName')
        #from common import csvstring2array
        #name = csvstring2array(self.send('getTrafficName'))
        name = name.split('\n')    #methods1
        #name = name.replace('{', '[').replace('}', '],')   #methods2
        #name = name.split(', ')
        #name = name.split(',')
        return name

    #ryi 8/5/2015 end
 #ryi 24/8/2015 begin
    def checkVdslTrafficAllBack(self, threshold=300):
        import math
        interval = 20
        index = 20
        flag = True
        tmp = self.getStatsItem("Traffic Item Statistics", "Frames Delta")
        time.sleep(10)
        while interval <= threshold:
            tmp1 = self.getStatsItem("Traffic Item Statistics", "Frames Delta")
            minus = []
            for item in range(len(tmp1)):
                for j in range(len(tmp1[item])):
                    minus.append(math.fabs(tmp1[item][j] - tmp[item][j]))
            if max(minus) == 0:
                flag = True
                break
            else:
                flag = False
                time.sleep(5)
                interval = interval + index
                tmp = tmp1
        if flag:
            pass
        else:
            msg = "streams are not all back!Case fail!"
            self.setFailFlag(msg)
            self.Write2Csv(msg)
        return 0

    def checkVdslLossDuration(self, threshold = 0.30):
        PktLossDurationList = self.getStatsItem("Flow Statistics", "Packet Loss Duration (ms)")
        name = self.getTrafficName()
        threshold = threshold * 1000
        num = 0
        for item in range(len(PktLossDurationList)):
            msg = ''
            result = []
            badStreamName = []
            import datetime
            maxNum = max(PktLossDurationList[item])
            minNum = min(PktLossDurationList[item])
            averNum = float((sum(PktLossDurationList[item])) / len(PktLossDurationList[item]))
            result.append([str(datetime.timedelta(seconds=minNum / 1000.)),
                           str(datetime.timedelta(seconds=averNum / 1000.)),
                           str(datetime.timedelta(seconds=maxNum / 1000.))])
            if maxNum > threshold:  #or averNum > threshold or minNum > threshold:
                msg = [name[item], ' FAIL']
                for i in range(len(PktLossDurationList[item])):
                    if PktLossDurationList[item][i] > threshold:
                        badStreamName.append([str(i) + ":" + self.getFlowName(i, "Flow Statistics"), str(PktLossDurationList[item][i])])
                report2 = [['stream recover time longer than threshold(%f):'%(threshold/1000.0)]]+badStreamName
                self.setFailFlag(report2)
            else:
                msg = [name[item], ' PASS']
            print msg
            report = [
                        msg,
                        ['Service Recovery Time'],
                        ['Shortest', 'Average', 'Longest']
                    ]+result
            if len(badStreamName) != 0:
                report = report + report2
            import os
            path = os.path.dirname(self.logfile.name)
            path = os.path.dirname(path)
            path = os.path.dirname(path)
            self.Write2Csv(report,'PacketLoss.csv',path)
        return 0
#ryi 26/8/2015 end


