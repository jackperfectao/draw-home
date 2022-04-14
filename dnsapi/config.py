# -*- coding:utf-8 -*-
'''DNSAPI全局配置'''
#onebox
HTTPS = False
IP_BLOCK = "10.138.0.0/16"
IP_BLOCK_SKIP = "10.138.0.0/22"
NETMASK = "255.255.0.0"
GATEWAY = "10.138.255.247"
MOCK = False
DNS_WORKDIR = ONEBOX_WORKDIR + "/tools/refreshDNS"
DNS_API_SERVER_PORT = "80"
LOCAL_DNS_API_SERVER_PORT = "15000"
CERT_DIR = "cert/certificate4bootstrap/"



OPS1_CHECK_LIST = {
    "local_dns_api_server": {\
        "start": "nohup /home/tops/bin/python local_dns_api_server.py > local_dns_api_server.out 2>&1 &",\
        "check": "curl -s 127.0.0.1:%s/ 1>/dev/null" % LOCAL_DNS_API_SERVER_PORT,\
        "stop": "ps axu|grep local_dns_api_server.py|grep -v grep|awk {'print $2'}|xargs -n 1 kill"},
    "dns_refresh": {\
        "start": "nohup /home/tops/bin/python tools/refreshDNS/run.py DNS1 DNS2 1> dns_run.out 2>&1 &",\
        "check": "ps axu|grep -v grep|grep run.py|grep DNS1|grep DNS2 1>/dev/null 2>/dev/null",\
        "stop": "ps axu|grep -v grep|grep run.py|grep DNS1|grep DNS2|awk {'print $2'}|xargs -n 1 kill"}
}

VMSERVER_CHECK_LIST = {
    "vm_server": {\
        "start": "nohup /home/tops/bin/python vmServer.py > vmServer.out 2>&1 &",\
        "check": "ps axu|grep -v grep|egrep vmServer.py$ 1>/dev/null 2>/dev/null",\
        "stop": "rm -f vm_server_running;/home/tops/bin/python tools/wait.py 0 \"ps axu|grep vmServer|grep -v grep|wc -l\" 1>/dev/null 2>/dev/null"}
    }



#HA_TEST
HA_TEST_DIR = "/apsarapangu/disk3/ha_test/"
