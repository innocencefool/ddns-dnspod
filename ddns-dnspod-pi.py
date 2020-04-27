#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import http.client
import json
import os
from socket import AF_INET6, SOCK_DGRAM, socket
from urllib import parse

import dns.resolver  # pip3 install dnspython -i https://pypi.tuna.tsinghua.edu.cn/simple

LOGIN_TOKEN = "13490,6b5976c68aba5b14a0558b77c17c3932"
DOMAIN = "dnspod.cn"
SUB_DOMAIN = "pi"

CONF_PATH = os.getcwd() + "/ddns-dnspod.conf"


def get_addr():
    try:
        sock = socket(AF_INET6, SOCK_DGRAM)
        sock.connect(("240C::6666", 53))
        addr = sock.getsockname()[0]
        sock.close()
        print("expect address : %s" % addr)
        return addr
    except Exception as e:
        print("get address failed : %s" % e)


def resolve():
    try:
        record = None
        resolver = dns.resolver.Resolver()
        resolver.lifetime = 6
        resolver.nameservers = ["119.29.29.29", '182.254.116.116']
        res = resolver.query(SUB_DOMAIN + "." + DOMAIN, "AAAA")
        for answer in res.response.answer:
            for item in answer.items:
                record = item.address
        print("record address : %s" % record)
        return record
    except Exception as e:
        print("resolve %s failed : %s" % (SUB_DOMAIN + "." + DOMAIN, e))


def load_conf():
    try:
        domain_id = None
        record_id = None
        if os.path.exists(CONF_PATH):
            with open(CONF_PATH, "r") as conf:
                lines = conf.readlines()
                for line in lines:
                    if "DOMAIN_ID" == line.split("=")[0]:
                        domain_id = line.split("=")[1][0:-1]
                    elif "RECORD_ID" == line.split("=")[0]:
                        record_id = line.split("=")[1][0:-1]
        print("DOMAIN_ID=%s, RECORD_ID=%s" % (domain_id, record_id))
        return [domain_id, record_id]
    except Exception as e:
        print("load config failed : %s" % e)


def save_conf(domain_id, record_id):
    try:
        if domain_id is not None and record_id is not None:
            with open(CONF_PATH, "w") as conf:
                conf.write("DOMAIN_ID=" + domain_id + "\n")
                conf.write("RECORD_ID=" + record_id + "\n")
                print("save config success")
    except Exception as e:
        print("save config failed : %s" % e)


def clear_conf():
    try:
        with open(CONF_PATH, "w") as conf:
            conf.write("")
            print("clear config success")
    except Exception as e:
        print("clear config failed : %s" % e)


def dict_param(domain=None, domain_id=None, sub_domain=None, record_id=None, record_type=None, value=None,
               record_line_id=None):
    param = dict(format="json", login_token=LOGIN_TOKEN)
    if domain is not None:
        param["domain"] = domain
    if domain_id is not None:
        param["domain_id"] = domain_id
    if sub_domain is not None:
        param["sub_domain"] = sub_domain
    if record_id is not None:
        param["record_id"] = record_id
    if record_type is not None:
        param["record_type"] = record_type
    if value is not None:
        param["value"] = value
    if record_line_id is not None:
        param["record_line_id"] = record_line_id
    return param


def request_dnsapi(url, body):
    try:
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
        conn = http.client.HTTPSConnection(host="dnsapi.cn", timeout=6)
        conn.request("POST", url, parse.urlencode(body), headers)
        res = conn.getresponse()
        result = None
        if res.status == 200:
            result = json.loads(res.read().decode("utf-8"))
        else:
            print("request dnsapi failed : %s" % res.reason)
        conn.close()
        return result
    except Exception as e:
        print("request dnsapi failed : %s" % e)


def get_domain_id():
    try:
        param = dict_param(domain=DOMAIN)
        res = request_dnsapi("/Domain.Info", param)
        if res is not None:
            if res.get("domain") is not None:
                print("get domain id success : %s" % res.get("domain").get("id"))
                return res.get("domain").get("id")
            else:
                print("get domain id failed : %s" % res.get("status").get("message"))
    except Exception as e:
        print("get domain id failed : %s" % e)


def get_record_id(domain_id):
    try:
        param = dict_param(None, domain_id, SUB_DOMAIN, None, "AAAA", None, None)
        res = request_dnsapi("/Record.List", param)
        if res is not None:
            if res.get("records") is not None:
                print("get record id success : %s" % res.get("records")[0].get("id"))
                return res.get("records")[0].get("id")
            else:
                print("get record id failed : %s" % res.get("status").get("message"))
    except Exception as e:
        print("get record id failed : %s" % e)


def create_record(domain_id):
    try:
        param = dict_param(None, domain_id, SUB_DOMAIN, None, "AAAA", "1::1", 0)
        res = request_dnsapi("/Record.Create", param)
        if res is not None:
            if res.get("record") is not None:
                print("create record success : %s" % res.get("record").get("id"))
                return res.get("record").get("id")
            else:
                print("create record failed : %s" % res.get("status").get("message"))
    except Exception as e:
        print("create record failed : %s" % e)


def ddns_record(domain_id, record_id):
    try:
        param = dict_param(None, domain_id, SUB_DOMAIN, record_id, None, None, 0)
        res = request_dnsapi("/Record.Ddns", param)
        if res is not None:
            print("ddns record result : %s" % res.get("status").get("message"))
            return res.get("status").get("code") == "1"
    except Exception as e:
        print("ddns record failed : %s" % e)


def modify_record(domain_id, record_id, address):
    try:
        param = dict_param(None, domain_id, SUB_DOMAIN, record_id, "AAAA", address, 0)
        res = request_dnsapi("/Record.Modify", param)
        if res is not None:
            print("modify record result : %s" % res.get("status").get("message"))
            return res.get("status").get("code") == "1"
    except Exception as e:
        print("modify record failed : %s" % e)


def start_ddns():
    try:
        domain_id = None
        record_id = None
        expect_addr = get_addr()
        record_addr = resolve()
        if expect_addr is not None:
            if record_addr is None or record_addr != expect_addr:
                conf = load_conf()
                if conf is not None:
                    domain_id = conf[0]
                    record_id = conf[1]
                if domain_id is None or record_id is None:
                    domain_id = get_domain_id()
                    if domain_id is not None:
                        record_id = get_record_id(domain_id)
                        if record_id is None:
                            record_id = create_record(domain_id)
                        if record_id is not None:
                            if ddns_record(domain_id, record_id):
                                if modify_record(domain_id, record_id, expect_addr):
                                    save_conf(domain_id, record_id)
                else:
                    if not modify_record(domain_id, record_id, expect_addr):
                        clear_conf()
    except Exception as ex:
        print("start ddns failed : %s" % ex)


if __name__ == '__main__':
    start_ddns()
