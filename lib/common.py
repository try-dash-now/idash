# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/9/18 
'''

# -*- coding:  UTF-8 -*-

__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
"""
created 2015/5/8 
"""
import io,csv,re
DELIMITER = '[${PATTERN_NOT_EXIST}$]'
import time
def addPath2syspath():
    import os
    pardir =os.path.dirname(os.path.realpath(os.getcwd()))
    subfolder = ['lib', 'dut']
    for sub in subfolder:
        libpath = os.path.sep.join([pardir,sub])
        if libpath not in sys.path:
            sys.path.insert(0,libpath)

def bench2dict(csvfile, delimiter='='):
    reComment = re.compile('\s*#', re.I)

    a =csvfile2array(csvfile)
    d={}

    for i in a:
        l = len(i)
        if l <2:
            continue
        name = str(i[0]).strip()
        if re.match(reComment,name):
            continue

        if l==2:
            name = str(i[0]).strip()
            value = i[1]
            d.update({name:value})
        else :
            name = str(i[0]).strip()
            if name=='':
                continue
            attr=i[1:]
            d.update({name:{}})

            for a in attr:
                if len(a)>2:
                    if re.match(reComment,a):
                        break
                    attrname, value= a.split(delimiter)
                    d[name].update({attrname.strip():value})


    return d
def csvfile2dict(csvfile):
    a =csvfile2array(csvfile)
    d={}
    for i in a:
        if len(i)>1:
            d.update({str(i[0]).strip():str(i[1]).strip()})
    return d
def csvstring2array(csvstring):
    lines= csvstring.split('\n')#.replace('\\r\\n','\\n').split('\\n')
    a=[]
    for line in lines:
        csvfile= io.StringIO(unicode(line, "utf-8"))
        for row in csv.reader(csvfile, quoting=csv.QUOTE_MINIMAL):
            tmp =[]
            for col in row:
                tmp.append(col.replace('\\r', '\r').replace('\\n', '\n'))
            a.append(tmp)
    return a
def csvfile2array(csvfile, Delimiter = ',', Newline = '', Quoting=csv.QUOTE_ALL):
    a=[]
    import os
    if os.name!='nt':
        f= open(csvfile, 'r', newline= Newline )
    else:
        f = open(csvfile,'r')
    reader = csv.reader(f, delimiter=Delimiter, quoting=Quoting)
    for row in reader:
        a.append(row)
    return a
def array2csvfile(array, csvfile, Newline = '\n'):
    with open(csvfile, 'ab+') as f:  #,newline ='',newline =Newline
        writer = csv.writer(f, lineterminator = Newline)
        if type(array)==type([]):
            for row in array:
                if type(row)==type([]):
                    writer.writerow(row)
                elif type(row)==type(()):
                    writer.writerow(list(row))
                else:
                    writer.writerow([row])
        else:
            writer.writerow([array])

def FunctionArgParser(stringOfArgs):
    def GetFunArg(*argvs, **kwargs):
        Argvs =[]
        Kwargvs ={}
        for arg in argvs:
            Argvs.append(arg)
        for k in kwargs.keys():
            Kwargvs.update({k:kwargs[k]})
        return Argvs, Kwargvs
    try:
        args, kw = eval('GetFunArg(%s)'%stringOfArgs)
    except Exception as e:

        from common import csvstring2array
        args = csvstring2array(stringOfArgs)[0]
        newargs = []
        for a in args:
            tmp = a.strip()
            if tmp.startswith('"') or tmp.startswith("'"):
                newargs.append(tmp)
            else:
                newargs.append('"%s"'%tmp)
        newstringArg= ','.join(newargs)
        args, kw = eval('GetFunArg(%s)'%newstringArg)


    return args, kw

def GetFunctionbyName(classobj, functionName):
    import inspect,re
    members = inspect.getmembers(classobj)
    objFun = None
    for item in members:
        if re.match(item[0],functionName, re.I):
            objFun =classobj.__getattribute__(item[0])
            break
    return  objFun
def DumpDict(dicts):
    import operator
    d = {}
    s=''

    key =dicts.keys()
    key = sorted(key)
    for k in key:
        n = k
        o= dicts[k]
        if k!='__builtins__':
            s+='\t%s: %s\n'%(repr(n),repr(o).replace('\\\\', '\\'))
            if k=='self':
                selfkey = dicts['self'].__dict__.keys()
                selfkey = sorted(selfkey)
                for member in selfkey:
                    s+='\t\t%s: %s\n'%(repr(member),repr(dicts['self'].__dict__[member]).replace('\\\\', '\\'))
    return s
import inspect
import sys, traceback

def DumpStack(e):

    exc_type, exc_value, exc_traceback = sys.exc_info()
    str = traceback.format_exception(exc_type, exc_value,exc_traceback)
    str = ''.join(str)
    #str=str.replace('\n', '\n*\t')

    trace= inspect.trace()
    lastframe = trace[-1][0]

    locals=  DumpDict(lastframe.f_locals)
    globals= DumpDict(lastframe.f_globals)

    return '''
ERROR MESSAGE:
   %s
%s-------------------------------------------------------------------------------
globals=>
%s
locals =>
%s
'''%(e.__str__(),str, globals,locals)


