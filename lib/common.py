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
    lines= csvstring.replace('\\r\\n','\\n').split('\\n')
    a=[]
    for line in lines:
        csvfile= io.StringIO(unicode(line, "utf-8"))
        for row in csv.reader(csvfile, quoting=csv.QUOTE_MINIMAL):
            a.append(row)
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
def array2csvfile(array, csvfile, Newline = ''):
    with open(csvfile, 'w',newline =Newline) as f:  #,newline =''
        writer = csv.writer(f)
        for row in array:
            writer.writerow(row)

def FunctionArgParser(stringOfArgs):
    def GetFunArg(*argvs, **kwargs):
        Argvs =[]
        Kwargvs ={}
        for arg in argvs:
            Argvs.append(arg)
        for k in kwargs.keys():
            Kwargvs.update({k:kwargs[k]})
        return Argvs, Kwargvs
    print('stringOfArgs:', stringOfArgs)
    args, kw = eval('GetFunArg(%s)'%stringOfArgs)
    return args, kw