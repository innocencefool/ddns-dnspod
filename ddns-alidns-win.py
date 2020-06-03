#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import os
import socket

from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkcore.client import AcsClient

# pip3 install aliyun-python-sdk-alidns -i https://mirrors.aliyun.com/pypi/simple

ACCESSKEY_ID = 'AccessKey ID'
ACCESSKEY_SECRET = 'AccessKey Secret'
DOMAIN = 'alidns.com'
SUBDOMAIN = 'www'

CONF_PATH = os.getcwd() + '\\ddns-alidns.conf'

acsClient = AcsClient(ACCESSKEY_ID, ACCESSKEY_SECRET, 'cn-hangzhou')


def load_conf():
    if os.path.exists(CONF_PATH):
        with open(CONF_PATH, 'r') as conf:
            return conf.readline().replace('\n', '')


def save_conf(save_id):
    with open(CONF_PATH, 'w') as conf:
        conf.write(save_id)


def clear_conf():
    with open(CONF_PATH, 'w') as conf:
        conf.write('')


def get_expect_addr():
    ip_addr = None
    try:
        client = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        client.connect(('2400:3200::1', 53))
        ip_addr = client.getsockname()[0]
        client.close()
    except:
        pass
    return ip_addr


def get_record_addr():
    ip_addr = None
    try:
        client = socket.getaddrinfo('%s.%s' % (SUBDOMAIN, DOMAIN), 3389)
        ip_addr = client[0][4][0]
    except:
        pass
    return ip_addr


def get_record():
    get_record_id = None
    try:
        request = DescribeSubDomainRecordsRequest()
        request.set_SubDomain('%s.%s' % (SUBDOMAIN, DOMAIN))
        request.set_Type('AAAA')
        request.set_DomainName(DOMAIN)
        request.set_accept_format('json')
        response = acsClient.do_action_with_exception(request)
        get_record_id = json.loads(response)['DomainRecords']['Record'][0]['RecordId']
    except:
        pass
    return get_record_id


def add_record(ip_addr):
    add_record_id = None
    try:
        request = AddDomainRecordRequest()
        request.set_DomainName(DOMAIN)
        request.set_RR(SUBDOMAIN)
        request.set_Type('AAAA')
        request.set_Value(ip_addr)
        request.set_accept_format('json')
        response = acsClient.do_action_with_exception(request)
        add_record_id = json.loads(response)['RecordId']
    except:
        pass
    return add_record_id


def update_record(update_id, ip_addr):
    update_record_id = None
    try:
        request = UpdateDomainRecordRequest()
        request.set_RR(SUBDOMAIN)
        request.set_RecordId(update_id)
        request.set_Type('AAAA')
        request.set_Value(ip_addr)
        request.set_accept_format('json')
        response = acsClient.do_action_with_exception(request)
        update_record_id = json.loads(response)['RecordId']
    except:
        pass
    return update_record_id


if __name__ == '__main__':
    record_id = None
    expect_addr = get_expect_addr()
    print('get_expect_addr : %s' % expect_addr)
    record_addr = get_record_addr()
    print('get_record_addr : %s' % record_addr)
    if expect_addr:
        if record_addr is None or record_addr != expect_addr:
            record_id = load_conf()
            if record_id is None or record_id == '':
                record_id = get_record()
                if record_id is None or record_id == '':
                    record_id = add_record(expect_addr)
                    print('add_record : %s' % record_id)
                else:
                    print('get_record_id : %s' % record_id)
                    update_record(record_id, expect_addr)
                    print('update_record : %s' % record_id)
                save_conf(record_id)
                print('save_conf : %s' % record_id)
            else:
                print('load_conf : %s' % record_id)
                if update_record(record_id, expect_addr):
                    print('update_record : %s' % record_id)
                else:
                    clear_conf()
                    print('clear_conf : %s' % record_id)
