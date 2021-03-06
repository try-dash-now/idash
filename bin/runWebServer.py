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

from socket import *


try:
    hostip=''
    s = socket(AF_INET, SOCK_DGRAM)
    port_b= 4321
    s.bind(("", port_b))
    #sq = socket(AF_INET, SOCK_DGRAM)
    s.connect(("10.0.0.4", port_b))

    domain = getfqdn()
    hostip = s.getsockname()[0]
    httpd=ThreadingHttpServer((hostip,port), HttpHandler)

    s.close()
except Exception as e:
    import traceback
    msg = traceback.format_exc()
    print(msg)
hostname =gethostname()
try:
    s.close()
except:
    pass
print("Server started on %s (%s),port %d....."%(hostname,hostip,port))
#print('Process ID:%d'%os.geteuid())
httpd.serve_forever()




