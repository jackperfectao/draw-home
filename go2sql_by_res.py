#!/home/tops/bin/python
#coding:utf-8

import json
import sys
import collections
import os
import requests

def get_db_msg_by_id():
    resid=sys.argv[1]
    a=requests.get("http://127.0.0.1:7070/api/v3/column/service.res.*?service.res.id=%s" % (resid))
    b = a.json()[0]["service.res.result"]
    c = json.loads(b)
    db_name=c["dbName"]
    db_user=c["db_user"]
    db_port=c["db_port"]
    db_passwd=c["passwd"]
    db_host=c["db_host"]
    db_instance=c["instance_name"]
    cmd="mysql -h%s -u%s -P%s -p%s %s" % (db_host,db_user,db_port,db_passwd,db_name)
    os.system(cmd)
get_db_msg_by_id()