#!/home/tops/bin/python
# -*- coding:utf-8 -*-
'''获取产品的DNS信息并更新到DNS和HttpsProxy服务器'''
import os
import sys
import json
import random
import copy
import traceback
import threading
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
    from ipServer import ipBlocktoIpList
except:
    pass

PROXY_CONF = '''
    server {
        listen              80;
        server_name         %s;
        rewrite ^/(.*) https://%s/$1 permanent;
    }

    server {
        listen 443 ssl;
        server_name %s;
        ssl_certificate     /home/admin/cert/certificate.crt;
        ssl_certificate_key /home/admin/cert/privateKey.pem;
        default_type "text/html";
 
        location / {
            proxy_pass   http://%s;
            proxy_read_timeout     300;
            proxy_send_timeout 90;
            proxy_connect_timeout  300;
        }
 
    }
'''
BASE_ISOLATE_POP_DNS = [
    {
        "ip": [
            "10.38.95.216"
        ],
        "domain": "ft.aliyun.com",
        "vip": "10.38.95.216",
        "https_proxy": False
    },
    {
        "ip": [
            "10.38.95.216"
        ],
        "domain": "acs.aliyun.com",
        "vip": "10.38.95.216",
        "https_proxy": False
    }
]

def isip(ip):
    '''判断是否是IP'''
    ip = str(ip)
    sec = ip.split('.')
    if len(sec) != 4:
        return False
    for i in sec:
        if not i.isdigit():
            return False
    return True

def getClusterDns():
    '''获取DNS信息'''
    dns = {}
    temp = json.load(os.popen("curl 'localhost:7070/api/v5/BatchGetServiceResInfo?service=resmgr&type=dns' 2>/dev/null"))
    for i in temp['data']:
        if (not i.has_key('cluster')) or (not i.has_key('result')):
            print "DNS format error"
            print json.dumps(i, indent=2)
            continue
        cluster = i['cluster']
        result = json.loads(i['result'])
        https_proxy = False
        vip = None
        if i.has_key("parameters"):
            try:
                parameters = json.loads(i['parameters'])
                if parameters.has_key("noop") and str(parameters["noop"]).lower() == "true":
                    continue
                if parameters.has_key("https_proxy") and str(parameters["https_proxy"]).lower() == "true":
                    https_proxy = True
                if parameters.has_key("vip"):
                    vip = parameters["vip"]
            except:
                print json.dumps(i, indent=2)
                continue
        ip = json.loads(result['ip'])
        if vip is None:
            vip = ip[0]
        domain = result['domain']
        if not dns.has_key(cluster):
            dns[cluster] = []
        dns[cluster].append({"domain":domain, "ip":ip, "https_proxy":https_proxy, "vip":vip})
    return dns

def getProjectMachine():
    '''获取产品机器列表'''
    machine = {}
    temp = json.load(os.popen("curl 'localhost:7070/api/v5/BatchGetMachineInfo' 2>/dev/null"))
    for i in temp['data']:
        if (not i.has_key('cluster')) or (not i.has_key('project')) or (not i.has_key('ip')):
            print "MachineInfo format error"
            print json.dumps(i, indent=2)
            continue
        project = i['project']
        cluster = i['cluster']
        ip = i['ip']
        if not machine.has_key(project):
            machine[project] = {'cluster':[], 'ip':[]}
        if not cluster in machine[project]['cluster']:
            machine[project]['cluster'].append(cluster)
        machine[project]['ip'].append(ip)
    return machine

class EditDnsConf(object):
    '''编辑DNS配置文件'''
    def __init__(self, tempdir):
        os.system("mkdir -p %s" % tempdir)
        os.system("cp /var/named/* %s  1>/dev/null 2>/dev/null" % tempdir)
        os.system("rm -rf %s" % os.path.join(tempdir, '*.jnl'))
        self.tempdir = tempdir
        self.zonelist = {}
    def edit(self, domain, ip, dnstype='A'):
        '''修改一条记录'''
        illegalChar = '_!?/\\;:@#$%&^~=+,<>(){}|"\'`'
        for i in illegalChar:
            if i in domain:
                print "[IllegalChar] %s" % domain
                return
        if dnstype == 'A':
            for i in ip:
                if not isip(i):
                    print "[IllegalIp] %s %s" % (domain, i)
                    return
        domainSplit = domain.split('.')
        for i in domainSplit:
            if i:
                if i[0] == '-' or i[-1] == '-':
                    print "[IllegalDomain] %s" % domain
                    return
        for i in xrange(1, len(domainSplit) - 1):
            zone = '.'.join(domainSplit[i:])
            if self.zonelist.has_key(zone) or os.path.exists(os.path.join(self.tempdir, zone)):
                if not self.zonelist.has_key(zone):
                    self.zonelist[zone] = open(os.path.join(self.tempdir, zone)).read().strip().split('\n')
                j = 0
                origin = ''
                while j < len(self.zonelist[zone]):
                    line = self.zonelist[zone][j].split()
                    if self.zonelist[zone][j] == '' or self.zonelist[zone][j][0].strip() == '':
                        pass
                    elif line[0] == '':
                        pass
                    elif line[0] == '$ORIGIN':
                        origin = line[1]
                        if origin[-1] == '.':
                            origin = origin[:-1]
                    elif line[0] == '$TTL':
                        pass
                    else:
                        if "%s.%s" % (line[0], origin) == domain:
                            del self.zonelist[zone][j]
                            while j < len(self.zonelist[zone]) and (self.zonelist[zone][j] == '' or self.zonelist[zone][j][0].strip() == ''):
                                del self.zonelist[zone][j]
                            j = j - 1
                    j = j + 1
                record = '%s.' % domain
                for j in ip:
                    record = record + '\t\t\t%s\t%s\n' % (dnstype, j)
                self.zonelist[zone].append(record.strip())
                break
        if domainSplit[0] != '*' and dnstype == 'A':
            for i in ip:
                zone = "%s.rev" % i.split('.')[0]
                if self.zonelist.has_key(zone) or os.path.exists(os.path.join(self.tempdir, zone)):
                    if not self.zonelist.has_key(zone):
                        self.zonelist[zone] = open(os.path.join(self.tempdir, zone)).read().strip().split('\n')
                    ip3 = i.split('.')[1:]
                    ip3.reverse()
                    record = '%s\tPTR\t%s.' % ('.'.join(ip3), domain)
                    self.zonelist[zone].append(record.strip())
    def save(self):
        '''保存修改'''
        for zone in self.zonelist:
            f = open(os.path.join(self.tempdir, zone), 'w+')
            f.write('\n'.join(self.zonelist[zone]) + '\n')
            f.close()

def assignHttpsProxy(result, httpsProxy):
    '''选取HttpsProxy服务器'''
    usedhostname = {}
    proxyinfo = {}
    for proxyname in httpsProxy.keys():
        result[proxyname] = {'dns':[], 'cluster':[], 'ip':httpsProxy[proxyname]}
        usedhostname[proxyname] = []
        proxyinfo[proxyname] = []
    for project in result.keys():
        for i in xrange(0, len(result[project]['dns'])):
            dns = result[project]['dns'][i]
            if dns.has_key("https_proxy") and dns["https_proxy"]:
                for proxyname in httpsProxy.keys():
                    if dns["domain"] not in usedhostname[proxyname]:
                        usedhostname[proxyname].append(dns["domain"])
                        proxyinfo[proxyname].append({"domain": dns["domain"], 'ip':[dns['vip']]})
                        result[proxyname]['dns'].append({"domain": dns["domain"], 'ip':httpsProxy[proxyname]})
                        result[project]['dns'][i]['ip'] = httpsProxy[proxyname]
                        break
    return proxyinfo

def dumpProxyInfo(proxyinfo, httpsProxy):
    '''存放HttpsProxy配置'''
    for proxyname in proxyinfo.keys():
        conf = ""
        for dns in proxyinfo[proxyname]:
            conf = conf + (PROXY_CONF % (dns["domain"], dns["domain"], dns["domain"], dns["ip"][0]))
        for ip in httpsProxy[proxyname]:
            f = open("https-proxy.%s.conf" % ip, "w+")
            f.write(conf)
            f.close()

def editProjectDns(project, result):
    '''编辑project的dns信息'''
    tempfile = "/var/named/tmp/oneboxdns/" + "".join(random.sample('1234567890abcdefghijklmnopqrstuvwxyz', 7))
    try:
        dnsConfig = EditDnsConf(tempfile)
        for dns in result[project]['dns']:
            if dns.has_key('type'):
                dnsConfig.edit(dns['domain'], dns['ip'], dns['type'])
            else:
                dnsConfig.edit(dns['domain'], dns['ip'])
        dnsConfig.save()
    except:
        pass
    os.system("rm -rf /var/named/%s" % project)
    os.system("mv %s /var/named/%s" % (tempfile, project))
    os.system("chown named:named -R /var/named/%s 1>/dev/null 2>/dev/null" % project)

def main():
    '''开始'''
    if sys.argv[1] == 'dumpdns':
        data = getProjectMachine()
        result = {}
        dns = getClusterDns()
        iptoproject = {}
        if os.path.exists("blacklist"):
            blacklist = open("blacklist").read().strip().split('\n')
        else:
            blacklist = []
        for project in data:
            if not project.split('-')[-1].isdigit():
                continue
            if len(data[project]['cluster']) == 1 and data[project]['cluster'][0] == 'default':
                continue
            if not data[project].has_key('dns'):
                data[project]['dns'] = []
            hasPop = False
            for cluster in data[project]['cluster']:
                if cluster.startswith("BasicCluster-webapp-pop") or project.startswith("webapp-pop"):
                    hasPop = True
                if cluster in blacklist:
                    continue
                if dns.has_key(cluster):
                    data[project]['dns'].extend(dns[cluster])
            if not hasPop:
                data[project]['dns'].extend(BASE_ISOLATE_POP_DNS)
            for filename in os.popen("ls %s.*.iplist 2>/dev/null" % project).read().strip().split('\n'):
                if filename.strip() == "":
                    continue
                iplist = json.load(open(filename))
                for ip in iplist:
                    if not ip in data[project]['ip']:
                        data[project]['ip'].append(ip)
                for ip in data[project]['ip']:
                    if "/" in ip:
                        for mip in ipBlocktoIpList(ip):
                            iptoproject[mip] = project
                    else:
                        iptoproject[ip] = project
            if data[project]['ip']:
                result[project] = data[project]
        httpsProxy = json.load(open("httpsProxyInfo"))
        proxyinfo = assignHttpsProxy(result, httpsProxy)
        json.dump({"Utility": str(max([len(proxyinfo[x]) for x in proxyinfo]) * 100 / 1024) + "%", "Time Stamp": os.popen("date").read().strip()}, open("httpsProxyStatus.json", "w+"), indent=2)
        dumpProxyInfo(proxyinfo, httpsProxy)
        if os.path.exists("privateDNS"):
            for line in open("privateDNS").read().strip().split('\n'):
                cols = line.replace("\xc2\xa0", "").strip().split()
                if not cols:
                    continue
                if float(cols[0]) < 1.0:
                    continue
                if len(cols) > 4 and cols[1] == "127.0.0.1":
                    cols[1] = cols[4]
                if len(cols) != 5:
                    continue
                if cols[1] == "all":
                    projectlist = result.keys()
                elif iptoproject.has_key(cols[1]):
                    projectlist = [iptoproject[cols[1]]]
                else:
                    projectlist = [cols[1]]
                for project in projectlist:
                    if not result.has_key(project):
                        continue
                    method = cols[2]
                    name = cols[3]
                    ip = cols[4]
                    if not isip(ip):
                        if ip[-1] != '.':
                            ip = ip + '.'
                            if method == 'add':
                                method = 'update'
                    pl = [project]
                    for p in pl:
                        f = False
                        for i in xrange(0, len(result[p]['dns'])):
                            if result[p]['dns'][i]["domain"] == name:
                                f = True
                                if method == 'add':
                                    if ip not in result[p]['dns'][i]["ip"]:
                                        result[p]['dns'][i]["ip"].append(ip)
                                elif method == 'update':
                                    result[p]['dns'][i]["ip"] = [ip]
                                    if not isip(ip):
                                        result[p]['dns'][i]["type"] = 'CNAME'
                                elif method == 'remove':
                                    while ip in result[p]['dns'][i]["ip"]:
                                        result[p]['dns'][i]["ip"].remove(ip)
                                    if not result[p]['dns'][i]["ip"]:
                                        del result[p]['dns'][i]
                                break
                        if (method == 'add' or method == 'update') and not f:
                            if isip(ip):
                                result[p]['dns'].append({"domain":name, "ip":[ip]})
                            else:
                                result[p]['dns'].append({"domain":name, "ip":[ip], "type":'CNAME'})
        if os.path.exists("project_group"):
            try:
                projectDomain = {}
                for project in result:
                    projectDomain[project] = []
                    for dns in result[project]["dns"]:
                        projectDomain[project].append(dns["domain"])
                project_group = json.load(open("project_group"))
                result_bak = copy.deepcopy(result)
                for group in project_group:
                    for projectA in group:
                        if result.has_key(projectA):
                            for projectB in group:
                                if projectA == projectB or not result.has_key(projectB):
                                    continue
                                for dns in result_bak[projectB]["dns"]:
                                    domain = dns["domain"]
                                    if domain not in projectDomain[projectA]:
                                        result[projectA]["dns"].append(dns)
            except:
                print traceback.format_exc()
        result["default"] = {
            "cluster": [],
            "dns": BASE_ISOLATE_POP_DNS,
            "ip": [
                "10.38.144.0/26",
                "10.38.160.0/26",
                "10.38.176.0/26",
                "10.138.0.0/23",
                "10.138.64.0/23",
                "10.138.128.0/23"
                ],
        }
        json.dump(result, open(sys.argv[2], 'w+'), indent=2)
    elif sys.argv[1] == 'refreshDns':
        result = json.load(open(sys.argv[2]))
        os.system("rndc freeze")
        if os.system("cat /etc/named.conf|grep onebox_named.conf") != 0:
            tempfile = open("/etc/named.conf").read().strip().split('\n')
            for i in xrange(0, len(tempfile)):
                if tempfile[i].strip() == "":
                    continue
                if tempfile[i].split()[0] == "zone":
                    tempfile[i] = "include \"/var/named/onebox_named.conf\";\nview \"all_view\" {\nmatch-clients {\n    any;\n};\n" + tempfile[i]
                    break
            f = open("/etc/named.conf", "w+")
            f.write("\n".join(tempfile) + "\n};")
            f.close()
        os.system("rm -rf /var/named/onebox_*.conf;touch /var/named/onebox_named.conf")
        os.system("chown named:named /var/named/onebox_named.conf 1>/dev/null 2>/dev/null")
        if not os.path.exists("/var/named/onebox_conf"):
            os.system("mkdir /var/named/onebox_conf")
            os.system("chown named:named /var/named/onebox_conf 1>/dev/null 2>/dev/null")
        tlist = []
        for project in result.keys():
            if os.system("cat /var/named/onebox_named.conf|grep onebox_%s.conf" % project) != 0:
                os.system(r'echo include \"/var/named/onebox_conf/onebox_%s.conf\"\; >> /var/named/onebox_named.conf' % project)
                tempfile = open("/etc/named.conf").read().strip().split('\n')
                content = "acl %s {\n" % project
                for ip in result[project]["ip"]:
                    content = content + "    %s;\n" %ip
                content = content + "};\nview \"%s_view\" {\nmatch-clients {\n    %s;\n};\n" % (project, project)
                for i in xrange(0, len(tempfile)):
                    if tempfile[i].strip() == "":
                        continue
                    if tempfile[i].split()[0] == "zone":
                        if tempfile[i].split()[1] == '"."':
                            content = content + tempfile[i] + "\n    type hint;\n"
                        else:
                            content = content + tempfile[i] + "\n    type master;\n"
                    elif tempfile[i].split()[0] == "file":
                        content = content + "    file \"/var/named/%s/%s\n};\n" % (project, tempfile[i].split()[1][1:])
                content = content + "};\n"
                f = open("/var/named/onebox_conf/onebox_%s.conf" % project, "w+")
                f.write(content)
                f.close()
                os.system("chown named:named /var/named/onebox_conf/onebox_%s.conf 1>/dev/null 2>/dev/null" % project)
            t = threading.Thread(target=editProjectDns, args=(project, result))
            t.start()
            tlist.append(t)
        for t in tlist:
            t.join()
        os.system("rndc reload")
        os.system("rndc thaw")
        os.system("rndc flush")

if __name__ == "__main__":
    main()
