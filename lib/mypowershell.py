print('aaa')
import sys
from subprocess import PIPE, Popen
import  subprocess
from threading  import Thread
myps = '%SystemRoot%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe'

cmd=['dir',
     'powershell',
     'cd /'
     'dir',
     'ping 127.0.0.1',
     '']
import sys

ps = Popen(['cmd.exe'],shell=True, stdin=PIPE, stderr=sys.stdout, stdout=sys.stdout)
import time

for c in cmd:
    ps.stdin.write(c)
    ps.stdin.write('\r\n')
    #o=ps.stdout.readline()
    #print(o)
