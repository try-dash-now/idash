#! /usr/bin/env python
__author__ = 'Sean Yu'
'''created @2015/10/11''' 
if __name__ == '__main__':
    import sys
    foldername ='..'# 'c:/workspace/gotest1' #'C:\\work\\auto\\dash2.1'##u'C:\\work\\auto\\workspace\\dash-ia' #'C:\\work\\auto\\winAI\\IA'#sys.argv[1]
    import os

    import re
    pComment=re.compile('\s*(#).*',re.MULTILINE|re.DOTALL)
    pBlank = re.compile('^\s*$', re.MULTILINE|re.DOTALL)
    def counterOfFile(filename):
        counter = 0
        with open(filename ) as f: #
            for line in f.readlines():
                if re.match(pComment, line):
                    continue
                elif re.match(pBlank, line):
                    continue
                else:
                    counter+=1
        return  counter, filename

    def counterOfFolder(foldername):
        allItems = os.listdir(foldername)
        counter =0
        message = ''
        for item in allItems:
            filename = foldername+'/'+item
            if os.path.isfile(filename) and filename.endswith('.py'):
                tmpcounter, filename = counterOfFile(filename)
                counter+=tmpcounter
                message += '\n%10d, %s'%(tmpcounter,filename)
            elif os.path.isdir(filename):
                subfoldername = foldername+'/'+item
                tmpcounter , folder =counterOfFolder(subfoldername)
                counter+=tmpcounter
                if tmpcounter:
                    message += '\n\n%10d, %s%s'%(tmpcounter,filename,folder.replace('\n','\n\t'))
        return  counter, message

    counter ,message= counterOfFolder(foldername)
    print(message)
    print('Total Number Of Python Code in %s: %d'%(foldername,counter))



