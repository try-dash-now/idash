__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
import os,sys
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
libpath = os.path.sep.join([pardir,'lib'])
if libpath not in sys.path:
    sys.path.insert(0,libpath)



from HttpServer import  ThreadingHttpServer, HttpHandler
port =9999
if len(sys.argv)>1:
    port =int(sys.argv[1])
httpd=ThreadingHttpServer(('',port), HttpHandler)

from socket import *


try:
    hostip=''
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(("", 1234))
    #sq = socket(AF_INET, SOCK_DGRAM)
    s.connect(("10.0.0.4", 1234))

    domain = getfqdn()
    hostip = s.getsockname()[0]
    s.close()
except Exception as e:
    import traceback
    msg = traceback.format_exc()
    print(msg)
hostname =gethostname()

print("Server started on %s (%s),port %d....."%(hostname,hostip,port))
#print('Process ID:%d'%os.geteuid())
httpd.serve_forever()

try:
    s.close()
except:
    pass


