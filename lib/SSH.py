__author__ = 'Sean Yu'
'''created @2015/12/4''' 
import ssh

import os, sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    if libpath not in sys.path:
        sys.path.insert(0,libpath)

import dut
class SSH(dut.dut, object):

    def __init__(self, name, attr =None,logger=None, logpath= None, shareData=None):
        dut.dut.__init__(self, name,attr,logger, logpath, shareData)

        client = ssh.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(ssh.WarningPolicy)
#        client.connect(hostname, port, username, password)


#!/usr/bin/env python

# Copyright (C) 2011  Jeff Forcier <jeff@bitprophet.org>
#
# This file is part of ssh.
#
# 'ssh' is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# 'ssh' is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with 'ssh'; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Suite 500, Boston, MA  02110-1335  USA.


import base64
import getpass
import os
import socket
import sys
import traceback

import ssh




ssh.util.log_to_file('demo_simple.log')



# now, connect and use ssh Client to negotiate SSH2 across the connection
try:
    client = ssh.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(ssh.WarningPolicy)
    print '*** Connecting...'
    client.connect('10.2.14.83', 22, 'root', 'root')
    stdin, stdout, stderr = client.exec_command('show length 1:24')
    a = stderr.readline()
    chan = client.invoke_shell()
    r = chan.send('show length 1:2')
    r = chan.send('show length 1:4')
    r = chan.recv(256)
    import interactive
    interactive.interactive_shell(chan)
    chan.close()
    client.close()

except Exception, e:
    print '*** Caught exception: %s: %s' % (e.__class__, e)
    traceback.print_exc()
    try:
        client.close()
    except:
        pass
    sys.exit(1)
