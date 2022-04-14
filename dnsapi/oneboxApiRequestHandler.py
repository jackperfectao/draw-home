# -*- coding:utf-8 -*-
'''OneboxRequestHandler基类'''
import BaseHTTPServer
import urllib
import time
import random
from SocketServer import ThreadingMixIn
from abc import abstractmethod
from config import HTTPS

class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    '''多线程https服务'''

class OneboxApiRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    '''OneboxRequestHandler基类'''
    filename = "".join(random.sample('1234567890abcdefghijklmnopqrstuvwxyz', 16))

    @classmethod
    def get_filename(cls):
        '''获取文件名'''
        return cls.filename

    @classmethod
    def set_filename(cls, filename):
        '''设置文件名'''
        cls.filename = filename


    lastest_action_time = time.time()

    @classmethod
    def modify_time(cls):
        '''获取最后修改时间'''
        return cls.lastest_action_time

    @classmethod
    def set_modify_time(cls):
        '''设置当前时间为最后修改时间'''
        cls.lastest_action_time = time.time()

    @classmethod
    def get_method_and_parm(cls, path):
        '''获取参数'''
        try:
            method = path.split('/')[-1].lower().split('?')[0]
        except:
            method = ""
        parm = {}
        try:
            if len(path.split('?')) > 1:
                for i in path.split('?')[1].split("&"):
                    parm[urllib.unquote(i.split('=')[0])] = urllib.unquote(i.split('=')[1].strip())
        except:
            print "Parameter Error:" + path
        return method, parm

    @abstractmethod
    def do_GET(self):
        '''处理GET'''
        pass

    @abstractmethod
    def do_PUT(self):
        '''处理PUT'''
        pass

    def do_POST(self):
        '''POST请求处理逻辑和PUT一致'''
        self.do_PUT()

    def do_HEAD(self):
        '''HEAD请求处理逻辑和GET一致'''
        self.do_GET()

    def write_data(self, code, data="", contentType="text/html"):
        '''回写数据'''
        self.send_response(code)
        self.send_header("Content-type", contentType)
        self.end_headers()
        self.wfile.write(data)
        if not HTTPS:
            self.wfile.close()
