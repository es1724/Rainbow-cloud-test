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
Version = '0.3.1'

import re
import os
import sys
import time
import logging
import requests
import argparse
from time import ctime as ct
from time import time as ut

from novaSimpl import check_nova_api
from novaSimpl import check_nova_create
from glanceSimpl import check_glance_api
from cinderSimpl import check_cinder_create
from cinderSimpl import check_cinder_api
from neutronSimpl import check_neutron
from neutronSimpl import check_neutron_api
from keystoneSimpl import check_keystone


try:
  requests.packages.urllib3.disable_warnings()
except:
  pass



DESCRIPTION = "Rainbow - cloud testing tool for openstack"
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG_FORMAT='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE = '%m-%d %H:%M'

DEBUG = False

# results
results = {}


# define functions

def parse_args ():
    ap = argparse.ArgumentParser(description=DESCRIPTION)

    ap.add_argument('-d', '--debug', action='store_true',
                    default=False, help='Show debugging output')
    ap.add_argument('-i', '--image', action='store',
                    default="",
                    help="Image for nova create")
    ap.add_argument('-n', '--net-id', action='store',
                    default="",
                    help="network id for nova create")
#    ap.add_argument('-c', '--config', action='store',
#                    default="",
#                    help="Path to configuration file")
    ap.add_argument('--action', action='store',
                    default="c",
                    help="Action either [c|r] client only or redundancy test")

    ap.add_argument('-p', '--process', action="store",
                    default="all",
                    help="Process to check [nova_api|nova_create|cinder_api|cinder_create|keystone|neutron_api|neutron_create] runs full API test suite if omitted. (no create tests)")
    ap_obj = ap.parse_args()
    for key in ['OS_TENANT_NAME', 'OS_USERNAME', 'OS_PASSWORD',
                'OS_AUTH_URL']:
        if key not in os.environ.keys():
            LOG.exception("Your environment is missing '%s'", key)
            sys.exit(0)
    return ap_obj

    

def format_results(results):
    for r in results:
        print r + ":" + str(results[r])
    

#__main__

# parse commandline
args = parse_args()
DEBUG = args.debug
if args.process == 'keystone':
    print( "Checking process[%s]" % args.process)
    results['keystone'] = check_keystone()
elif args.process == 'neutron_api':
    print( "Checking process[%s]" % args.process)
    results['neutron_api'] = check_neutron_api()
elif args.process == 'neutron':
    print( "Checking process[%s]" % args.process)
    results['neutron'] = check_neutron()
elif args.process == 'nova_create':
    print( "Checking process[%s]" % args.process)
#    l = args.__dict__
#    for i in l:
#        print '[' + i + '][' + str(l[i]) + ']'
    results['nova_api'] = check_nova_create(args)
elif args.process == 'nova_api':
    print( "Checking process[%s]" % args.process)
    results['nova_api'] = check_nova_api()
elif args.process == 'glance_api':
    print( "Checking process[%s]" % args.process)
    results['glance_api'] = check_glance_api()
elif args.process == 'cinder_api':
    print( "Checking process[%s]" % args.process)
    results['cinder_api'] = check_cinder_api()
elif args.process == 'cinder_create':
    print( "Checking process[%s]" % args.process)
    results['cinder'] = check_cinder_create(args)
elif args.process == 'glance':
    print( "Checking process[%s]" % args.process)
    check_glance()
elif args.process != 'all':
    print( "unknown process[%s]" % args.process)
    sys.exit(1)
else:
    results['keystone'] = check_keystone()
    results['nova_api'] = check_nova_api()
    results['neutron_api'] = check_neutron_api()
    results['cinder_api'] = check_cinder_api()
    results['glance_api'] = check_glance_api()


sys.exit(0)

format_results(results)
sys.exit(0)
