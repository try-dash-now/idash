__author__ = 'Sean Yu'
'''created @2016/4/26''' 

import datetime,os, pprint
from common import bench2dict
from runner import createLogDir, createLogger, releaseDUTs, initDUT
class case(object):
    error_message = None
    fail_flag = False
    bench_file = None
    bench = None
    log_dir = None
    name = None
    logger = None
    duts = None
    dut_names = None
    share_data = None
    dry_run = False
    def __init__(self, name=None, bench=None, log_folder=None, dry_run =False):
        self.name = name if name else 'case'
        self.log_dir = '../../log' if log_folder is None else log_folder

        if not os.path.exists(self.log_dir ):
            os.mkdir(self.log_dir )
        self.log_dir = createLogDir(self.name, self.log_dir)
        self.logger = createLogger(name, self.log_dir)
        self.load_bench(bench)
        self.error_message=''
        self.duts={}
        self.dut_names =[]
        self.share_data = {}
        self.set_dry_run(dry_run)

    def end_case(self):
        self.info('releasing duts', self.duts)
        releaseDUTs(self.duts, self.logger)
        self.info('case ended')
    def set_dry_run(self,flag):
        if flag:
            self.dry_run = True
        else:
            self.dry_run = False

    def init_duts(self, *dut_names):
        tmp =[]
        for dut_name in dut_names:
            if dut_name not in self.bench.keys():
                self.error(dut_name, 'is not defined in bench file ', self.bench_file)
                raise Exception('%s is not defined in bench file %s'%(dut_name, self.bench_file))
            elif dut_name in self.dut_names:
                self.info(dut_name, ' already existed!')
                #raise Exception('%s already existed! '%(dut_name, self.bench_file))
            else:
                tmp.append(dut_name)
        self.dut_names +=tmp
        self.duts.update(initDUT(self.error_message,self.bench,self.dut_names,self.logger,self.log_dir, self.share_data,self.dry_run))
        return  self.duts



    def load_bench(self, bench_file=None):
        bench_file= self.bench_file if bench_file is None else bench_file
        if bench_file is not None:
            if os.path.exists(bench_file):
                self.bench =  bench2dict(bench_file)
                self.set_bench_file(bench_file)
            else:
                self.info('%s is not exist or not a valid bench file, current work dir %s'%(bench_file,os.getcwd()))
        else:
            self.info('bench file is None!')

    def setFail(self, msg):
        if type('') != type(msg):
            msg = str(msg)
        if self.error_message is None:
            self.error_message=''
        self.error_message+=msg+'\n'
        self.fail_flag=True
        with open('%s/case_error.txt'%self.log_dir, 'a+') as ef:
            ef.write(msg+'\n')
    def formatMsg(self, *msg):
        now =datetime.datetime.now()
        new_msg = ','.join([pprint.pformat(x,indent=2,width=256) for x in msg])
        msg = '%s\t%s\t%s'%(now.isoformat().replace("T", ' '), self.name, new_msg)
        print(msg)
        return msg
    def info(self, *msg):
        '''
        add info message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.info(msg)

    def error(self, *msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)
        if self.logger:
            self.logger.error(msg)
        self.setFail(msg)

    def debug(self, *msg):
        '''
        add error message to logger
        '''
        msg = self.formatMsg(msg)

        if self.logger:
            self.logger.debug(msg)
    def set_bench_file(self, bench_file):
        if os.path.exists(bench_file):
            self.bench_file = os.path.abspath(bench_file)
        else:
            self.error('bench file  is not existed: %s'%bench_file)
    def check_sut_fail_flag(self):
        for sut in self.duts.keys():
            if sut is not 'tc':
                dut_inst = self.duts[sut]
                from dut import dut
                if isinstance(dut_inst,dut):
                    if dut_inst.FailFlag:
                        self.error(dut_inst.ErrorMessage)


    def __del__(self):
        for sut in self.duts.keys():
            if sut is not 'tc':
                dut_inst = self.duts[sut]
                from dut import dut
                if isinstance(dut_inst,dut):
                    dut_inst.SessionAlive =False



