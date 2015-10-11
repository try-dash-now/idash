#! /usr/bin/env python
__author__ = 'Sean Yu'
'''created @2015/10/11'''

# -*- coding: UTF-8 -*-
import sys
import time
import  os

import telnetlib

#reload(sys)
#sys.setdefaultencoding('utf-8')

#from CSession import CSession
#attr={'TIMEOUT': 10, 'CMD':'ftp localhost'}
#s = CSession('sut',attr)
import time
filetype = sys.argv[1].strip().lower()
import time
host = sys.argv[2]
port = 23
import re
rehostport = re.compile('\s*(\S+)\s+(\S+)\s*' )
mhostport = re.match(rehostport, host)
if mhostport:
    host = mhostport.group(1)
    port = mhostport.group(2)


csv_name = sys.argv[3]
log = '%s_%s_%s.log'%(host,csv_name, time.strftime("%Y%m%d_%H%M%S"))
log= log.replace(' ', '_')
try:
    index = 1
    import csv
    with open(csv_name, 'rb') as csvfile:
        case = csv.reader(csvfile)
        print(case)
        returncode = True

        s = telnetlib.Telnet(host, port)
        print(s.expect(['[\s\S]+'],1)[2])
        #print(resp)
        defaultTime= 1
        defExp = '[\s\S]*'
        if filetype =='txt':
            defExp = 'pattern never happen'
            defaultTime= 2

        for step in case:
            if len(step)==0:
                continue

            sys.stdout.write(s.expect(['[\s\S]+'] ,1)[2])
            #print('-'*80)
            #print('step\t%d: %s'%(index, step[0]))

            s.write(step[0])
            s.write(os.linesep)
            time.sleep(0.5)
            timeout=defaultTime
            lenS = len(step)

            if lenS>2:
                 step[2]= step[2].strip()
                 if step[2]!='':
                         timeout = float(step[2])
            elif lenS==2:
                step.append(defaultTime)
            elif lenS==1:
                step.append(defExp)
                step.append(defaultTime)
            else:
                step = ['', defExp,defaultTime]
            #s.sendline(step[0])
            #print('-'*80)

            if  len(step)!=1 :
                    #print('expect\t%d: %s'%(index, step[1]))
                response = s.expect([step[1]],timeout)
                if response[0]!=0 and filetype!='txt':
                    raise Exception("can't find:%s"%step[1])
                sys.stdout.write(response[2])
            else:
                #s.expect('[\s\S]*', 5)
                response = s.expect(['[\s\S]+'],2)
                sys.stdout.write(response[2])

            index+=1
            time.sleep(0.5)
        print('\n**********************PASS**********************')
except Exception, e:
    print(e)
    print('\n!!!!!!!!!!!!!!!!!!!!!!!FAIL!!!!!!!!!!!!!!!!!!!!!!!')
    returncode = True
    sys.exit(1)



