#!/home/tops/bin/python
# -*- coding:utf-8 -*-
'''DNS刷新服务启动程序'''
import os
import sys
import time
import traceback
import json
import threading

def refreshDns(ip):
    '''刷新一个DNS服务器'''
    os.system("scp refreshDNS.py %s:~/" % ip)
    os.system("scp temp.dns %s:~/" % ip)
    os.system("ssh %s /home/tops/bin/python refreshDNS.py refreshDns temp.dns" % ip)

def refreshHttpsProxy():
    '''刷新https proxy'''
    httpsProxy = json.load(open("httpsProxyInfo"))
    for proxyname in httpsProxy.keys():
        for ip in httpsProxy[proxyname]:
            if os.system("ssh %s service nginx status > /dev/null" % ip) != 0:
                os.system("sh install_nginx.sh %s" % ip)
            filename = "https-proxy.%s.conf" % ip
            if os.path.exists(filename):
                os.system("scp %s %s:/home/admin/nginx/conf/extra/ > /dev/null" % (filename, ip))
                os.system("ssh %s service nginx reload > /dev/null" % ip)

def main():
    '''启动服务'''
    if len(sys.argv) > 1:
        iplist = sys.argv[1:]
    else:
        iplist = []
    for ip in iplist:
        os.system("scp refreshDNS.py %s:~/" % ip)
    t1 = time.time() - 30
    while True:
        time.sleep(0.1)
        try:
            os.system("scp mockdns.tbsite.net:/home/admin/privateDNS ./privateDNS > /dev/null")
            os.system("/home/tops/bin/python refreshDNS.py dumpdns temp.dns > /dev/null")
            if os.system("diff temp.dns temp.dns.bak  1>/dev/null 2>/dev/null") == 0 and  time.time() - t1 < 120:
                os.system("cat privateDNS|tail -1|awk {'print $1'} > privateDNS.done")
                os.system("scp privateDNS.done mockdns.tbsite.net:/home/admin/privateDNS.done")
                continue
            tlist = []
            tlist.append(threading.Thread(target=refreshHttpsProxy, args=()))
            for ip in iplist:
                tlist.append(threading.Thread(target=refreshDns, args=(ip,)))
            for t in tlist:
                t.start()
            for t in tlist:
                t.join()
            os.system("cat privateDNS|tail -1|awk {'print $1'} > privateDNS.done")
            os.system("scp privateDNS.done mockdns.tbsite.net:/home/admin/privateDNS.done")
            t1 = time.time()
            os.system("cp -f temp.dns temp.dns.bak")
        except:
            print traceback.format_exc()
            sys.exit(-2)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
