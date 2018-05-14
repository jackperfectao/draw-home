#!/home/tops/bin/python
#coding=utf-8

import requests, json
import time
import subprocess


def notify(content):
    try:
        #nomal 
        url = "https://oapi.dingtalk.com/robot/send?access_token=599182e0be68d9617248b933c9e0113dc0d336ec4cc4a680cd5450e2935ae7eb"
        #test
        #url = "https://oapi.dingtalk.com/robot/send?access_token=acb9c4f596813a1ac2b86b998c23a7bc3134ffc044be9570e570897172536a01"
        msg = {}
        msg["msgtype"] = "text"
        msg["text"] = {"content": content}
        msg["at"] = {"atMobiles": ["17681809799"], "isAtAll": False}
        headers = {'content-type': 'application/json'}
        requests.post(url, data=json.dumps(msg), headers=headers)
    except Exception as e:
        print "Error, e = %s" % repr(e)

def exec_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout,stderr = p.communicate()
    if p.returncode:
        raise Exception("exec cmd[%s] failed, stdout[%s], stderr[%s]" % (cmd, stdout, stderr))
    return (p.returncode, stdout, stderr)


def pretty(message):
    import pdb
    #pdb.set_trace()
    import json
    header = u"【8B环境克隆失败kvm】\n"
    ret = header
    content = {}
    # 分类结果信息
    for m in message:
        key = m[1] # clonescript
        value = m[0] # hostname
        if content.has_key(key):
            content[key].append(value)
        else:
            content[key] = [value] # 初始化list
    
    # 换行输出
    for key, values in content.iteritems():
        ret += u"【" + key + u"】"+ u"："
        for value in values:
            ret += value
            if values[len(values) - 1] != value:
                ret += u"，"
            else:
                ret += "\n"
    return ret

def task_status_overtime():
    import pdb
    #pdb.set_trace()
    cmd = "ssh -p 50102 root@100.67.76.9 'curl -s http://ks.kvmclone.net/clonetask/notdone' "
    _, r, _ = exec_cmd(cmd)
    scmd = "ssh -p 50102 root@100.67.76.9 'ssh ks.kvmclone.net 'ls  /root/clone/download/clonescripts'' "
    _, sr, _ = exec_cmd(scmd)
    onesr = sr.split()
    all_list = []
    data = json.loads(r)
    for ng in data:
        notgood = {}
        notgood["hostname"] = ng["hostname"]
        notgood["starttime"] = ng["start_time"]
        notgood["clonescript"] = ng["clonescript"]
        nowtime = time.time()
        time_start = time.mktime(time.strptime(notgood["starttime"],'%Y-%m-%d %H:%M:%S'))
        time_interval = (nowtime - time_start)
        if int(time_interval) > 4600:
            if sr.find(notgood["clonescript"]):
                all_list.append([ng["hostname"], ng["clonescript"]])
            else:
                print "8B don't support %s clone scripts" % notgood["clonescript"]
    print "8B: hostlist %s not OK" %  all_list
    #notify("8B: hostname = %s not OK" % all_list)
    notify(pretty(all_list))

if __name__ == '__main__':
    print "========================="
    while True:
        try:
            task_status_overtime()
            time.sleep(7200)
        except Exception as exp:
            print exp
            time.sleep(7200)
            pass



