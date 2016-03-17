#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys, time, os, traceback
pardir =os.path.dirname(os.path.realpath(os.getcwd()))
subfolder = ['lib', 'dut', '../../workspace/tr249/dlv', '../../workspace/tr249/product']
for sub in subfolder:
    libpath = os.path.sep.join([pardir,sub])
    libpath = os.path.abspath(libpath)
    if libpath not in sys.path:
        sys.path.insert(0,libpath)

if __name__ =='__main__':
    from ia import ia
    tmpout = sys.stdout
    f = open(os.devnull, 'w')

    try:
        file_name =os.path.basename( __file__)
    except NameError:  # We are the main py2exe script, not a module
        file_name = os.path.dirname(os.path.abspath(sys.argv[0]))


    print('''%s
    or
%s bench_file DUT1 [DUT2, DUT3 ...]
          '''%(file_name, file_name))
    sys.stdout = f

    if len(sys.argv)>2:
        benchfile = sys.argv[1]
        dutNames = sys.argv[2:]
    else:
        benchfile = './bench.csv'
        dutNames = ['PS']
    i=ia(benchfile, dutNames)
    sys.stdout = tmpout
    print('#'*80)

    flagEndCase = False
    i.do_setCheckLine('enable')
    while not i.flagEndCase:
        try:
            #i.complete('show alar\t', 0)
            i.cmdloop()

            time.sleep(.1)
        except Exception as e:
            msg = traceback.format_exc()
            print(msg)

    del i
    os._exit(0)
