#!/home/tops/bin/python
#coding:utf-8
import os
import os.path
import json
import time


def get_meta_sha256():
    ret = []
    # 1. 遍历repo目录获取所有product
    for _, products, _ in os.walk(repo_path):
        for product in products:
            product_path = os.path.join(repo_path, product)
            # 2. 遍历product下所有services
            for _, services, _ in os.walk(product_path):
                for service in services:
                    service_path = os.path.join(product_path, service)
                    tags_path = service_path + "/_manifests/tags"
                    # 3. 遍历services下所有tags
                    for _, tags, _ in os.walk(tags_path):
                        for tag in tags:
                            tag_path = os.path.join(tags_path, tag) + "/index/sha256"
                            for _, sha256s, _ in os.walk(tag_path):
                                for sha256 in sha256s:
                                    result = {}
                                    result["namespace"] = product
                                    result["image"] = service
                                    result["tag"] = sha256
                                    ret.append(result)
    return ret

def cat_meta_and_read(meta):
    ret = []
    # 1.拼接出你需要使用到的meta的信息在blobs中的具体值
    for m in meta:
        size = 0
        sha_no = m["tag"]
        sha_head = sha_no[0:2]
        data_path = "%s/%s/%s/data" % (blobs_path, sha_head, sha_no)
        with open(data_path, 'r') as f:
            datas = json.load(f)
            bls = datas["fsLayers"]
            #注意镜像文件去重的问题，因为强制发布可能会产生重复值
            blobs = []
            for bl in bls:
                blobs.append(bl["blobSum"])
            new_bls = list(set(blobs))
            for bl in new_bls:
                sha_v =  bl[7:]
                sha_h =  bl[7:9]
                cout_data_path = "%s/%s/%s/data" % (blobs_path, sha_h,sha_v)
                size += os.path.getsize(cout_data_path)/1024.0/1024
            m["size"] = str(int(size)) + "MB"
            ret.append(m)
    return ret


if __name__ == "__main__":
    try:
        registry_path = sys.argv[1]
    except Exception as e:
        registry_path = "/apsarapangu/disk2"
    repo_path = "%s/registry/docker/registry/v2/repositories" % (registry_path)
    blobs_path = "%s/registry/docker/registry/v2/blobs/sha256" % (registry_path)
    meta = get_meta_sha256()
    result = cat_meta_and_read(meta)
    result = json.dumps(result)
    print result