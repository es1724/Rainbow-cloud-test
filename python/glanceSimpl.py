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

from credentials import *


debug = False

def get_glance():
    """ get glance - create the glance object

        @ params none
        @ returns - glance object
    """
    from keystoneauth1 import loading
    from keystoneauth1 import session
    from glanceclient import Client
    creds = get_v3_creds()
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**creds)
    s = session.Session(auth=auth)

    glance = Client('2', session=s)
    
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
        try:
            if i is not None:
                list.append(i)
        except:
            pass
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
