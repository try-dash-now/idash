1. install python2.7.12
python -m pip install --upgrade pip
go to :http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
download numpy-1.11.2+mkl-cp27-cp27m-win32.whl
pip install "C:\numpy-1.11.2+mkl-cp27-cp27m-win32.whl"
paramiko\paramiko-master\python setup.py install
py2exe-0.6.9.win32-py2.7
pycrypto-2.6.win32-py2.7
pyhook-1.5.1.win32-py2.7
pyreadline-2.1
PyUserInput-0.1.10
edit C:\Python27\Lib\hashlib.py, goto line 137, comment line 137 and 138 out as below http://gis.stackexchange.com/questions/181384/qgis-corrupted-plugins-upon-reinstallation
	try:
		import _hashlib
		new = __hash_new
		__get_hash = __get_openssl_constructor
	#    algorithms_available = algorithms_available.union(
	#        _hashlib.openssl_md_meth_names)
	except ImportError:
		new = __py_new
		__get_hash = __get_builtin_constructor
pip install -U selenium
