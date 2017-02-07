#!/usr/bin/env python
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
#
version = '0.3.0'

#import pdb
import re
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

debug = False

import keystoneclient
import glanceclient

from keystoneclient.v2_0 import client
from glanceclient import Client
from credentials import get_keystone_creds

def get_glance():
    """ get glance - create the glance object

        @ params none
        @ returns - glance object
    """
    kscreds = get_keystone_creds()
    keystone = keystoneclient.v2_0.client.Client(**kscreds)
    auth_token = keystone.auth_token
    image_url = keystone.service_catalog.url_for(service_type='image',
                                                 endpoint_type='publicURL')
    image_url = re.sub(r'/v2/$', '', image_url, flags=re.IGNORECASE)
    glance = Client('2', endpoint=image_url, token=auth_token)
    return glance

def get_list(type = None):
    """ get_list given a type (public or None)
        get a list of image objects

        @params type(str)
        @returns list of image objects
    """
    glance = get_glance()
    filters = {}
    if type is 'public':
        filters = {'visibility': 'public'}
    kwargs = {'sort_key': 'name', 'sort_dir': 'asc', 'owner': None, 'filters': filters}

    list = []
    for i in glance.images.list(**kwargs):
        if i is not None:
            list.append(i)
    return list


# noinspection PyIncorrectDocstring
def check_glance_api():
    """ check_glance - check the glance api
        @param argparse obj

        @returns - count of images in the list
    """
    try:
        count = len(get_list(type = 'public'))
        print "\n\nGlance: PASS\n\n"
        return count
    except:
        print "\n\nGlance: FAIL\n\n"
        return 0

def glance_image_list():
    """ glance_image_list - yet another way to get a list of images
        from the departement of redundacy department

        @params none
        @ returns list of image objects
    """
    list = get_list()
    print('%s: found [%d] images in the list' % (__name__, len(list)))
    return list

def main():
    ok = check_glance_api()

    get_list()

if __name__ == '__main__':
    main()
