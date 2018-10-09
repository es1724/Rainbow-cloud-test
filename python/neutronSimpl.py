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
Version = '0.4.0'


import re
import os
import sys
import time
import logging
import requests
from Tkinter import *
import tkSimpleDialog

from neutronclient.v2_0 import client

from credentials import *


try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

debug = False


DESCRIPTION = sys.argv[0]
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG_FORMAT='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE = '%m-%d %H:%M'

def get_neutron_client():
    sess = get_v3_session()
    neutron = client.Client(session=sess)
    return neutron

def neutron_net_list():
    neutron = get_neutron_client()
    netlist = neutron.list_networks()
    return netlist

def check_neutron_api():
    """ check_neutron_api - do net-list to check neutron api

        @params arg obj (debug)

        @returns count of networks in list

    """
    netlist = neutron_net_list()
    count = len(netlist['networks'])
    if len(netlist):
        print "\n\nNeutron API check: PASS\n\n"
        return count
    else:
        print "\n\nNeutron API check: FAIL\n\n"
        return 0

def create_network():
    """ create_network() -create network usinf the neutron api

        @params - none
        Success:
        @rettype: char list (string): net id
        Failure:
        @return False (0)
    """
    name = 'RainbowNet-' + str(int(time.time()))
    return create_named_net(name)

def create_named_net(name):
    neutron = get_neutron_client()
    net_id = check_network_exists(neutron, name)
    if net_id:
        return net_id
    subnet_name = 'RainbowSubnet-' + str(int(time.time()))
    subnet = '10.99.99.0/24'
    net_descr = 'rainbow network'
    subnet_descr = 'rainbow subnet'
    nobj = {'name': name, 'admin_state_up': True}
    try:
        neutron.create_network({'network':nobj})
    except e:
        e = sys,exc_info()[0]
        self.print_line('Network create FAILED [%s]\n' % e.message)
        raise
    
    thisnet = neutron.list_networks(name=name)
    if not len(thisnet):
        LOG.exception("Neutron: create network failed")
        return 0
        
    netid = thisnet['networks'][0]['id']
    # if we created a network neutron is good
    print 'network id [' + netid + ']'


    # create a subnet
    subobj = {'name': subnet_name,
              'cidr': subnet,
              'gateway_ip': None,
              'network_id': netid,
              'ip_version': 4}
    neutron.create_subnet({'subnet':subobj})
    # future: check subnet status
    return netid

def delete_network(net_id):
    neutron = get_neutron_client()
    try:
        print('%s:Deleting network id [%s]' % (__name__, net_id))
        neutron.delete_network(net_id)
        return 1
    except:
        print("ERROR: Network delete failed.")
        e = sys.exc_info()[0]
        print('ERROR: %s' % e.message)
        raise
    return 0

def check_neutron():
    net_id = create_network()
    if net_id:
        delete_network(net_id)

def check_network_exists(neutron, name):
    try:
        thisnet = neutron.list_networks(name=name)
        netid = thisnet['networks'][0]['id']
        return netid
    except:
        return None

class NetName(tkSimpleDialog.Dialog):

    def __init__(self, parent, title = None, netname = None):
        self.nname = ''
        self.defname = netname
        tkSimpleDialog.Dialog.__init__(self, parent, title = title)

    def body(self, master):

        Label(master, text="Net Name:").grid(row=0)
        self.e1 = Entry(master)
        if self.defname:
            self.e1.insert(0, self.defname)
        self.e1.grid(row=0, column=1)
        return self.e1 # initial focus

    def apply(self):
       self.nname = str(self.e1.get())

    def get_name(self):
        if self.nname:
            return self.nname
        else:
            return None

# __main__

def main():
    n = check_neutron()
    sys.exit(0)

if __name__ == '__main__':
    main()


