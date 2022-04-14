#!/home/tops/bin/python
# -*- coding:utf-8 -*-
'''MOCK DNS API'''
import json
import os
import sys
import ssl
import time
import traceback
import threading
import log
import random
from config import *
from oneboxApiRequestHandler import OneboxApiRequestHandler
from oneboxApiRequestHandler import ThreadedHTTPServer
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

WRITE_LOCK = threading.Lock()


class ApiRequestHandler(OneboxApiRequestHandler):
    '''RequestHandler'''
    logger = log.getLogger("dns_api.log")
    @classmethod
    def write_action(cls, client_address, action, name, ip):
        '''写入修改记录'''
        WRITE_LOCK.acquire()
        writeTime = time.time()
        os.system("echo %s %s %s %s %s >> %s" % ("%f" % writeTime, client_address, action, name, ip, cls.get_filename()))
        ApiRequestHandler.set_modify_time()
        WRITE_LOCK.release()
        timeOut = 590
        t1 = time.time()
        if action in ["add", "update"]:
            while time.time() - t1 <= timeOut:
                if os.path.exists(cls.get_filename() + ".done"):
                    break
                time.sleep(1)
            while time.time() - t1 <= timeOut:
                updateTime = open(cls.get_filename() + ".done").read().strip()
                try:
                    updateTimeFloat = float(updateTime)
                except:
                    updateTimeFloat = 0.0
                if updateTimeFloat >= writeTime:
                    break
                time.sleep(1)

    def megre_dns_recode(self):
        WRITE_LOCK.acquire()
        try:
            dns_info = {}
            for line in open(self.get_filename()).read().strip().split('\n'):
                if line.strip() == "":
                    continue
                if line.count(" ") != 4:
                    self.logger.error(line)
                    continue
                writeTime, client_address, action, name, ip = line.split(' ')
                if not dns_info.has_key(client_address):
                    dns_info[client_address] = {}
                if not dns_info[client_address].has_key(name):
                    dns_info[client_address][name] = {}
                if action != "remove":
                    if action == "update":
                        dns_info[client_address][name] = {}
                    dns_info[client_address][name][ip] = writeTime
                elif dns_info[client_address][name].has_key(ip):
                    del dns_info[client_address][name][ip]
            data = []
            action = 'add'
            for client_address in dns_info:
                for name in dns_info[client_address]:
                    for ip in dns_info[client_address][name]:
                        data.append("%s %s %s %s %s" % (dns_info[client_address][name][ip], client_address, action, name, ip))
            data.sort()
            f = open(self.get_filename(), "w")
            f.write('\n'.join(data) + '\n')
            f.close()
            WRITE_LOCK.release()
            ret = True
        except:
            self.logger.error(traceback.format_exc())
            WRITE_LOCK.release()
            ret = False
        return ret

    def do_GET(self):
        '''处理GET请求'''
        if self.path.split('/')[-1].lower() == 'isrrvalid':
            code = 200
            detail = json.dumps({
                "resultCode": "000000",
                "transactionId": "",
                "resultMessage": "ok",
                "data": {"idValid":True}
            })
        elif self.path.split('/')[-1].lower() == 'merge':
            try:
                if self.megre_dns_recode():
                    code = 200
                    detail = "OK"
                else:
                    code = 500
                    detail = "ERROR"
            except:
                self.logger.error(traceback.format_exc())
                code = 500
                detail = "ERROR"
        else:
            code = 200
            detail = "OK"
            parm = {}
            try:
                for i in self.path.split('?')[1].lower().split("&"):
                    parm[i.split('=')[0]] = i.split('=')[1]
                if parm.has_key("action") and parm.has_key("name") and parm.has_key("ip"):
                    if '_' in parm["name"]:
                        self.logger.error("name非法: %s", parm["name"])
                        detail = "ERROR"
                    elif parm.has_key("source"):
                        self.write_action(parm["source"], parm["action"], parm["name"], parm["ip"])
                    else:
                        self.write_action(self.client_address[0], parm["action"], parm["name"], parm["ip"])
                else:
                    self.logger.error("缺少参数,当前参数为: %s", ",".join(parm.keys()))
                    detail = "ERROR"
            except:
                self.logger.error(traceback.format_exc())
                detail = "ERROR"
            if random.random() < 0.02:
                try:
                    self.megre_dns_recode()
                except:
                    self.logger.error(traceback.format_exc())
        self.write_data(code, detail, "text/html")

    def do_PUT(self):
        '''处理PUT请求'''
        code = 200
        detail = {
            "resultCode": "000000",
            "transactionId": "",
            "resultMessage": "ok"
        }
        try:
            method = self.path.split('/')[-1].lower()
            if method == 'isrrvalid':
                detail["data"] = {"idValid":True}
            else:
                if method == 'addrr':
                    method = 'add'
                elif method == 'delrr':
                    method = 'remove'
                else:
                    method = 'update'
                content = self.rfile.read(int(self.headers.getheader("Content-Length")))
                try:
                    parm = json.loads(content)
                except:
                    parm = None
                if not isinstance(parm, dict):
                    parm = {}
                    for i in content.lower().split("&"):
                        parm[i.split('=')[0]] = i.split('=')[1]
                if parm.has_key("transactionId"):
                    detail["transactionId"] = parm["transactionId"]
                if parm.has_key("zone") and parm.has_key("name") and parm.has_key("value"):
                    if "_" in parm["name"]:
                        self.logger.error("name非法: %s", parm["name"])
                        detail["resultCode"] = "000002"
                        detail["resultMessage"] = "error"
                    else:
                        if parm['zone'][-1] == '.':
                            parm['zone'] = parm['zone'][:-1]
                        if parm.has_key("source"):
                            self.write_action(parm["source"], method, "%s.%s" % (parm["name"], parm['zone']), parm["value"])
                        else:
                            self.write_action(self.client_address[0], method, "%s.%s" % (parm["name"], parm['zone']), parm["value"])
                else:
                    self.logger.error("缺少参数,当前参数为: %s", ",".join(parm.keys()))
                    detail["resultCode"] = "000001"
                    detail["resultMessage"] = "error"
        except:
            self.logger.error(traceback.format_exc())
            detail["resultCode"] = "000001"
            detail["resultMessage"] = "error"
        self.write_data(code, json.dumps(detail), "application/json")


def main():
    '''启动服务'''
    server_class = ThreadedHTTPServer
    server_address = ('', int(DNS_API_SERVER_PORT))
    ApiRequestHandler.set_filename(sys.argv[1])
    httpd = server_class(server_address, ApiRequestHandler)
    if HTTPS:
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./certificate.crt', keyfile='./privateKey.pem', server_side=True)
    os.system("touch dns_api_server_running")
    t = threading.Thread(target=httpd.serve_forever)
    t.start()
    while os.path.exists("dns_api_server_running"):
        try:
            time.sleep(1)
        except:
            print traceback.format_exc()
            break
    httpd.shutdown()
    t.join()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(-1)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
