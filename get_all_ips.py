#!/home/tops/bin/python
#coding=utf-8
import json
import subprocess
import requests

def exec_cmd(cmd):
# print "[exec_cmd], cmd = %s" % cmd
    p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode:
        raise Exception, "exec cmd[%s] failed, stdout[%s], stderr[%s]" % (cmd, stdout, stderr)
    return (p.returncode, stdout, stderr)

def generate_tj_json():
    cmd = "cd /apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/ && /home/tops/bin/python /apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/zhuque_tianji_util.py   /cloud/data/bootstrap_controller/BootstrapController#/bootstrap_controller/tianji_dest.conf"
    exec_cmd(cmd)

def process_docker():
    print "正在出终态，请稍等，大约耗时5分钟..."
# generate_tj_json()
    result = []
    with open("/apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/zhuque2tj.json") as f:
        data = json.load(f)
        product = data["productList"]
        for p in product:
            pname = p["productName"]
            cluster = p["clusterList"]
            for c in cluster:
                service = c["serverRoleGroupList"]
                for s in service:
                    servicerole = s["serverRoleList"]
                    for sr in servicerole:
                        service_name = sr["serviceName"]
                        serverrole_name = sr["serverRoleName"]
                        if sr.has_key("userContainerInfo"):
                            container = sr["userContainerInfo"]
                            for con in container:
                                ret = {}
                                ret["product"] = pname
                                ret["ip"] = con["userContainerIp"]
                                ret["service"] = service_name
                                ret["serverrole"] = serverrole_name
                                result.append(ret)
    return result


def process_vm_nc():
    r = requests.get("http://127.0.0.1:7070/api/v3/column/m.ip,m.project,m.machine_type_with_nic_type")
    data = r.json()
    result = []
    for d in data:
        try:
            cmd = "ssh %s ls /cloud/app" % d["m.ip"]
            _, stdout, _ = exec_cmd(cmd)
            services = stdout.split("\n")
            for s in services:
                s = s.strip()
                if s != "":
                    cmd = "ssh %s ls /cloud/app/%s" % (d["m.ip"], s)
                    _, out, _ = exec_cmd(cmd)
                    serverroles = out.split("\n")

                    for sr in serverroles:
                        sr = sr.strip()
                        if sr != "":
                            if d["m.machine_type_with_nic_type"] == "VM":
                                mtype = "vm"
                            else:
                                mtype = "nc"
                            product = {}
                            product["product"] = d["m.project"]
                            product["service"] = s
                            product["serverrole"] = sr
                            product["ip"] = d["m.ip"]
                            product["mtype"] = mtype
                            print result
                            result.append(product)
        except Exception as e:
            print repr(e)
        break
    return result

if __name__ == '__main__':
    docker_ret = process_docker()
    vm_nc_ret = process_vm_nc()
    result = docker_ret + vm_nc_ret
    with open("result.json", "a+") as f:
        f.write(json.dumps(result))

    print "查询完成，结果在result.json"