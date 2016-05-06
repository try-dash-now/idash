__author__ = 'Sean Yu'
'''created @2016/4/22'''
from dut import dut
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from pprint import pformat as pp
g_retry_counter = 10
def retry(fun):
    def inner(*arg, **kwargs):

        retry_counter = 1
        tmp_g_retry_counter= g_retry_counter
            #g_retry_counter
        while (retry_counter-1)<tmp_g_retry_counter:
            retry_counter+=1
            try:
                print('retry %d/%d %s'%(retry_counter,tmp_g_retry_counter, fun.__name__))
                response = fun(*arg, **kwargs)

                break
            except Exception as e:
                if  retry_counter>=tmp_g_retry_counter:
                    raise e
                else:

                    print(pp(arg))
                    print(pp(kwargs))
                    continue
        return  response

    return inner
import time
FireFox =True
#binary = FirefoxBinary(firefox_path='./')
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os
class webgui(dut, object):
    obj     = None
    path = None
    common_wait_interval = 1
    old_retry = 5
    driver = None
    def quit(self):
        if self.driver:
            self.driver.quit()
    def __init__(self, name, attr =None,logger=None, logpath= None, shareData=None):
        #try:
        dut.__init__(self, name,attr,logger,logpath,shareData)
        self.log_file =self.logfile


        binary = None
        if FireFox:
            binary_path = './selenium/webdriver/firefox'
            if os.path.exists(binary_path):
                binary = FirefoxBinary(binary_path)

            self.driver= webdriver.Firefox(firefox_binary=binary)

            self.driver.log_file= self.logfile
        else:
            self.driver = webdriver.Chrome()
            #webdriver.Chrome.__init__(self)
        #webdriver.Firefox.__init__(self,firefox_profile=profile)#, firefox_profile=profile, firefox_binary=)#

        #except:
        #    webdriver.Chrome.__init__(self)
            #webdriver.Firefox.__init__(self)

        if self.attribute.has_key('INTERVAL'):
            self.common_wait_interval = self.attribute['INTERVAL']
            time.sleep(0.5)
        else:
            self.common_wait_interval = 1

    @retry
    def set_retry(self, retry_max):
        global g_retry_counter
        self.old_retry = g_retry_counter
        g_retry_counter = retry_max
    @retry
    def restore_retry(self):
        global g_retry_counter
        g_retry_counter =self.old_retry
    @retry
    def xfind(self, path, type):
        if path is not None:
            self.path = path
        if str(type).lower() == 'xpath':
            function = self.driver.find_element_by_xpath
        elif str(type).lower() == 'name':
            function = self.driver.find_element_by_name
        elif str(type).lower() == 'text':
            function = self.find_element_by_link_text
        self.obj = function(self.path)
        return  self.obj
    @retry
    def xsend(self, cmd, path=None, type_by= 'xpath'):
        element = self.xfind(path, type_by)
        element.send_keys(cmd)
        #time.sleep(1)
    @retry
    def xclick( self, xpath=None, type_by='xpath'):
        element = self.xfind(xpath, type_by)
        element.click()
        self.sleep(1)
    @retry
    def xclear( self, xpath=None, type_by='xpath'):
        element = self.xfind(xpath, type_by)
        element.clear()
        #time.sleep(1)
    @retry
    def xrefill(self, data, xpath, type_by = 'xpath'):
        element = self.xfind(xpath, type_by)
        element.clear()
        element.send_keys(data)
    @retry
    def xselect(self, value, xpath=None, type_by='xpath'):
        self.obj = Select(self.xfind(xpath, type_by))
        self.obj.select_by_visible_text(value)
        self.sleep(1)
    @retry
    def xget(self,url=None):
        if url is not None:
            self.curr_url = url
        self.driver.get(self.curr_url)
        self.sleep(1)
    @retry
    def have_text(self, exp_txt, path, type_by = 'xpath'):
        try:
            elem = self.xfind(path, type_by)
            if elem.text.find(exp_txt)!=-1:
                return True
            else:
                return False
        except Exception as e:
            return False
    def closeSession(self):
        super(webgui,self).closeSession()
        self.quit()
    def xcheck(self, xpath=None, type_by='xpath'):
        self.obj = self.xfind(xpath, type_by)
        if not self.obj.is_selected():
            self.obj.click()
            self.sleep(1)
    def xuncheck(self, xpath=None, type_by='xpath'):
        self.obj = self.xfind(xpath, type_by)
        if self.obj.is_selected():
            self.obj.click()
            self.sleep(1)
