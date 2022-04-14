#!/home/tops/bin/python
# -*- coding:utf-8 -*-
'''OneboxAPI 提供给CICD'''
import BaseHTTPServer
import json
import os
import threading
import ssl
import time
import datetime
import traceback
from config import *
from oneboxApiRequestHandler import OneboxApiRequestHandler

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

def printlog(info, level="INFO"):
    '''输出日志'''
    logfile = "log/api_server_log"
    if isinstance(info, (str, unicode)):
        info = [info]
    for i in xrange(0, len(info)):
        if isinstance(info[i], unicode):
            info[i] = info[i].encode('utf-8')
        if isinstance(info[i], str):
            info[i] = str(info[i])
    f = open(logfile, 'a+')
    f.write("[%s][%s]%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level, ' '.join(info)))
    f.close()

class ApiRequestHandler(OneboxApiRequestHandler):
    '''RequestHandler'''
    def do_GET(self):
        '''处理GET请求'''
        printlog(self.path)
        method, parm = self.get_method_and_parm(self.path)
        if method == "checkhealth":
            if os.path.exists("standard_api_server_running"):
                httpStatusCode = 200
                message = "successful"
                code = 0
            else:
                httpStatusCode = 503
                message = "Service Unavailable"
                code = "onebox.10000.1.service_unavailable"
            detail = {
                "httpStatusCode": httpStatusCode,
                "code": code,
                "message": message,
                "traceId": "",
                "resultData": {
                    "url" : self.path,
                    "client": self.client_address[0]
                }
            }
            if parm.has_key("traceId"):
                detail["traceId"] = parm["traceId"]
        else:
            httpStatusCode = 405
            detail = {
                "httpStatusCode": httpStatusCode,
                "code": "onebox.21405.0.unknow_method",
                "message": "Method Not Allowed",
                "traceId": "",
                "resultData": {
                    "url" : self.path,
                    "client": self.client_address[0]
                }
            }
            if parm.has_key("traceId"):
                detail["traceId"] = parm["traceId"]
        self.write_data(httpStatusCode, json.dumps(detail), "application/json")

    def do_PUT(self):
        '''处理PUT请求'''
        method, parm = self.get_method_and_parm(self.path)
        printlog(self.path)
        httpStatusCode = 200
        message = ""
        traceId = ""
        resultData = {
            "url": self.path,
            "client": self.client_address[0]
        }
        step = None
        status = None
        try:
            printlog(self.headers.getheader("Content-Length"))
            content = self.rfile.read(int(self.headers.getheader("Content-Length")))
            printlog(json.dumps(content))
            data = json.loads(content)
            for key in parm:
                data[key] = parm[key]
            resultData['postData'] = data
            if not data.has_key('traceId'):
                httpStatusCode = 400
                message = "Required traceId"
                printlog(message)
            else:
                traceId = data['traceId']
                action = data['action'] if data.has_key('action') else 'start'
                if action not in ['start', 'check']:
                    httpStatusCode = 400
                    message = "Not support action=%s" % action
                    printlog(message)
                elif not data.has_key('artifact'):
                    httpStatusCode = 400
                    message = "Required artifact"
                    printlog(message)
                else:
                    if not data.has_key('fastwork_id'):
                        data['fastwork_id'] = str(int('0x' + data['traceId'].replace('-', ''), 16))
                    resultData['projectName'] = "%s-%s" % (data['artifact'], data['fastwork_id'])
        except:
            printlog(traceback.format_exc())
            httpStatusCode = 400
            message = "Content must be json"
            printlog(message)
        if httpStatusCode == 200:
            workdir = SUPERAG_API_SERVER_WORK_DIR
            mock_workdir = SUPERAG_API_SERVER_MOCK_WORK_DIR
            if action == 'start':
                if method == "deployone":
                    step = "DeployOnebox"
                elif method == "starttest":
                    if data.has_key('step'):
                        step = "test" + data['step']
                    else:
                        httpStatusCode = 400
                        message = "Required step"
                        printlog(message)
                elif method == "clearonebox":
                    step = "ClearOnebox"
                else:
                    httpStatusCode = 405
                    message = "Method Not Allowed"
                    printlog(message)
                if step != None:
                    if data.has_key("Mock") and data["Mock"]:
                        workfile = os.path.join(mock_workdir, "%s-%s.%s" % (data['artifact'], data['fastwork_id'], step))
                        try:
                            json.dump(data, open(workfile, "w+"))
                            output = os.popen("/home/tops/bin/python onebox31.py mockdeploy %s" % workfile).read().strip().split("\n")
                            for i in xrange(1, len(output)):
                                if output[i] == "####ONEBOX PRINT RESULT####":
                                    resultData["ZhuqueFile"] = json.load(open(output[i - 1]))
                                    break
                            if not resultData.has_key("ZhuqueFile"):
                                httpStatusCode = 500
                                message = "ERROR"
                        except:
                            httpStatusCode = 500
                            message = "ERROR"
                            printlog(traceback.format_exc())
                    else:
                        workfile = os.path.join(workdir, "%s-%s.%s" % (data['artifact'], data['fastwork_id'], step))
                        traceIdfile = os.path.join(workdir, traceId)
                        if os.path.exists(workfile) or os.path.exists(workfile + ".done"):
                            httpStatusCode = 200
                            message = "Already Submitted"
                            printlog(message)
                        elif method == "starttest" and os.system("ls " + os.path.join(workdir, "%s-%s.*" % (data['artifact'], data['fastwork_id']))) == 0:
                            httpStatusCode = 401
                            message = "Test Conflict"
                            printlog(message)
                        else:
                            json.dump({"status":"waiting", "info":""}, open(traceIdfile, "w+"))
                            json.dump(data, open(workfile, "w+"))
                            httpStatusCode = 200
                            message = "Success"
                            printlog(message)
            else:
                traceIdfile = os.path.join(workdir, traceId)
                if os.path.exists(traceIdfile):
                    result = json.load(open(traceIdfile))
                    status = result["status"]
                    resultData['info'] = result['info']
                    httpStatusCode = 200
                    message = "Success"
                    printlog(message)
                else:
                    status = 'notfound'
                    httpStatusCode = 404
                    message = "Not Found"
                    printlog(message)
        detail = {
            "httpStatusCode": httpStatusCode,
            "code": 0,
            "message": message,
            "traceId": traceId,
            "resultData": resultData
        }
        if httpStatusCode != 200:
            detail["code"] = "onebox.%d.1.http_error" % (21000 + httpStatusCode)
        elif detail["resultData"].has_key('info'):
            if "requestZhuque30Release error" in detail["resultData"]['info'] or "requestZhuque30Release  error" in detail["resultData"]['info']:
                detail["code"] = "onebox.22001.1.zhuque_error"
            elif "Not enough docker resources." in detail["resultData"]['info']:
                detail["code"] = "onebox.22002.1.not_enough_docker_resources"
            elif "Machine not enough." in detail["resultData"]['info']:
                detail["code"] = "onebox.22003.1.not_enough_machine"
            elif "KVM not support os template" in detail["resultData"]['info']:
                detail["code"] = "onebox.22004.0.kvm_not_support_os_template"
            elif "KVM not support machine type" in detail["resultData"]['info']:
                detail["code"] = "onebox.22004.0.kvm_not_support_machine_type"
            elif detail["resultData"]['info'] != "":
                detail["code"] = "onebox.22005.2.unknow_error"
        if status != None:
            detail['status'] = status
        self.write_data(httpStatusCode, json.dumps(detail), "application/json")

def main():
    '''启动服务'''
    server_class = BaseHTTPServer.HTTPServer
    server_address = ('', int(STANDARD_API_SERVER_PORT))
    httpd = server_class(server_address, ApiRequestHandler)
    os.system("touch standard_api_server_running")
    if HTTPS:
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./certificate.crt', keyfile='./privateKey.pem', server_side=True)
    t = threading.Thread(target=httpd.serve_forever)
    t.start()
    while os.path.exists("standard_api_server_running"):
        try:
            time.sleep(1)
        except:
            break
    httpd.shutdown()
    t.join()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
