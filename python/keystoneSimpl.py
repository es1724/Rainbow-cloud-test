#! /usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2015 AT&T Services, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#    Authors: Ed Smith (edward.smith@att.com)
#             Dan Bice (dan.bice@att.com)
version = '0.2.0'

import os
import sys
import logging
import requests
from credentials import get_keystone_creds

try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

debug = False

def get_keystone_client():
    kscreds = get_keystone_creds()
    from keystoneclient.v2_0 import Client as ks
    try:
        keystone = ks(**kscreds)
    except:
        e = sys.exc_info()[0]
        print ('ERROR: %s' % e.message)
        raise
    if 'OS_TENANT_NAME' not in os.environ.keys():
       os.environ['OS_TENANT_NAME'] = keystone.project_name
    if 'OS_TENANT_ID' not in os.environ.keys():
       os.environ['OS_TENANT_ID'] = keystone.project_id
    return keystone

def check_keystone():
    """check keystone api function"""
    try:
        keystone = get_keystone_client()
    except:
        e = sys.exc_info()[0]
        raise
        return 0
    if len(keystone.auth_token):
        print "\n\nKeystone: PASS\n\n"
        return 1
    else:
        print "\n\nKeystone: FAIL\n\n"
        return 0

if __name__ == '__main__':
    check_keystone()
