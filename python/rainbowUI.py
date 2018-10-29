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
import argparse
from buttons import *
import os
import re
import sys
import six
import subprocess
import sys
from time import ctime as ct
from time import time as ut
from Tkinter import *
from tkFileDialog import asksaveasfile
from tkFileDialog import askopenfilename
from tkMessageBox import *

from credentials import *
from heatSimpl import *
from utils import *
from novaSimpl import *
from glanceSimpl import check_glance_api
from glanceSimpl import glance_image_list
from cinderSimpl import cinder_create
from cinderSimpl import cinder_delete
from cinderSimpl import cinder_poll
from cinderSimpl import check_cinder_api
from neutronSimpl import *
from keystoneSimpl import check_keystone
from keystoneSimpl import get_keystone_client


version = '3.0.1'
date = '10/24/2018'
DESCRIPTION = "Rainbow UI openstack test framework."
DEBUG = 0
# default timeout for procs

initial_screen = ['Welcome to the Rainbow Cloud Test Framework.',
                  '',
                  'This app will perform basic API tests.',
                  '',
                  'Listing images and networks will allow',
                  'selection from a (filtered) list',
                  '',
                  '\'Nova Create\' will create an instance.',
                  '\'Poll\' will poll instance status.'
                 ]

class RainbowUI:

    def __init__(self):
        """

        :type self: object
        """
        self.Status = ''
        self.messages = []
        self.ap = argparse.ArgumentParser(description=DESCRIPTION)
        self.args = self.parse_args()
        self.vm = None
        self.flavors = None
        self.vol = None
        self.poll_count_max = 30
        if self.args.poll:
            self._debug('setting poll-max[%s]' % self.args.poll)
            self.poll_count_max = int(self.args.poll)
        # offset for select lists
        self.offset = 0
        self.type = 'None'
        self.activeVar = None
        self.typelist = {}
        self.multiSelect = []
        self.toplist = []
        self.top = Tk()
        self.top.title('Rainbow Cloud Test Framework')
        self.labelfm = Frame(self.top)
        self.label = Label(self.labelfm,
                           padx=10,
                           text='Version: ' + version
                           )
        self.label.grid(row=0, column=0)

        self.userV = StringVar()
        self.userLabel = Label(self.labelfm,
                               padx=10,
                               textvariable = self.userV)
        try:
            if 'OS_PROJECT_NAME' in os.environ.keys():
                self.userV.set('Project:' + os.environ['OS_PROJECT_NAME'])
            else:
                self.userV.set('Project:' + os.environ['OS_TENANT_NAME'])
        except:
            self.userV.set('Project: Not Set')
        self.userLabel.grid(row=0, column=9)
 
        self.siteOVar = StringVar()
        self.siteOVar.trace("w", self._set_site)
        self.siteV = StringVar()
        self.siteLabel = Label(self.labelfm,
                               padx=10,
                               textvariable=self.siteV)
        self.siteLabel.grid(row=0, column=10)

        self.labelfm.pack()

        self.statusfm = Frame(self.top)

        self.statussb = Scrollbar(self.statusfm)
        self.statusxsb = Scrollbar(self.statusfm, orient=HORIZONTAL)
        self.statuslb = Listbox(self.statusfm,
                                height=15,
                                width=90,
                                font=('Courier', 12),
                                selectmode=EXTENDED,
                                yscrollcommand=self.statussb.set,
                                xscrollcommand=self.statusxsb.set
                                )
        self.statuslb.bind("<Return>", self._select)
        self.statuslb.bind("<Double-Button-1>", self._selectbind)
        self.statussb.config(command=self.statuslb.yview)
        self.statusxsb.config(command=self.statuslb.xview)
        # api vertical button frame
        self.apivfm = Frame(self.statusfm)
        self.siteL = Label(self.apivfm, text="Site:")
        self.siteL.pack(fill=X)
        self.siteList = []
        self.siteList = self._get_site_list(self.args.sites)
        if len(self.siteList):
            self.siteOVar.set(self.siteList[0])
        else:
#            self.messages.append('Warning: OS_REGION_NAME is not set - using default site')
            self.siteOVar.set('None')
        self.siteOM = apply(OptionMenu, (self.apivfm, self.siteOVar) + tuple(self.siteList))
        self.siteV.set('Site:%s' % self.siteOVar.get())
        self.siteOM.pack(fill=X)

        self.credB = Bbut(self.apivfm, "Login", self._get_creds)

        # API test buttons
        self.apiL = Label(self.apivfm, text="API tests:")
        self.keyB = Bbut(self.apivfm, "Keystone", self.keyOp)
        self.novB = Bbut(self.apivfm, "Nova", self.novOp)
        self.glaB = Bbut(self.apivfm, "Glance", self.glaOp)
        self.cinB = Bbut(self.apivfm, "Cinder", self.cinApiOp)
        self.neuB = Bbut(self.apivfm, "Neutron", self.neuOp)
        self.allB = Bbut(self.apivfm, "Test ALL", self.allOp)
        # pack em up!
        self.credB.pack(fill=X)
        self.apiL.pack(fill=X)
        self.keyB.pack(fill=X)
        self.novB.pack(fill=X)
        self.glaB.pack(fill=X)
        self.cinB.pack(fill=X)
        self.neuB.pack(fill=X)
        self.allB.pack(fill=X)
        self.apivfm.pack(side=RIGHT, fill=Y)
        self.statussb.pack(side=LEFT, fill=Y)
        self.statusxsb.pack(side=BOTTOM, fill=X)
        self.statuslb.pack(side=LEFT, fill=BOTH, expand=True)
        self.statusfm.pack(fill=BOTH,expand=True)

        # build frame
        self.bframe = Frame(self.top)
        # variable frame
        self.varfm = Frame(self.bframe)
        # filter pattern
        self.filterVar = StringVar()
        self.filterL = Label(self.varfm, text="Filter:")
        self.filterL.grid(row=0, column=0)
        self.filterE = Entry(self.varfm, textvariable=self.filterVar, width=36, bd=2)
        self.filterE.grid(row=0, column=1)
        # image id
        self.imageVar = StringVar()
        self.imageL = Label(self.varfm, text="Image")
        self.imageL.grid(row=1, column=0)
        self.imageE = Entry(self.varfm, textvariable=self.imageVar, width=36, bd=2)
        self.imageE.grid(row=1, column=1)

        # flavors
        self.flaVar = StringVar()
        self.flaL = Label(self.varfm, text="Flavor")
        self.flaL.grid(row=2, column=0)
        self.flaE = Entry(self.varfm, textvariable=self.flaVar, width=36, bd=2)
        self.flaE.grid(row=2, column=1)

        # net id
        self.netIdVar = StringVar()
        self.netIdL = Label(self.varfm, text="Net ID")
        self.netIdL.grid(row=3, column=0)
        self.netIdE = Entry(self.varfm, textvariable=self.netIdVar, width=36, bd=2)
        self.netIdE.grid(row=3, column=1)

        # instance id
        self.novaLV = StringVar()
        self.novaL = Label(self.varfm, text="vm/stack ID")
        self.novaL.grid(row=4, column=0)
        self.novaLE = Entry(self.varfm, textvariable=self.novaLV, width=36, bd=2)
        self.novaLE.grid(row=4, column=1)
        # POLL vars
        self.pollVar = StringVar()
        self.pollVar.set(True)
        # adhoc command
        self.cmndV = StringVar()
        self.cmndL = Label(self.varfm, text="Command")
        self.cmndL.grid(row=5, column=0)
        self.cmndE = Entry(self.varfm, textvariable=self.cmndV, width=36, bd=2)
        self.cmndE.grid(row=5, column=1)

        # button frame
        self.bufm1 = Frame(self.bframe)

        self.glaIlB = Bbut(self.bufm1, "Image List", self.glaIl)
        self.neuNlB = Bbut(self.bufm1, "Net List", self.neuNl)
        self.flaLB = Bbut(self.bufm1, "Flavor List", self.flaList)
        self.selB = Gbut(self.bufm1, "Select", self._select)

        # instance count
        self.cntVar = IntVar()
        self.cntVar.set(1)
#        self.cntVar.set(1)
        #self.cntL = Label(self.bufm1, text="# to launch")
#        self.cntE = Entry(self.bufm1, textvariable=self.cntVar, width=5, bd=2)

        self.netCB = Gbut(self.bufm1, "Net Create", self._net_create)
        self.vncCB = Gbut(self.bufm1, "VNC Console", self._get_vnc_console)
        # H.O.T. buttons
        self.hotGB = Gbut(self.bufm1, "HOT Gen", self._hot_gen)
        self.hotRB = Gbut(self.bufm1, "Stack Create", self._run_hot)
        self.staLB = Gbut(self.bufm1, "Stack list", self._stack_list)
        self.staDB = Gbut(self.bufm1, "Stack delete", self._stack_delete)


#        self.netDB = Rbut(self.bufm1, "Net Delete", self._net_delete)

        self.novaConB = Gbut(self.bufm1, "Nova Console", self.nova_console)
        self.novaCB = Gbut(self.bufm1, "Nova Create", self.nova_boot)
        self.novLB = Bbut(self.bufm1, "Nova list", self.nova_list)
        self.novDB = Rbut(self.bufm1, "Nova delete", self._nova_delete)
        self.novSB = Gbut(self.bufm1, "Nova show", self._nova_show)
        self.novaBA = Gbut(self.bufm1, "Build All", self.nova_boot_all)
        self.pollB = Bbut(self.bufm1, 'Poll VM', self._poll)

        self.runB = Bbut(self.bufm1, "Run", self.run_adhoc)

        self.statuslb.pack(side=LEFT, fill=BOTH)

        # column 0
        self.glaIlB.grid(row=0, column=0)
        self.flaLB.grid(row=1, column=0)
        self.neuNlB.grid(row=2, column=0)
        self.novLB.grid(row=3, column=0)
        self.runB.grid(row=4, column=0)

        # column 1
        self.novaConB.grid(row=0, column=1)
        self.novaCB.grid(row=1,column=1)
        self.novDB.grid(row=2, column=1)
        self.novSB.grid(row=3, column=1)
        self.novaBA.grid(row=4,column=1)

        # column 2
        self.hotGB.grid(row=0, column=2)
        self.hotRB.grid(row=1, column=2)
        self.staLB.grid(row=2, column=2)
        self.staDB.grid(row=3, column=2)
        self.pollB.grid(row=4, column=2)

        # column 4
        self.selB.grid(row=0,  column=4)
        self.netCB.grid(row=1, column=4)
        self.vncCB.grid(row=2, column=4)

        self.varfm.pack(side=LEFT)
        self.bufm1.pack(side=LEFT)
        self.bframe.pack(side=LEFT)

        self.quitfm = Frame(self.top)
        self.clearB = Rbut(self.quitfm, 'Clear All', self._clear_all)

        self.quitB = Rbut(self.quitfm, 'Quit', self.top.quit)
        self.quitB.pack(fill=X, side=RIGHT)
        self.clearB.pack(fill=X, side=RIGHT)
        self.quitfm.pack(side=RIGHT)

        # finally print the welcome screen
        for l in initial_screen:
            self.print_line(l)
        # print any startup messages
        self._print_mess(self.messages)
        # check for valid credential
        self._cred_check()
        # run auth_check
        self._auth_check()
######################################## end of frame

    def _debug(self, stuff):
        if DEBUG:
           print(str(stuff))
           self.print_line(str(stuff))
            
    def _get_creds(self):
        cb = CredBox(self.top)
#        self._debug(cb.result)
        # try captures exception on cancel
        try:
            for key in cb.result.keys():
                if cb.result[key]:
                    os.environ[key] = cb.result[key]
                    if key == 'OS_PASSWORD':
                        self._debug('env key[%s] val[<redacted>]' % key)
                    else:
                        self._debug('env key[%s] val[%s]' % (key, os.environ[key]))
                else:
                    try:
                        del os.environ[key]
                    except:
                        pass
            try:
                self.siteOVar.set(os.environ['OS_REGION_NAME'])
            except:
                pass
            try:
                if 'OS_PROJECT_NAME' in os.environ.keys():
                    os.environ['OS_TENANT_NAME'] = os.environ['OS_PROJECT_NAME']
                    self.userV.set('Project:' + os.environ['OS_PROJECT_NAME'])
                else:
                    self.userV.set('Project:' + os.environ['OS_TENANT_NAME'])
            except:
                pass
            try:
                if os.environ['OS_TENANT_ID'] == 'Optional':
                    del os.environ['OS_TENANT_ID']
            except:
                pass
#                self._get_creds()
        except:
            self.print_line('Login cancelled.')

    def _key_error(self,key):
        print("Your environment is missing '%s'" % key)

    def _cred_check(self):
        print "_cred_check()"
        er_msg = ['Notice: No rc file has been sourced.',
                  'you can either:',
                  'a) source an rc file prior to starting rainbow',
                  '-  or  -',
                  'b) enter your credentials.']
        for key in ['OS_USERNAME', 'OS_PASSWORD', 'OS_AUTH_URL' ]:
            if key not in os.environ.keys():
                self._clear()
                for l in er_msg:
                    self.print_line(l)
                self._key_error(key)
                self._get_creds()
                break
#            if not len(os.environ[key]):
#                self._clear()
#                for l in er_msg:
#                    self.print_line(l)
#                self._get_creds()
#                break

    def _auth_check(self):
        self.print_line("Initializing auth check...")
        # check for valid AUTH_URL
        if 'OS_AUTH_URL' not in os.environ.keys():
            self.print_line('Warning: OS_AUTH_URL not set - source rc file or login to continue..')
            return
        if 'v3' in os.environ['OS_AUTH_URL']:
            print "using v3 auth.."
            if (not os.environ.get('OS_PROJECT_ID')) and (not os.environ.get('OS_PROJECT_NAME')):
                self._key_error('OS_PROJECT_ID or OS_PROJECT_NAME')
                return
        else:
            print "using v2 auth.."
            if (not os.environ.get('OS_TENANT_ID')) and (not os.environ.get('OS_TENANT_NAME')):
                self._key_error('OS_TENANT_ID or OS_TENANT_NAME')
                return

        try:
            self.ksclient = get_keystone_client()
            if check_keystone():
                self.print_line("Auth check: PASS")
        except Exception as e:
            self.print_line('Auth check: FAIL [%s]' % e)
            # future - popup to ask to confirm password..

    def _print_mess(self,mess):
        """ print a list of messages """
        for m in mess:
            self.print_line(m)

    def _set_site(self, *args):
        try:
            os.environ['OS_REGION_NAME'] = self.siteOVar.get()
            # set the header label
            self.siteV.set('Site:%s' % self.siteOVar.get())
        except:
            os.environ['OS_REGION_NAME'] = None
        self.labelfm.update()
        return os.environ['OS_REGION_NAME']

    def _get_site_list(self, fname):
        """ get_site_list  import the site list from the config

            @param /path/to/filename
            @returns list of sites
        """
        self._debug('reading site list[%s]' % fname)
        slist = []
        if os.environ['OS_REGION_NAME']:
           slist.append(os.environ['OS_REGION_NAME'])
        sites = read_list_file(fname)
        for s in sites:
            self._debug('site[%s]' % s)
            slist.append(s)
        return slist

    def update_status(self, stuff):
        self.Status = stuff
        self.statuslb.insert(END, str(ct()) + ":" + self.Status)
        self.statuslb.see(END)
        self.top.update()
        return

    def parse_args(self):

        try:
            os.environ['OS_TIMEOUT']
        except:
            os.environ['OS_TIMEOUT'] = '5'
            print('setting default timeout to [%s]' % os.environ['OS_TIMEOUT'])

        # if OS_REGION_NAME is unset just pront a warning
        if 'OS_REGION_NAME' not in os.environ.keys():
            # set the status since the frame is not built yet
            self.messages.append('Warning: OS_REGION_NAME is not set - using default site')
            os.environ['OS_REGION_NAME'] = 'None'

        self.ap.add_argument('-p', '--poll',
                             default=0,
                             help='max poll attempts'
                            )

        self.ap.add_argument('-s', '--sites',
                             action='store_true',
                             default='site.list',
                             help='sitelist file'
                            )

        self.ap.add_argument('-d', '--debug',
                             action='store_true',
                             default=False,
                             help='Show debugging output'
                            )
        return self.ap.parse_args()

    def _cancel(self):
        return self.runit(self.noOp)

    def _selectbind(self,obj):
        # get the offset between the display and the list length
        del self.multiSelect[:]
        self.vm = None
        firstIndex = None
        if not self.offset:
            self.offset = int(self.statuslb.size() - len(self.toplist))
        try:
            firstIndex = self.statuslb.curselection()[0]
            self.value = self.toplist[int(firstIndex-self.offset)]
            print("index [%s]" % str(firstIndex))
            print("value [%s]" % self.value)
            print("chose [%s]" % str(self.toplist[int(firstIndex)-self.offset]))
            self.typelist[self.type] = self.value
            self.activeVar.set(self.value)
        except IndexError:
            print("IndexError list len [%s] index [%s]" % (str(len(self.toplist)), str(firstIndex)))
            self.print_line("Selection out of range. Select from list.")
            self.value = None

        return

    def _select(self):
        """ _select - choose one or more lines from status listbox

            @params

            @returns nothing - sets value in self
        """
        firstIndex = None
        self.vm = None
        self._debug('choosing..')
        # get the offset between the display and the list length
        if not self.offset:
            self.offset = int(self.statuslb.size() - len(self.toplist))
        print('toplist %s' % len(self.toplist))
#        if len(self.toplist) == 1:
#            self.print_line('Single entry returned.')
#            self.print_line('Clear Filter and/or item field if larger list desired')
        try:
            lines = self.statuslb.curselection()
            firstIndex = lines[0]
            self.value = self.toplist[int(firstIndex-self.offset)]
            print("index [%s]" % str(firstIndex))
#                print("value [%s]" % self.value)
            print("top value [%s]" % str(self.toplist[int(firstIndex)-self.offset]))
            self.activeVar.set(self.value)
#            else:
            self.print_line("[%s] lines selected" % len(lines))
            self.multiSelect = []
            for l in lines:
                self.multiSelect.append(self.toplist[int(l)-self.offset])
            for m in self.multiSelect:
                self.print_line(m)
        except IndexError:
            print("IndexError list len [%s] index [%s]" % (str(len(self.toplist)), str(firstIndex)))
            self.print_line("IndexError [%s]: run <App> List before selecting." % str(firstIndex))
            self.value = None

    def _get_vnc_console(self):
        """ open a vnc console to a give instance

            @params self
            @ vars self.vm.id (instance id)
            @returns nothing
        """

        try:
            iid = self.vm.id
        except:
            try:
                iid = self.novaLV.get()
            except:
                self.print_line("ERROR: id not set. Run nova list and select an instance.")
                return 0

        if not len(iid):
            self.print_line('Instance id not set or instance deleted.')
            return
        self.print_line('Querying ID [%s]' % iid)
        gv = GetVnc(iid)
        gv.open_vnc_console()
        

    def _nova_show(self):
        try:
            iid = self.vm.id
        except:
            try:
                iid = self.novaLV.get()
            except:
                self.print_line("ERROR: id not set. Run nova list and select an instance.")
                return 0

        if not len(iid):
            self.print_line('Instance id not set or instance deleted.')
            return
        self._clear()
        self.print_line('Querying ID [%s]' % iid)

        sn = ShowNova(iid)
        for key in sorted(sn.info.keys()):
            try:
                self.print_line('|%s|%s|' % (str(key).ljust(40), str(sn.info[key]).ljust(40)))
            except KeyError:
                pass

    def _poll(self):
        self.add_header('---------[Polling]---------')
        self.pollVar = True
        try:
            nid = self.vm.id
        except:
            try:
                nid = self.novaLV.get()
            except:
                self.print_line("ERROR: id not set. Run nova list and select an instance.")
                self.pollVar = False
                return 0
        pcnt = 0
        while self.pollVar:
            pcnt += 1
            try:
                if not len(nid):
                    raise ValueError('Instance id not set or instance deleted.')
                self.print_line('Polling for ID [%s]' % nid)
                self.vm = poll(id=nid)
                self.status = self.vm.status
                self.print_line('%s|%s|%s|%s' %
                                (int(ut()),
                                 self.vm.id,
                                 self.status.ljust(8),
                                 self.vm.name
                                )
                               )
                if self.status != 'BUILD':
                     self.pollVar = False
            except:
                e = sys.exc_info()[0]
                m = 'Instance id not set or instance deleted.'
                self.print_line('[%s]%s' % (e.message, m))
                self.vm = None
                self.novaLV.set('')
                self.pollVar = False
        if pcnt == self.poll_count_max:
            self.print_line('Reached poll_count_max [%s]' % self.poll_count_max)
            self.pollVar = False
        return

    def _clear(self):
        self.offset = 0
        self.statuslb.delete(0, END)

    def _clear_all(self):
        self._clear()
        self.activeVar = None
        self.pollVar = False
        self.netIdVar.set('')
        self.filterVar.set('')
        self.imageVar.set('')
        self.flaVar.set('')
        self.novaLV.set('')
        self.cmndV.set('')
        self.cntVar.set(1)
        return

    def print_line(self, stuff):
        self.Status = stuff
        self.statuslb.insert(END, self.Status)
        self.statuslb.see(END)
        self.top.update()
        return

    def add_header(self, stuff):
        self.Status = stuff
        self.statuslb.insert(END, self.Status)
        self.statuslb.see(END)
        self.top.update()
        return


    def validate(self):
        """ validate - check the minimum boot requirements

            @params: none

            @returns bool the truth will set you free! (to launch)
        """
        if not len(self.imageVar.get()):
            self.glaIl()
            if len(self.toplist):
                showinfo('No Image selected', 'Please select Image.')
            return 0
        elif not len(self.netIdVar.get()):
            self.neuNl()
            if len(self.toplist):
                showinfo('No Network selected', 'Please select Network.')
            return 0
        elif not len(self.flaVar.get()):
            self.flaList()
            if len(self.toplist):
                showinfo('No Flavor selected', 'Please select Flavor.')
            return 0
        # if we got here - all's good
        return 1
	    
    def _net_create(self):
        mess = ['Note: Create will fail in sites where more than',
                'the defaults are required to create a network.',
                'Manually confirm failure.'
               ]
        self._clear()
        self.add_header('---------[Neutron net create]---------')
        newnets = []
        try:
            name = 'RainbowNet-' + str(int(ut()))
            nn = NetName(self.top, title = 'Net Name', netname = name)
            self.nname = nn.get_name()
            if len(self.nname) == 0:
                self.print_line('---------[Net Create Cancelled]---------')
                return
            self.print_line('Creating network..')
            nid = create_named_net(self.nname)
            self.netIdVar.set(nid)
            newnets.append(self.nname)
        except Exception as e:
            self.print_line(e)
            self.netIdVar.set('')
            return 0
#        num = int(num)-1
        nl = neutron_net_list()
        for i in nl['networks']:
            if i['name'] in newnets:
                self.print_line('|%s|%s|%s' % (i['id'], i['status'].ljust(8), i['name']))
        if len(self.netIdVar.get()):
            return 1
        else:
            self._print_mess(mess)
        return 0
	    
    def _net_delete(self):
        self.add_header('---------[Neutron net delete]---------')
        count = len(self.multiSelect)
        if not count:
            try:
                self.multiSelect.append(self.netIdVar.get())
                count = 1
            except Exception as e:
                self.print_line(e)
            if not len(self.multiSelect[0]):
                self.print_line("No Network selected")
                return
        if not askyesno('Confirm', 'Delete ' + str(count) + ' networks?'):
            self.print_line('Delete cancelled.')
            return
        for net in self.multiSelect:
            if not len(net): continue
            self.print_line('Deleting network [%s]' % net)
            try:
                delete_network(net)
                self.print_line('instance id [%s] delete scheduled' % net)
            except Exception as e:
                self.print_line(e)
        self.netIdVar.set('')
        del self.multiSelect[:]
        self.print_line('-------- Deletion(s) complete --------')

    def _nova_delete(self):
        self.add_header('---------[Nova delete]---------')
        count = len(self.multiSelect)
        if not count:
            try:
                count = 1
                self.multiSelect.append(self.novaLV.get())
            except Exception as e:
                self.print_line(e)
        if not len(self.multiSelect[0]):
            self.print_line("No Instance selected")
            return
        self.print_line('[%s] instance(s) in list' % count)
        if not askyesno('Confirm', 'Delete ' + str(count) + ' instance(s)?'):
            self.print_line('Delete cancelled.')
            return
        for i in self.multiSelect:
            self.print_line('Deleting instance id [%s]' % i)
            try:
                nova_delete(i)
                self.print_line('instance id [%s] delete scheduled' % i)
            except Exception as e:
                self.print_line(e)
                self.novaLV.set('') 
        del self.multiSelect[:]
        self.print_line('-------- Deletion(s) complete --------')
        return
            
    def nova_console(self):
        self.add_header('---------[Nova console]---------')
        nid = None
        try:
            nid = self.novaLV.get()
        except:
            self.print_line('Console log pull failed..')
            self.print_line('No instance selected. input id or run \'Nova List\'')
        try:
            lines = get_console_out(nid).split('\n')
            # if we got back an error object and not
            # a chunk of plain text say something
            try:
                self.print_line('Console log pull failed. [%s]' % lines.message)
            except:
                for l in lines:
                    self.print_line(l)
        except:
            e = sys.exc_info()[0]
            self.print_line('Console log pull failed [%s]' % e.message)
            
    def nova_list(self):
        self._clear()
        self._set_site()
        self.add_header('---------[Nova List]---------')
        del self.multiSelect[:]
        self.print_line('Retrieving list..')
        #del self.toplist[:]
        self.toplist = []
        nlist = get_nova_list()
        if len(self.novaLV.get()):
            p = re.compile(self.novaLV.get(), re.IGNORECASE)
        elif len(self.filterVar.get()):
            p = re.compile(self.filterVar.get(), re.IGNORECASE)

        for i in nlist:
            try:
                if not p.match(i.id) and not p.findall(i.name):
                    continue
            except:
                pass
            self.toplist.append(i.id)
            # NOTE: if there are mutiple interfaces only the first one is displayed
            try:
                net_addr = i.networks.values()[0][0]
            except:
                net_addr = "Not Defined"
            self.print_line('|%s|%s|%s|%s' % (i.id, i.status.ljust(9), str(i.name.encode('utf-8')), 
                net_addr))
        # say something if we got nothing back
        if not len(self.toplist):
            self.print_line('Query returned [0] instances.')
            self.novaLV.set('')
        self.activeVar = self.novaLV
        return

    def nova_boot_all(self):
        """  nova_boot_all - create an instance on every hypervisor

             @params: none - gets data from gui selection process

             @ side effects - sets self.novaLV
             @returns: the id of the instance
        """
        nid = None
        self._clear()
        self.filterVar.set('')
        self.add_header('---------[Nova Boot All Hypervisors]---------')
        self.print_line('NOTE: Boot All will attempt to boot on all hypervisors.')
        self.print_line('      To build on a specific hypervisor or rack, enter')
        self.print_line('      full or partial name in the [Host Filter] field.')
        self.print_line('')
        self.print_line('      To Cancel use the [Clear All] button to')
        self.print_line('      interrupt the process.')
        if len(self.multiSelect) > 0:
            showinfo('Note','multiple selection not supported for this function')
            del self.multiSelect[:]
        if not self.validate():
            return
        self.bootName = "bootall-"
        bb = BootAllBox(self.top, title = 'Boot All Hypervisors', bootName = self.bootName)
        # when cancel is hit handle exception
        self.bootName = bb.get_name()
        self.data = bb.get_data()
        self.filterVar.set(bb.get_filter())
        if  self.bootName is None:
            self.print_line('-------------[Boot Cancelled]-------------')
            return
        if self.data:
            self.print_line('Selected user data [' + self.data + ']')
        
        
        self.print_line('Getting hypervisor list...')
        hlist = get_hypervisor_list()
        filtered_list = filter_list(self.filterVar.get(), hlist)
        if len(filtered_list):
            filtered_list.sort()
            for h in filtered_list:
                #self.print_line('building on [' + h + ']')
                nid = self._create_factory(self.data, h)
                if not nid:
                    self.print_line('Build on [' + h + '] failed - cancelling builds.')
                    break
            self.print_line('-------------[Builds Completed]----------------')
            self.novaLV.set(nid)
        else:
            self.print_line('Filtered list returned Zero results.')
            return


    def nova_boot(self):
        """  nova_boot - create an instance

             @params: none - gets data from gui selection process

             @ side effects - sets self.novaLV
             @returns: the id of the instance
        """
        nid = None
        self._clear()
        self.add_header('---------[Nova Boot]---------')
        if len(self.multiSelect) > 0:
            showinfo('Note','multiple selection not supported for this function')
            del self.multiSelect[:]
        if not self.validate():
            return

        self.bootName = "rainbow-" + str(int(ut()))
        bb = BootBox(self.top, title = 'Nova Boot', bootName = self.bootName)
        # when cancel is hit handle exception
        self.bootName = bb.get_name()
        if  self.bootName is None:
            self.print_line('-------------[Boot Cancelled]-------------')
            return
        self.data = bb.get_data()
        self.cntVar.set(int(bb.get_count()))

        nid = self._create_factory(self.data)
        self.novaLV.set(nid)

    def _create_factory(self, data = None, hypervisor = None):
        """ _create_factory - backend to support generic builds as 
                              well as builds directed to specific
                              hypervisors for 'build all' ops

            @params: all common build params are set in GUI vars
                     data (Default: None) is a file object as set in the
                     BootAllBox class of novaSimpl
                     hypervisor (Default: None) the name of the
                     hypervisor as returned form nova

            @returns: the uui of the instance created
        """
        create_args = {'name': self.bootName,
                       'net_id': self.netIdVar.get(),
                       'image_id': self.imageVar.get()}
        # accept direct user output if the flavors aren't listed
        try:
            create_args['flavor_id'] = self.flavors[self.flaVar.get()]
        except:
            create_args['flavor_id'] = get_flavor_byname(self.flaVar.get())
        try:
            create_args['availability_zone'] = 'Default:' + hypervisor
            create_args['name'] = self.bootName + hypervisor
        except:
            pass
        try:
            # create dialog for cntVar
            create_args['num_instances'] = int(self.cntVar.get())
        except:
            self.cntVar.set(1)
        if data:
            #self.print_line('adding userdata [' + data + '] to args.')
            try:
                userdata = open(data)
                # pass the file type object to nova
                create_args['userdata'] = userdata
            except IOError as e:
                self.print_line('user data open failed - cancelling build.')
                self.print_line(str(e))
                raise IOError("Can't open file '%s': %s" %
                                          (data, e))
        if hypervisor:
            self.print_line('Building on [' + hypervisor + ']')
            try:
                self.print_line('userdata = %s' % (str(create_args[userdata].name)))
            except:
                pass
        else:
            for k in create_args.keys():
                # handle file object if present
                if 'userdata' in k:
                    self.print_line('%s = %s' % (k, str(create_args[k].name)))
                    print '%s = %s' % (k, str(create_args[k].name))
                else:
                    self.print_line('%s = %s' % (k, str(create_args[k])))
                    print '%s = %s' % (k, str(create_args[k]))
        start = int(ut())
        try:
            self.vm = nova_create(**create_args)
        except Exception as e:
            self.print_line('%s:ERROR: %s' % (__name__,str(e.message)))
            self.print_line("Nova Boot Failed")
            return
        try:
            dataobj.close()
        except:
            pass # fail silently
        d = int(ut()) - start
        try:
            nid = self.vm.id
            print '\n\nPoll for status. Elapsed time [' + str(d) + '] seconds.\n\n'
            self.update_status('instance id[%s] launched' % nid)
            self.update_status('Poll for status. Elapsed time [' + str(d) + '] seconds')
        except:
            print '\n\nFAIL Elapsed time [' + str(d) + '] seconds.\n\n'
            self.update_status('FAIL Elapsed time [' + str(d) + '] seconds')

        return nid

    def glaIl(self):
        self._clear()
        self.add_header('---------[Searching for all images]---------')
        if len(self.multiSelect) > 0:
            showinfo('Note','multiple selection not supported for this function')
            del self.multiSelect[:]
        self._set_site()
        self.type = 'Image'
        self.toplist = []
        glist = glance_image_list()
        if len(self.imageVar.get()):
            p = re.compile(self.imageVar.get(), re.IGNORECASE)
        elif len(self.filterVar.get()):
            p = re.compile(self.filterVar.get(), re.IGNORECASE)

        self._clear()
        self.add_header('---------[Glance Image List]---------')
        # reset the filter
        self.activeVar = self.imageVar
        for i in glist:
            try:
                if not p.match(i['id']) and not p.findall(i['name']):
                    continue
            except:
                pass
            self.toplist.append(i['id'])
            if 'name' not in i.keys():
                i['name'] = 'Undefined'
            #self.print_line('|%s|%s|%s' % (str(i['id']), i['status'], str(i['name'].encode('utf-8'))))
            try:
              self.print_line('|%s|%s|%s' % (str(i['id']), i['status'], str(i['name'].encode('utf-8'))))
            except:
              pass
            
        if not len(self.toplist):
            self.print_line('Query returned [0] images.')
        return

    def neuNl(self):
        self._clear()
        self.add_header('---------[Network List]---------')
        del self.multiSelect[:]
        self._set_site()
        self.type = 'Net'
        #del self.toplist[:]
        self.toplist = []
        nl = neutron_net_list()
        for i in nl['networks']:
            if len(self.netIdVar.get()):
                p = re.compile(self.netIdVar.get(), re.IGNORECASE)
                if not p.match(i['id']) and not p.match(i['name']):
                    continue
            elif len(self.filterVar.get()):
                p = re.compile(self.filterVar.get(), re.IGNORECASE)
                if not p.match(i['id']) and not p.match(i['name']):
                    continue
            self.toplist.append(i['id'])
            self.print_line('|%s|%s|%s' % (i['id'], i['status'].ljust(8), i['name']))
#        if len(self.toplist) == 1:
#            self.print_line('Single entry returned.')
#            self.print_line('Clear Filter and/or \'Net ID\' field if larger list desired')
        self.activeVar = self.netIdVar
        if not len(self.toplist):
            self.print_line('Query returned [0] networks.')
        return

    def flaList(self):
        self.flavors = {}
        self._clear()
        self.add_header('---------[Flavor List]---------')
        self.add_header('Command [nova flavor-list]')
        if len(self.multiSelect) > 0:
            showinfo('Note','multiple selection not supported for this function')
            del self.multiSelect[:]
        self._set_site()
        self.type = 'Fla'
        #del self.toplist[:]
        self.toplist = []
        toplist = get_flavor_list()
        for i in toplist:
            self.flavors[i.name] = i.id
            if len(self.filterVar.get()):
                p = re.compile(self.filterVar.get(), re.IGNORECASE)
                if not p.match(i.id) and not p.findall(i.name):
                    continue
            self.toplist.append(i.name)
            self.print_line('|%s|%s' % (i.id.ljust(36), i.name))
        self.activeVar = self.flaVar
        if not len(self.toplist):
            self.print_line('Query returned [0] flavors.')
            if len(self.filterVar.get()):
                self.print_line('Clearing filter and running again...')
                self.filterVar.set('')
                self.flaList()

    def novOp(self):
        self.add_header('---------[Nova]---------')
        self.add_header('Command [nova list]')
        self._set_site()
        count = self.runit(check_nova_api)
        if not count:
            self.print_line('Clear all and try again or create an instance to confirm')
        self.print_line("Nova API test found [%s] instances" % count)
        return count

    def glaOp(self):
        self.add_header('---------[Glance]---------')
        self.add_header('Command [glance image-list]')
        self._set_site()
        count = self.runit(check_glance_api)
        self.print_line("Glance API test found [%s] public images" % count)
        return count

    def cinApiOp(self):
        self.add_header('---------[Cinder API]---------')
        self.add_header('Command [cinder list]')
        self._set_site()
        start = ut()
        count = self.runit(check_cinder_api)
        #count = check_cinder_api()
        self.print_line("Cinder API test found [%s] volumes" % count)
        if not count:
            self.print_line("running cinder create")
            self.vol = cinder_create()
            while self.vol.status == 'creating':
                self.print_line('Polling volume [%s]' % self.vol.name)
                self.vol = cinder_poll(self.vol)
                self.print_line('|%s|%s|%s' % (self.vol.id, self.vol.status, self.vol.name))
            d = int(ut() - start)
            if self.vol.status == 'available':
                self.print_line('PASS Elapsed time [' + str(d) + '] seconds.')
                # >0 for pass
                return 1
            else:
                self.print_line('Fail Elapsed time [' + str(d) + '] seconds.')
            self.print_line('deleting volume [%s]' % self.vol.name)
            cinder_delete(self.vol)

        return count

    def cinOp(self):
        self.add_header('---------[Cinder]---------')
        self.add_header('Command [cinder list]')
        self._set_site()
        rc = self.runit(check_cinder_api)
        self.print_line("Cinder: Test complete..")
        return rc

    def neuOp(self):
        self.add_header('---------[Neutron]---------')
        self.add_header('Command [Neutron net-list]')
        self._set_site()
        count = self.runit(check_neutron_api)
        self.print_line("Neutron API test found [%s] networks" % count)
        return count

    def keyOp(self):
        self.add_header('---------[Keystone]---------')
        self.add_header('Command [keystone catalog]')
        self._set_site()
        rc = self.runit(check_keystone)
        self.print_line("Keystone: Test complete..")
        return rc

    def allOp(self):
        self.add_header('---------[Running all API tests]---------')
        self._set_site()
        my_results = {'keystone': self.keyOp(),
                      'nova': self.novOp(),
                      'glance': self.glaOp(),
                      'cinder': self.cinApiOp(),
                      'neutron': self.neuOp()}
        self.print_line("Summary:")
        for key in my_results.keys():
            print '%s [%s]' % (key, my_results[key])
            if my_results[key] <= 0:
                self.print_line('%s: FAIL' % key)
            else:
                self.print_line('%s: PASS' % key)
        self.add_header('-------------[Testing Complete]------------')


    def _hot_gen(self):

        hg = HotGen(self.top)
        hb = HotBox(self.top, title = 'Stack Data')
        self._clear()
        self.print_line('-----------[Begin Template Generation]------------')
        try:
            hg.set_image(self.imageVar.get())
            hg.set_net(self.netIdVar.get())
            hg.set_flavor(self.flaVar.get())
            hg.set_count(hb.get_count())
            hg.set_volume_size(hb.get_size())
        except:
            pass
        if hg.invalid():
            verr = hg.get_val_error()
            for e in verr:
                self.print_line(verr[e])
            self.print_line('-----------[Cancelling Template Generation]------------')
            return
        else:
            self.print_line("Hot Gen Valid")

        # print variables for review
        self.print_line("Template data:")
        self.print_line('-------------------------------------------------------')
        self.print_line('image: %s' % hg.imageV.get())
        self.print_line('flavor: %s' % hg.flaV.get())
        self.print_line('network: %s' % hg.netV.get())
        self.print_line('Instances: %d' % hg.countV.get())
        self.print_line('Volume size: %d' % hg.volSize)
        self.print_line('-------------------------------------------------------')

        

        hotFile = hg.get_filename()
        self._debug("file name set to [" + hotFile + "]")
        # open a dialog to confirm it.
        f = asksaveasfile(initialfile=hotFile,
                         mode='w',
                         title='Save HOT Template',
                         defaultextension=".txt")
        if f is None:
            self.print_line('-----------[Cancelling Template Generation]------------')
            return
        #self.print_line("filename [" + str(f) + "]")
        #check for template file and read it into the listbox for review

        try:
            hg.hot_gen(f)
        except:
            self.print_line('An error occured in template generation. Check console for traceback')
            pass
        self.print_line('-----------[Template Generation Complete]------------')



    def _stack_list(self):
        print "0"
        rh = RainbowHeat()
        try:
            self.print_line('Retrieving list..')
            hl = rh.stack_list()
            self._clear()
            self.offset = 3
            del self.multiSelect[:]
            self.add_header('+--------------------------------------+-----------------------+-----------------+----------------------+')
            self.add_header('| %36s | %21s | %15s | %20s |' % ('id', 'stack_name', 'stack_status', 'creation_time'))
            self.add_header('+--------------------------------------+-----------------------+-----------------+----------------------+')
            # pad the toplist for headers
            self.toplist = []
            for s in hl:
                self.toplist.append(s.id)
                self.print_line('| %36s | %21s | %15s | %20s |' %
                    (s.id,
                     s.stack_name,
                     s.stack_status,
                     s.creation_time))
            self.print_line('+--------------------------------------+-----------------------+-----------------+----------------------+')
            # share the novaLV - will change the name in the next major version?
            self.activeVar = self.novaLV
            self.activeVar.set('')
        except:
            e = sys.exc_info()[0]
            self.print_line('ERROR: %s' % e.message)
            self.print_line("Stack List Failed")

    def _stack_delete(self):
        self._clear()
        self.print_line('Deleting stack [%s]' % self.novaLV.get())
        rh = RainbowHeat()
        count = len(self.multiSelect)
        if not count:
            try:
                count = 1
                self.multiSelect.append(self.novaLV.get())
            except:
                e = sys.exc_info()[0]
                self.print_line('ERROR: %s' % e.message)
        try:
            if not askyesno('Confirm', 'Delete %s stack(s)' % count):
                self.print_line('Delete cancelled.')
                return
            for i in self.multiSelect:
                self.print_line('Deleting stack id [%s]' % i)
                try:
                    rh.stack_delete(i)
                    self.print_line('Stack id [%s] delete scheduled' % i)
                except:
                    e = sys.exc_info()[0]
                    self.print_line('ERROR: %s' % e.message)
                    self.novaLV.set('') 
            del self.multiSelect[:]
        except:
            raise
        rh.stack_list()

    def _run_hot(self):
        rh = RainbowHeat()
        f = askopenfilename(defaultextension='.yaml',title='Select Heat Template')
        if not f:
            self.print_line('Stack Create  canncelled.')
            return
        name = ''
        sn = StackName(self.top)
        name = sn.get_name()
        if name:
            self._clear()
            # offset
            del self.multiSelect[:]
            self.toplist = []
            self.activeVar = self.novaLV
            self.activeVar.set('')
            try:
                with Capture() as output:
                    rh.stack_create(f, name)
                for l in output:
                    try:
                        id = l.split('|')[1]
                    except:
                        id = "NULL"
                    self.toplist.append(id)
                    self.print_line(l)
#                for v in self.toplist:
#                    print v
            except Exception as e:
                print(e)
                self.print_line(e)
        else:
            self.print_line('Stack Create  canncelled.')


    def runit(self, app):
        """
           runit  run a function as a passed arg
        """
        rc = 0
        start = int(ut())
        print "Test in progress..."
        self.update_status('Test in progress...')

        try:
            rc = app()
            if rc == 0:
                d = int(ut()) - start
                print '\n\nPass Elapsed time [' + str(d) + '] seconds.\n\n'
                self.update_status('Pass Elapsed time [' + str(d) + '] seconds')
                self.update_status('API returned a 0 result. Manual check recommended.')
            else:
                d = int(ut()) - start
                print '\n\nPASS Elapsed time [' + str(d) + '] seconds.\n\n'
                self.update_status('PASS Elapsed time [' + str(d) + '] seconds')
                return rc
        except:
            d = int(ut()) - start
            e = sys.exc_info()[0]
            self.print_line('Error: API call failed [%s]' % e.message)
            print '\n\nFAIL Elapsed time [' + str(d) + '] seconds.\n\n'
            self.update_status('FAIL Elapsed time [' + str(d) + '] seconds')
            rc = -1
        return rc

    def run_adhoc(self):
        cmnd = self.cmndV.get()
        self.print_line('Running [%s]' % cmnd)
        out = subprocess.check_output(cmnd,
                                      stderr=subprocess.STDOUT,
                                      shell=True
                                      )
        for line in out.splitlines() :
           self.print_line(line)
        #self.print_line(out)
        self.print_line("------------[End of line]-----------")
        return

    def noOp(self):
        self.print_line("-------- Action not implemented. ----------")
        self.print_line("The time is now [%s]" % str(ct()))
    
#class BootBox(tkSimpleDialog.Dialog):
#
#
#    def __init__(self, parent, title = None, bootName = None):
#
#        self.bootName = ''
#        self.name = ''
#        self.count = 1
#        if bootName:
#            self.bootName = bootName
#        tkSimpleDialog.Dialog.__init__(self, parent, title = title)
#
#    def body(self, master):
#
#        Label(master, text="Name:").grid(row=0)
#        self.e1 = Entry(master)
#        if self.bootName:
#            self.e1.insert(0, self.bootName)
#        Label(master, text="# of instances:").grid(row=1)
#        self.e2 = Entry(master)
#        self.e2.insert(0, '1')
#        self.e1.grid(row=0, column=1)
#        self.e2.grid(row=1, column=1)
#        return self.e1 # initial focus
#
#    def apply(self):
#
#        self.name = str(self.e1.get())
#        self.count = int(self.e2.get())
#
##
#    def get_name(self):
#
#        return self.name
#
#    def get_count(self):
#
#        return self.count
#


def main():
    r = RainbowUI()
    mainloop()


if __name__ == '__main__':
    main()
