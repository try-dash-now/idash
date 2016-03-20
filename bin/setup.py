# -*- coding:  UTF-8 -*-
__author__ = 'Sean Yu'
__mail__ = 'try.dash.now@gmail.com'
'''
created 2015/11/10
'''

##################################
#http://www.py2exe.org/index.cgi/ExeWithEggs, install ssh by command 'python setup.py install_scripts to ExeWithEggs
##################################
import os,sys
pardir =os.path.dirname(os.path.realpath(__file__))
pardir= os.path.sep.join(pardir.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([pardir,'lib']))
sys.path.append(os.path.sep.join([pardir,'test']))
sys.path.append(os.path.sep.join([pardir,'dut']))
print('\n'.join(sys.path))
import wx
import Tkinter
from colorama import *
import os
import glob
from py2exe.build_exe import py2exe as build_exe
import zipfile



class tcltk(Tkinter.Tk):
    def __init__(self):
        Tkinter.Tk.__init__(self, None, None, 'Tk', 0)
tcltk()
from dut import dut
logpath = '../../log'
if not os.path.exists(logpath):
    os.mkdir(logpath)

def compressFile(infile,outfile):
    import zipfile
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    modes = { zipfile.ZIP_DEFLATED: 'deflated',
              zipfile.ZIP_STORED:   'stored',
              }

    print 'creating archive'
    zf = zipfile.ZipFile(outfile, mode='w')
    try:
        zf.write(infile,outfile, compress_type=compression)
    except :
        import traceback
        print(traceback.format_exc())
        print 'closing'
        zf.close()
    return outfile
class MediaCollector(build_exe):
    def copy_extensions(self, extensions):
        build_exe.copy_extensions(self, extensions)

        # Create the media subdir where the
        # Python files are collected.
        media = 'selenium\\webdriver\\firefox'
        full = os.path.join(self.collect_dir, media)
        if not os.path.exists(full):
            self.mkpath(full)

        # Copy the media files to the collection dir.
        # Also add the copied file to the list of compiled
        # files so it will be included in zipfile.
        files = [
                '''C:\\Python27\\Lib\\site-packages\\selenium\\webdriver\\firefox\\webdriver.xpi'''
                 #   '''C:/Python27/Lib/site-packages/selenium-2.46.0-py2.7.egg/selenium/webdriver/firefox/webdriver.xpi''',
                 # '''C:\\Python27\\Lib\\site-packages\\selenium\\webdriver\\firefox\\webdriver_prefs.json'''
                 ]
        for f in files :#glob.glob('tools/'):
            name = os.path.basename(f)
            try:
                self.copy_file(f, os.path.join(full, name))
                self.compiled_files.append(os.path.join(media, name))
            except Exception as e:
                import traceback
                print(traceback.format_exc())

from distutils.core import setup
import py2exe
dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll',
                #'tcl84.dll',
                #'tk84.dll',
                'MSVCP90.dll']
py2exe_options = {
        'cmdclass': {'py2exe': MediaCollector},
        # [...] Other py2exe options here.
    }

wd_base = 'C:/Python27/Lib/site-packages/selenium-2.46.0-py2.7.egg/selenium/webdriver/'
RequiredDataFailes = [
    ('selenium/webdriver/firefox', ['%s\\firefox\\webdriver.xpi'%(wd_base), '%s\\firefox\\webdriver_prefs.json'%(wd_base)])
]

def copy_dir(dir_path):
    #dir_path = 'test'
    base_dir = os.path.join('.', dir_path)
    for (dirpath, dirnames, files) in os.walk(base_dir):
        for f in files:
            print(f)
            if f.endswith('.py'):
                continue
            yield os.path.join(dirpath.split(os.path.sep, 1)[1], f)
try:
    dist = setup(
        windows = [],#'../bin/dash.py'
        console=["./cr.py",
                    "./sr.py",
                    './y.py',#"../lib/ia.py",
                    "../bin/ImportModule.py",#to include tcl things in the distribute package
                ],

        data_files= [
                       '../LICENSE.TXT',
                       ( 'bench',['../bench/e7.login','../bench/e7raw.login', '../bench/lnx.login', '../bench/ixiaNetwork.login']),
                        ('dut', [ f for f in copy_dir('../dut')]),
                        ('dut/IxTclNetwork', [ f for f in copy_dir('../dut/IxTclNetwork')]),
                        ('dut/IxTclNetwork/Generic', [ f for f in copy_dir('../dut/IxTclNetwork/Generic')]),
                       ('bin',[]),
                       ('bin', [f for f in copy_dir('../test')]),
                       ('selenium', []),
                       #('dut', [ f for f in copy_dir('../dut')]),


                       ],
        options = {"py2exe":
                       {
                          "unbuffered": True,

                          #"compressed": 2,
                          "optimize": 2,
                          "includes":[],# includes,
                          "excludes":[],# excludes,
                          "packages": [],#packages,
                          "dll_excludes": dll_excludes,
                          #"bundle_files": 1,
                          "dist_dir": "dist",
                          "xref": False,
                          "skip_archive": True,
                          "ascii": False,
                          "custom_boot_script": '',

                        }
                   },
        **py2exe_options
    )
except:
    import traceback
    print(traceback.format_exc())


folder = '../../dist'
for op in sys.argv:

    indexOfd = op.find('-d')
    if indexOfd !=-1:
        folder = sys.argv[sys.argv.index(op)+1]
        break




import shutil
targetDir = os.sep.join([folder, 'bin'])
excludedFolder =['bin',
                 'lib',
                 'bench',
                 'dut',
                 ]


try:
    IxtclNetworkPath = os.path.abspath('../dut/IxTclNetwork')
    #shutil.copytree(IxtclNetworkPath, os.path.abspath(targetDir+'/../dut/IxTclNetwork'))
except Exception as e:
    print(e)
    pass

for file in os.listdir(folder):
    sourceFile = os.path.join(folder,  file)
    targetFile = os.path.join(targetDir,  file)
    #cover the files
    if os.path.basename(sourceFile)=='LICENSE.TXT':
        continue
    if os.path.isfile(sourceFile):
        try:
            filename = os.path.basename(sourceFile)
            if filename not in ['ImportModule.exe']:
                open(targetFile, "wb").write(open(sourceFile, "rb").read())
            os.remove(sourceFile)
            pass
        except:
            pass
    elif os.path.isdir(sourceFile) and os.path.basename(sourceFile) not in excludedFolder:
        try:
            shutil.rmtree(targetFile)
        except:
            pass
        shutil.copytree(sourceFile, targetFile)
        shutil.rmtree(sourceFile)

