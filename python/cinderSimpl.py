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
#
#    some, but not all, of the cinder api - for us regular folks
#
Version = '0.3.0'

import re
import os
import sys
import time
import logging
import requests

from credentials import *

try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

DEFAULT_API_VERSION = '2'
debug = False

def get_cinder_client():
    """ create an instance of the cinder object with credentials """
    from cinderclient import client
    VERSION = DEFAULT_API_VERSION
    sess = get_v3_session()
    cinder = client.Client(VERSION, session=sess)
    return cinder


def cinder_create():
    """ create a small volume to test functionality
        hard coded to 1G

        @ params: none
        @returns volume object
    """
    cinder = get_cinder_client()
    v = {'size': 1, 'name': "RAINBOW-VOL01"}
    try:
        vol = cinder.volumes.create(**v)
    except:
        e = sys.exc_info()[0]
        print('Error [%s]' % e.message)
        raise
    return vol

def cinder_poll(vol):
    """ cinder_poll - check the status if a given volume

        @params: vol_id
        @returns: volume object

    """
    cinder = get_cinder_client()
    vol = cinder.volumes.get(vol.id)
    return vol

def cinder_delete(vol):
    """ cinder_delete - delete given volume

        @params: vol_id
        @returns: bool

    """
    cinder = get_cinder_client()
    # delete
    print("deleting volume [%s]" % vol.name)
    try:
        cinder.volumes.delete(vol)
        print("delete of volume [%s] scheduled." % vol.name)
        return True
    except:
        print("delete of volume [%s] FAILED." % vol.name)
        return False
 
def check_cinder_create():
    """ create and delete a small volume to test functionality
    """
    vol = cinder_create()

    rc = 0
    while vol.status == 'creating':
        print("%s:Volume status: '%s'" % (time.ctime(), vol.status))
        time.sleep(5)
        vol = cinder.volumes.get(vol.id)
        status = vol.status

    print("%s:Volume status: '%s'" % (time.ctime(), vol.status))
    if status == 'available':
        print "\n\nCinder: PASS\n\n"
        # return true if good
        rc = 1
    else:
        print "\n\nCinder: FAIL\n\n"
        return rc
    print "| %36s | %s  %s | %s\n\n" % (vol.id, vol.name,
                             vol.size, vol.status)
    cinder_delete(vol)
    return rc

def check_cinder_api():
    """ check the funcionality of the cinder api
        if no volume exists it will create one

       @param - none
       @ return True/False (1|0)
    """
    cinder = get_cinder_client()
    try:
        count = len(cinder.volumes.list())
        # if we have a list or no list and an auth token the test was good
        if  count or len(cinder.client.auth_token):
            print "\n\nCinder API: PASS\n\n"
            # return volume count if good
            return count
        else:
            print "\n\nCinder API: FAIL\n\n"
            return 0
    except:
        print "\n\nCinder API: FAIL\n\n"
        return 0


#__main__

def main():
    c = check_cinder()
    sys.exit(0)

if __name__ == '__main__':
    main()

