# -*- coding: utf-8 -*-
#!/home/tops/bin/python
#****************************************************************#
# ScriptName: merge.py
# Author: 
# Create Date: 2016-03-31 17:20
# Modify Author: $SHTERM_REAL_USER@alibaba-inc.com
# Modify Date: 2016-06-03 09:48
# Function: 
#***************************************************************#

import os
import sys
import requests
import json
import time
import commands
import traceback
import threading
import thread
from libs import log
from optparse import OptionParser

reload(sys)
sys.setdefaultencoding('utf-8')

def GetOption():
    usage = ''' 
            %prog [options] args
    '''
    parser = OptionParser(usage)
    parser.add_option("-i", "--ip", action = "store", type = "string", dest = "ip",
            help = "ip for docker registry")
    parser.add_option("-n", "--dir", action = "store", type = "string", dest = "dir",
            help = "docker image and tianji service package dir")
    parser.add_option("--skip_packages", action = "store_true", dest = "skip_packages",
            help = "skip tianji service package")
    parser.add_option("--skip_images", action = "store_true", dest = "skip_images",
            help = "skip docker images")
    parser.add_option("-p", "--product", action = "store", type= "string", dest = "product",
            help = "product name")
    return parser

def get_required_ip():
    path = "/cloud/app/tianji-tools/PrivateCloudTool#/tianji_ops_tool/current/conf.global/self/role.json"
    with open(path, 'r') as fd:
        info = json.load(fd) 
    ip_str = info["ServerRoles"]["PrivateCloudTool#"][0]
    ip = ip_str.split(":")[1]
    return ip

def merge(dir, ip = None, product = None, skip_packages = False, skip_images = False):
    #get image list and package list
    images, packages = get_images_packages(dir, product)
    if ip is None:
        ip = get_required_ip()

    #import image
    if not skip_images:
        ret = import_images(images, dir, ip)
        if ret != 0:
            raise Exception, "import image fail"

    #import tianji service package
    if not skip_packages:
        ret = import_tj_packages(dir, packages)
        if ret != 0:
            raise Exception, "import tianji service package fail"

def get_images_packages(dir, product):
    new_version = True
    image_info_file = os.path.join(dir, "_docker_image", "image_info")
    package_info_file = os.path.join(dir, "_tianji_repository", "package_info")
    if (not os.path.isfile(image_info_file)) or (not os.path.isfile(package_info_file)):
        new_version = False

    #raise exception if old version, and product is not none
    if product is not None:
        if not new_version:
            raise Exception, "Get %s images and packages fail!" % product

    #all products
    if new_version:
        image_info = os.path.join(dir, "_docker_image", "image_info")
        images = read_images_from_json(image_info, product)
        package_info = os.path.join(dir, "_tianji_repository", "package_info")
        packages = read_packages_from_json(package_info, product)
    else:
        image_file = os.path.join(dir, "_docker_image", "image_list")
        images = read_image_file(image_file)
        package_file = os.path.join(dir, "_tianji_repository", "package_list")
        packages = read_package_file(package_file)
    return images, packages

def read_images_from_json(image_info, product):
    return read_from_json(image_info, product)

def read_packages_from_json(package_info, product):
    return read_from_json(package_info, product)

def read_from_json(file_path, product):
    with open(file_path, 'r') as fd:
        info = json.load(fd)

    if product is None:
        result = []
        for key, items in info.items():
            for item in items:
                if item not in result:
                    result.append(item)
    else:
        if product in info:
            result = info[product]
        else:
            result = []
    return result

def read_image_file(image_file):
    return read_from_file(image_file)

def read_package_file(package_file):
    return read_from_file(package_file)

def read_from_file(file_path):
    with open(file_path) as fd:
        lines = fd.readlines()
    result_list = []
    for line in lines:
        if line.strip() != "":
            result_list.append(line.strip())
    return result_list

def write_list_to_file(file_path, ls):
    with open(file_path, 'w') as fd:
        content = '\n'.join(ls)
        fd.write(content)

def import_images(images, dir, ip):
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) 
    image_file = "/tmp/images_%s" % current_time
    write_list_to_file(image_file, images)

    cmd = "cd tools; ./image_import.py %s %s/_docker_image alidocker1.12 %s" % (image_file, dir, ip)
    ret = os.system(cmd)
    return ret

def import_tj_packages(dir, packages):
    pangu_dir = "pangu://localcluster/_tianji_repository/"
    pu = "./libs/tianji_zhuque_sdk/pu"
    if os.path.exists("/apsara/deploy/pu"):
        pu = "/apsara/deploy/pu"
    ret = 0
    for package in packages:
        cmd = "%s cpdir %s -m overwritten -t normal --pangu_tool_defaultMinCopy=2 --pangu_tool_defaultMaxCopy=3 %s" % (pu, os.path.join(dir, "_tianji_repository", package), os.path.join(pangu_dir, package))
        ret = os.system(cmd)
        if ret != 0:
            break
    return ret

if __name__ == "__main__":
    parser = GetOption()
    opts, args = parser.parse_args()
    if opts.dir is None:
        parser.error("-n disk dir is needed")
    merge(opts.dir, opts.ip, opts.product, opts.skip_packages, opts.skip_images) 