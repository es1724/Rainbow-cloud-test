#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# -*- coding: iso-8859-1 -*-
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
#    HOT formatting taken from hotGen.py written by Jake Howe(jh6103@att.com)
#    thanks Jake!
#
#    interface to all things heat

import time
from Tkinter import *
import tkSimpleDialog
version = '0.0.9'

import pdb
import os
import re
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

debug = False

from Tkinter import *
import tkSimpleDialog
import keystoneclient
import heatclient

from keystoneclient.v2_0.client import Client as ksclient
from heatclient.client import Client
import heatclient.shell as shell
import heatclient.exc as exc
from credentials import get_keystone_creds


# noinspection PyIncorrectDocstring
class RainbowHeat(object):
    '''  class for interfacing with heat '''

    def get_heat(self):
        """ get_heat - return an instance of the heat client
    
            @requires - credentials.py
            @params: none
            @returns: instance of the heatclient.client.Client
        """
    
        kscreds = get_keystone_creds()
        ks = ksclient(**kscreds)
        heat_url = ks.service_catalog.url_for(service_type='orchestration',
                                                     endpoint_type='publicURL')
        auth_token = ks.auth_token
        heat = Client('1', endpoint=heat_url, token=auth_token)
        return heat

    def stack_list(self):
        """ stack_list return a list of all stacks

            @params None
            @returns list of stack objects
        """
        try:
            hc = self.get_heat()
            sl = []
            for i in hc.stacks.list():
                sl.append(i)
        except:
            e = sys.exc_info()[0]
            print ('ERROR: %s' % e.message)
            raise
        return sl

    def stack_delete(self, sid):
        """ stack_delete

           @params stack id (str)
           @returns None
        """
        failure_count = 0
        fields = {'stack_id': sid}
        try:
            hc = self.get_heat()
            hc.stacks.delete(**fields)
        except exc.HTTPNotFound as e:
            failure_count += 1


    def stack_create(self,tfile,name):
        """
        stack_create - create a heat sstack given a template
    
        @params: heat orchestration template in yaml format
        @returns: 0 on success - 1 on error
        """

        args = ['stack-create',
            '--template-file',
            tfile,
            name]
        try:
          shell.HeatShell().main(args)
        except Exception as e:
          raise

    def get_list():
    #    print "get_list"
    # untested - written on spec
        heat = get_heat()
        list = []
        for i in heat.stacks.list():
            list.append(i)
        return list

    def check_heat_api():
        """ check_heat - check the heat api
            @param argparse obj
    
            @returns - count of stacks in the list
        """
        try:
            count = len(get_list())
            print "\nfound [" + str(count) + "] stacks"
            print "\nHeat: PASS\n\n"
            return count
        except:
            print "\n\nHeat: FAIL\n\n"
            return 0
    
    def heat_stack_list():
        list = get_list()
        print('%s: found [%d] stacks in the list' % (__name__, len(list)))
        return list
    
    def main():
        # mainly for CLI if the OS_TIMEOUT is not set
        if 'OS_TIMEOUT' not in os.environ.keys():
            os.environ['OS_TIMEOUT'] = '30'
        ok = check_heat_api()
    
class StackName(tkSimpleDialog.Dialog):

    def body(self, master):

        Label(master, text="Stackname:").grid(row=0)
        self.e1 = Entry(master)
        self.e1.grid(row=0, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.tname = str(self.e1.get())

    def get_name(self):
        return self.tname

class HotBox(tkSimpleDialog.Dialog):
    '''HotBox - popup window to prompt for template data'''

    def __init__(self, parent, title = None):

        self.count = 1
        self.volSize = 1
        tkSimpleDialog.Dialog.__init__(self, parent, title = title)

    def body(self, master, title = None):

        Label(master, text="# instances:").grid(row=0)
        self.e1 = Entry(master)
        self.e1.grid(row=0, column=1)
        Label(master, text="Volume size:").grid(row=1)
        self.e2 = Entry(master)
        self.e2.grid(row=1, column=1)
        Label(master, text="Volume size=0 for no volume").grid(row=2)
        return self.e1 # initial focus

    def apply(self):
        self.count = int(self.e1.get())
        self.volSize = int(self.e2.get())

    def get_name(self):
        return self.name

    def get_count(self):
        return self.count

    def get_size(self):
        return self.volSize

    if __name__ == '__main__':
        main()


class HotGen:
    """
    HotGen - class for generating a Heat Orchestration Template.
    template is intended for use in the rainbow tool but may be used
    in heat client as well. Minimum HOT may not produce accessible
    instances and is intended for infrastructure testing only.

    @params: none
    @returns: none
    """

    def __init__(self, parent):
        """
        :type self:object
        """
        self.filenameV = StringVar()
        self.imageV = StringVar()
        self.netV = StringVar()
        self.flaV = StringVar()
        self.keyV = StringVar()
        self.countV = IntVar()
        self.val_error = {}
        self.volSize = 0

    def set_image(self,i):
        ''' set_image(str) - set the number of instances
            @params: image id 
        '''
        self.imageV.set(i)

    def set_net(self,n):
        ''' set_count(str) - set the number of instances
            @params: net id
        '''
        self.netV.set(n)

    def set_flavor(self,fl):
        ''' set_count(str) - set the number of instances
            @params: flavor name or id 
        '''
        self.flaV.set(fl)

    def set_count(self,c):
        ''' set_count(int) - set the number of instances
            @params: count 
        '''
        self.countV.set(c)

    def set_volume_size(self,v):
        ''' set_volume_size(int) - set the number of instances
            @params: count 
        '''
        self.volSize = v

    def invalid(self):
        """
        validate minimum required vars:
            image, net and flavor
        validates existence only

        @params: none
        @returns: 0 = valid, 1 = invalid
    
        @sets: self.val_error[]
        """
        # set count to 1 if not set
        if self.countV.get() < 1:
            self.countV.set(1)
        if not len(self.filenameV.get()):
            self.filenameV.set("hot_example.yaml")
        if not len(self.imageV.get()):
            self.val_error['image'] = "HotGen error - image not set"
        if not len(self.netV.get()):
            self.val_error['network'] = "HotGen error - network not set"
        if not len(self.flaV.get()):
            self.val_error['flavor'] = "HotGen error - flavor not set"
        if 'OS_REGION_NAME' not in os.environ.keys():
            self.val_error['OS_REGION_NAME'] = "HotGen error - OS_REGION_NAME not set"
        if not isinstance(self.volSize, int):
            self.val_error['volSize'] = "HotGen error - volume size invalid"
        
        if not self.val_error.keys():
            return 0
        else:
            return 1

    def get_val_error(self):
        """
        get_val_error - return the var error dict

        @params: none
        @returns: dict
        """
        return self.val_error

    def set_filename(self,f):
        """
            create a popup allowing user to select a filename for 
            H.O.T. output and generate the H.O.T.

            @params: none
            @returns 0 on success and 1 on failure
        """
        # create a default filename to display
        # f = open(args.region + '_' + self.countV.get() + '_nodes.yaml', 'w+')
        self.filenameV.set(f)

        # generate file
 
    def get_filename(self):
        # create a default filename to display
        # f = open(args.region + '_' + self.countV.get() + '_nodes.yaml', 'w+')
        self.filenameV.set(os.environ['OS_REGION_NAME'] +
                           '_' +
                           str(self.countV.get()) +
                           '_nodes.yaml')
        return  self.filenameV.get()

    def hot_gen(self,f):
        """
        hot_gen - write H.O.T. to file
        """

        region = os.environ['OS_REGION_NAME']
        now = time.strftime("%m%d%Y")
        usr = os.environ['OS_USERNAME']
        # Write the parameters section
        f.write("""
# DATE: %s
# USER: %s
heat_template_version: 2014-10-16
description: Test Template for %d vm(s) in %s

parameters:
    image_id:
        type: string
        label: Image ID
        description: Image to be used for compute instance
        default: %s
    instance_flavor:
        type: string
        label: Instance Flavor
        description: Type of instance (flavor) to be used
        default: %s
    private_network:
        type: string
        label: Private Network
        description: Private/Internal network ID
        default: %s

resources:""" % (now,
                 usr,
                 int(self.countV.get()),
                 region,
                 self.imageV.get(),
                 self.flaV.get(),
                 self.netV.get()))

        # Write the VM/Volume section for each node
        for x in range(0, int(self.countV.get())):
            node = str(x).zfill(3)
            f.write("""
    # NODE%s
    node%s_vm:
        type: OS::Nova::Server
        properties:
            image: { get_param: image_id }
            flavor: { get_param: instance_flavor }
            networks:
                - network: { get_param: private_network }
            user_data_format: RAW
            user_data: |
                #!/bin/bash
                # set the root password
                echo "root:rainbow1"|/usr/sbin/chpasswd
    """ % (node,node))

            if self.volSize:
                f.write("""
    node%s_vol0:
        type: OS::Cinder::Volume
        properties:
            size: %d

    node%s_vol_att:
        type: OS::Cinder::VolumeAttachment
        properties:
            volume_id: { get_resource: node%s_vol0 }
            instance_uuid: { get_resource: node%s_vm }
    """ % (node,self.volSize,node,node,node))

        f.write("\n")
        f.close()


if __name__ == '__main__':
    pass
