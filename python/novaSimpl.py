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
Version = '0.5.0'
import re
import sys
import six
import json
import time
import logging
import webbrowser
from Tkinter import *
import tkSimpleDialog

from inspect import currentframe, getframeinfo
import requests
from credentials import *
from neutronSimpl import create_network

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


debug = True
DESCRIPTION = "Rainbow - cloud testing tool for Openstack"
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG_FORMAT='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE = '%m-%d %H:%M'

DEFAULT_NOVA_API_VERSION = '2'


class ShowNova:

    def __init__(self, iid=None):
        # holder for server info
        self.iid = iid
        self.info = {}
        # what to get
        self.attribs = ['addresses',
                        'OS-DCF:diskConfig',
                        'OS-EXT-AZ:availability_zone',
                        'OS-EXT-SRV-ATTR:host',
                        'OS-EXT-SRV-ATTR:hypervisor_hostname',
                        'OS-EXT-SRV-ATTR:instance_name',
                        'OS-EXT-STS:power_state',
                        'OS-EXT-STS:task_state',
                        'OS-EXT-STS:vm_state',
                        'OS-SRV-USG:launched_at',
                        'OS-SRV-USG:terminated_at',
                        'accessIPv4',
                        'accessIPv6',
                        'config_drive',
                        'created',
                        'fault',
                        'flavor',
                        'hostId',
                        'id',
                        'image',
                        'key_name',
                        'metadata',
                        'name',
                        'os-extended-volumes:volumes_attached',
                        'progress',
                        'security_groups',
                        'status',
                        'tenant_id',
                        'updated',
                        'user_id'
                       ]
        self.nc = get_nova_client()
        if self.iid:
            self.get_info(self.nc, self.iid)

    def get_info(self, nc, iid):
        """
        get_info(iid)
            get info on an id when instance exists or was called with no instance id
            populates self.info[]
        :param nova client, iid:
        :return:
        """
        try:
            self.server = self.nc.servers.get(iid)
            self.allinfo = self.server.__dict__
            print "before"
            for k in self.attribs:
                try:
                    self.info[k] = self.allinfo[k]
                except KeyError:
                    print "key error"
                    pass
            self.reformat()
            print "after"
        except:
            e = sys.exc_info()[0]
            print('Exception [%s]' % e.message)
            raise

    def reformat(self):
        """
        reformat()
        addresses, flavor, image and security_groups need reformatting
        """

        #### key[addresses] val[{u'ORT-NET01':
        #                    [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:f4:60:84',
        #                      u'version': 4, u'addr': u'10.99.99.170',
        #                      u'OS-EXT-IPS:type': u'fixed'}]}]
        # list of networks
        if 'addresses' in self.info.keys():
            addrs = []
            for key in self.info['addresses'].keys():
                for n in self.info['addresses'][key]:
                    addrs.append(n['addr'])
                self.info[key] = ', '.join(addrs)
            del self.info['addresses']

        #### flavor
        # key[flavor] val[{u'id': u'3c3b4abf-9387-4d62-8662-f9ceece51024',
        # u'links': [{u'href': u'http://compute-aic.pdk1.cci.att.com:8774/ab83ab7adcb74fec9682fae6b3ba9ad9
        # /flavors/3c3b4abf-9387-4d62-8662-f9ceece51024',
        # u'rel': u'bookmark'}]}]
        if 'flavors' in self.info.keys():
            fl = self.nc.flavors.get(self.info['flavor']['id'])
            self.info['flavor'] = fl.name

        #### key[image] val[{u'id': u'c6a7f01b-f232-40a6-b78a-78550153950e',
        # u'links': [{u'href': u'http://compute-aic.pdk1.cci.att.com:8774/ab83ab7adcb74fec9682fae6b3ba9ad9
        # /images/c6a7f01b-f232-40a6-b78a-78550153950e', u'rel': u'bookmark'}]}]
        if 'image' in self.info.keys():
            im = self.nc.images.get(self.info['image']['id'])
            iname = im.name + '(' + im.id + ')'
            self.info['image'] = self.nc.images.get(self.info['image']['id']).name + '(' + self.info['image']['id'] + ')'

        #### key[security_groups] val[[{u'name': u'default'}]]
        if 'security_groups' in self.info.keys():
            sg = []
            for s in self.info['security_groups']:
                sg.append(s['name'])
            self.info['security_groups'] = ', '.join(sg)
        #

        #### reformat fault to print multi-line output
        if 'fault' in self.info.keys():
            try:
                for k in self.info['fault'].keys():
                    key = 'fault.' + k
                    self.info[key] = self.info['fault'][k]
                del self.info['fault']
            except Exception as e:
                print('%s:ERROR: %s' % (__name__,six.text_type(e)))
                pass
              



# end of ShowNova

# define functions

#  spew some info with debug
def debug_out(line):
    if debug:
        print(line)

def get_nova_client():
    from novaclient import client as novaclient
    s = get_session()
    VERSION = DEFAULT_NOVA_API_VERSION
    nova = novaclient.Client(VERSION, session=s)
    return nova




def get_nova_list():
    """ get_nova_list
       
        @params None
        @returns nova list object
    """
    nova = get_nova_client()
    nlist = nova.servers.list()
    return nlist

def get_hypervisor_list():
    """ get_hypervisor_list - returns list of valid hypervisors
        hypervisors must be 'up' and 'enabled' in nova services

        @param: none

        @returns: list of available hypervisor names
    """
    nova = get_nova_client()
    h_objects = nova.hypervisors.list()
    hlist = []
    for obj in h_objects:
        if (obj.state == 'up') and (obj.status == 'enabled'):
          hlist.append(obj.hypervisor_hostname)
    return hlist

def get_flavor_list():
    """ get_flavor_list - return the flavor list

        @param: none

        @returns: flavor list
     """
    nova = get_nova_client()
    flavors = nova.flavors.list()
    return flavors

def get_flavor_byname(name):
    """ get_flavor_byname - the flavor_id selection tool

        @param: none

        @returns: flavor_id
     """
    # only show m.1 flavors
    nova = get_nova_client()
    try:
        f = nova.flavors.find(name = name)
        return f
    except:
        return None

def get_console_out(id):
    """ get_console_out - get the console output for a give server

        @param Server obj (or id)

        @returns '\n' delimited console output
    """
    nova = get_nova_client()
    try:
        con = nova.servers.get_console_output(id)
        return con
    except:
        e = sys.exc_info()[0]
        print('ERROR: %s' % e.message)
        raise

    return 0

def nova_create(**kwargs):
    """ create_instance(**kwargs) - create a single instance

        @params: args object from argparse
        @requires image, net-id

        @returns server object

    """
    nova = get_nova_client()
#    pdb.set_trace()
    # create an instance using the main() from novaclient.shell
    kwa = {} # dict of create arges 
    kwa['image'] = kwargs['image_id']
    kwa['flavor'] = kwargs['flavor_id']
    kwa['nics'] = [{'net-id': str(kwargs['net_id'])}]
    kwa['name']= kwargs['name']
    ##############################################################
    # if we are using availaiblity zones to build to a specific
    # host we ignore num_instances
    # note that novaclient.Client.server.create() takes a minimum of 4 args
    ##############################################################
    if 'availability_zone' in kwargs:
        kwa['availability_zone'] = kwargs['availability_zone']
    elif 'num_instances' in kwargs:
        kwa['min_count'] = kwargs['num_instances']
        kwa['max_count'] = kwargs['num_instances']
    else:
        # dummy value
        kwa['key_name'] = None
    try:
        v = nova.servers.create(**kwa)
    except:
        e = sys.exc_info()[0]
        print('%s:ERROR: %s' % (__name__,e.message))
        raise
    return v


def create_instance(**kwargs):
    """ create_instance(**kwargs) - create a tested (needs a rework)

        @params: args object from argparse
        @requires image, net-id

        @returns nothing (this is the 'needs work' part)

    """
    # create an instance using the main() from novaclient.shell
    i = kwargs['image_id']
    f = kwargs['flavor_id']
    net = "net-id=" + str(kwargs['net_id'])
    name = kwargs['name']
    sys.argv = [sys.argv[0], "boot",
                "--image", i,
                "--flavor", f,
                "--nic", net,
                name]
    # future: change to a real api call
    from novaclient.shell import main as nova
    try:
        nova()
    except:
      raise

def poll(**kwargs):
    """ poll status of build
        @params instance id or name

        @returns current server onject
    """
    nova = get_nova_client()
    try: 
        server = nova.servers.find(id=kwargs['id'])
    except KeyError:
        try:
            server = nova.servers.find(name = kwargs['name'])
        except:
            e = sys.exc_info()[0]
            print('ERROR: %s' % e.message)
            raise

    print('%s|%s|%s' % ( server.id, server.status.ljust(8), server.name))
    return server

def nova_delete(id): 
    nova = get_nova_client()
    try:
      nova.servers.delete(id)
    except:
        raise
    return

def check_nova_create(args):
    """ check nova api and scheduler function 

         @params: [image_id, net_id, flavor_id, debug(bool)]

         @returns bool

    """
    LOG.info('checking nova')
    nova = get_nova_client()

    rc = 0

    # get the image id
    image = get_image(args,nova)
    if not image:
        print "No suitable test image not found run again with '-i <image>'!"
        sys.exit(0)
    print ("\nUsing image [%s]\n" % image.name)
    debug_out("\nImage id [%s]\n" % image.id)

    # get the flavor
    try:
        flavor_id = args.flavor_id
    except:
        flavor_id = get_flavor_byname('m1.small').id
    print "flavor_id [" + str(flavor_id) + "]"

    if args.net_id:
        net_id = args.net_id
    else:
        net_id = create_network()
    if net_id:
        print("Line: %s" % str(getframeinfo(currentframe()).lineno))
        print "net_id [" + str(net_id) + "]"
    else:
        # we should never get here but just in case we do..
        print("Line: %s" % str(getframeinfo(currentframe()).lineno))
        print "Network invalid. Create failed."
        sys,exit(1)

    #  instance 
    name = "ORT-simpl-" + str(int(time.time()))
    # alt method uses shell.main()
    create_args = {}
    create_args['name'] = name
    create_args['net_id'] = net_id
    create_args['image_id'] = image.id
    create_args['flavor_id'] = flavor_id
    create_instance(**create_args)
    # Wait until built
    server = nova.servers.find(name=name)
    server = poll(id=server.id)
    if server.status == 'ACTIVE':
        rc = 1
    else:
        while server.status == 'BUILD':
            print("%s:Instance status: '%s'" % (time.ctime(), server.status))
            time.sleep(5)
            server = nova.servers.get(server.id)
            server.status
        if server.status == 'ACTIVE':
            rc = 1
        else:
        # if it's not active it's a fail.
            rc = 0
    print("%s:Instance status: '%s'", time.ctime(), server.status)
    # we're done here - delete everything
    confirm = raw_input('Delete instance? [y/n] ')
    if confirm == 'y':
        print "\nDeleting instance id [" + server.id + "]\n"
        nova_delete(server.id)
    return rc

def check_nova_api():
    """ check nova api function 

         @params: debug(bool)

         @returns bool

    """
    nova = get_nova_client()
    # do an instance list to confirm api ops
    # nova credentials
    try:
        count = len(nova.servers.list())
        print "\n\nNova API check: PASS\n\n"
        return count
    except:
        print "\n\nNova API check: FAIL\n\n"
        return 0

class GetVnc:
    """ open a console given the instance id 

        @params: iid(instance id)
        @returns nothing
    """
 
    def __init__(self, iid=None):
        # holder for server info
        self.iid = iid
        self.url = ''
        self.nc = get_nova_client()

    def open_vnc_console(self):
        """ open a console 
    
            @params: None
            @returns nothing
        """

        self.con = self.nc.servers.get_vnc_console(self.iid, 'novnc')
        #open i a new tab if possible
        new = 2
        try:
            webbrowser.open(self.con['console']['url'])
        except:
            print "\nFailed to open console.\n"

class BootBox(tkSimpleDialog.Dialog):


    def __init__(self, parent, title = None, bootName = None):

        self.bootName = ''
        self.name = ''
        self.count = 1
        if bootName:
            self.bootName = bootName
        tkSimpleDialog.Dialog.__init__(self, parent, title = title)

    def body(self, master):

        Label(master, text="Name:").grid(row=0)
        self.e1 = Entry(master)
        if self.bootName:
            self.e1.insert(0, self.bootName)
        Label(master, text="# of instances:").grid(row=1)
        self.e2 = Entry(master)
        self.e2.insert(0, '1')
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):

        self.name = str(self.e1.get())
        self.count = int(self.e2.get())


    def get_name(self):

        if self.name:
            return self.name
        else:
            return None

    def get_count(self):

        return self.count
