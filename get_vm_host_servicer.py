#!/home/tops/bin/python
#coding:utf-8
# the tools is just adjust for shuguang  .
import os
import sys
import json

ops1ip="10.36.254.1"
cloudId="环境61014"
regionId="cn-hangzhou-env6-d01"
azoneId="cn-hangzhou-env6-ew9001-a"


def get_vm_host_service():

    cmd_tianji="ssh %s  'cd /apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/ && /home/tops/bin/python /apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/zhuque_tianji_util.py   /cloud/data/bootstrap_controller/BootstrapController#/bootstrap_controller/tianji_dest.conf %s' " % (ops1ip,azoneId)
    print cmd_tianji
    os.system(cmd_tianji)
    scp_cmd="scp %s:/apsarapangu/disk9/tmp/chengfei.zcf/upgrade_tool/tools/zhuque_tools/zhuque2tj.json  /tmp/zhuque2tj.json" % (ops1ip)
    print os.system(scp_cmd)

    cmd_post="curl http://zhuque.alibaba-inc.com/postFinalPlanOutputJsonFile?cloudId=%s&regionId=%s&azoneId=%s  -XPOST --data @/tmp/zhuque2tj.json" % (cloudId,regionId,azoneId)
    os.system(cmd_post)

    cmd_getline="curl 'http://zhuque.alibaba-inc.com/getFinalPlanLinesCsv?cloudId=%s&regionId=%s&azoneId=%s'  > /tmp/1PlanLinesCsv" % (cloudId,regionId,azoneId)
    os.system(cmd_getline)
    cmd_gethost="curl 'http://zhuque.alibaba-inc.com/getFinalPlanHostListCsv?cloudId=%s&regionId=%s&azoneId=%s'  > /tmp/2HostListCsv" % (cloudId,regionId,azoneId)
    os.system(cmd_gethost)
get_vm_host_service()