#! /usr/bin/env python
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
#
#    various methods to pull credentials from environment and
#    provide some interfaces to them in the gui
#
from Tkinter import *
import tkSimpleDialog
import os
version = '0.3.0'

def set_timeout():
    if 'TIMEOUT' not in os.environ.keys():
        # set a default timeout value if not set
        os.environ['OS_TIMEOUT'] = '10'

def get_v3_creds():
    """ credentials session based auth versions. """
    #endpoint_type='publicURL'
    d = {'auth_url': os.environ['OS_AUTH_URL'],
         'password': os.environ['OS_PASSWORD'],
         'project_id': os.environ['OS_PROJECT_ID'],
         'username': os.environ['OS_USERNAME'],
         'user_domain_name': os.environ['OS_USER_DOMAIN_NAME']}
    return d

def get_v2_creds():
    d = {'username': os.environ['OS_USERNAME'],
         'password': os.environ['OS_PASSWORD'],
         'auth_url': os.environ['OS_AUTH_URL']}
    if 'OS_TENANT_NAME' in os.environ.keys():
        d['tenant_name'] = os.environ['OS_TENANT_NAME']
    elif 'OS_PROJECT_NAME' in os.environ.keys():
        d['tenant_name'] = os.environ['OS_PROJECT_NAME']
    if 'OS_TENANT_ID' in os.environ.keys():
        d['tenant_id'] = os.environ['OS_TENANT_ID']
    elif 'OS_PROJECT_ID' in os.environ.keys():
        d['tenant_id'] = os.environ['OS_PROJECT_ID']
    return d

def get_v2_session():
    from keystoneauth1.identity import v2
    from keystoneauth1 import session
    #from keystoneclient.v2_0 import client
    creds = get_v2_creds()
    auth = v2.Password(**creds)
    sess = session.Session(auth=auth)
    return sess

def get_v3_session():
    """ for v3 auth we use session for auth """
    from keystoneauth1 import loading
    from keystoneauth1 import session
    loader = loading.get_plugin_loader('password')
    creds = get_v3_creds()
    auth = loader.load_from_options(**creds)
    sess = session.Session(auth=auth)
    return sess

def get_session():
    """ for v3 auth we use session for auth """
    from keystoneauth1 import loading
    from keystoneauth1 import session
    loader = loading.get_plugin_loader('password')
    if '/v3' in os.environ['OS_AUTH_URL']:
        sess = get_v3_session()
    else:
        sess = get_v2_session()
    return sess

class CredBox(tkSimpleDialog.Dialog):
    """ popup for manual entry of credentials """

    def body(self, master):

        # 2 segments user/pass and all

        Label(master, text="User:").grid(row=0,sticky=E)
        Label(master, text="Password:").grid(row=1,sticky=E)
        Label(master, text="Project:").grid(row=2,sticky=E)
        Label(master, text="Project ID:").grid(row=3,sticky=E)
        Label(master, text="Site:").grid(row=4,sticky=E)
        Label(master, text="Auth URL:").grid(row=5,sticky=E)
        Label(master, text="Domain:").grid(row=6,sticky=E)
        self.userV = StringVar()
        self.user = Entry(master, textvariable=self.userV)
        self.paswV = StringVar()
        self.pasw = Entry(master, textvariable=self.paswV, show="*")
        self.projV = StringVar()
        self.proj = Entry(master, textvariable=self.projV)
        self.pridV = StringVar()
        self.prid = Entry(master, textvariable=self.pridV)
        self.siteV = StringVar()
        self.site = Entry(master, textvariable=self.siteV)
        self.aurlV = StringVar()
        self.aurl = Entry(master, textvariable=self.aurlV)
        self.domaV = StringVar()
        self.doma = Entry(master, textvariable=self.domaV)

        self.set_env()
        self.user.grid(row=0, column=1)
        self.pasw.grid(row=1, column=1)
        self.proj.grid(row=2, column=1)
        self.prid.grid(row=3, column=1)
        self.site.grid(row=4, column=1)
        self.aurl.grid(row=5, column=1)
        self.doma.grid(row=6, column=1)
        return self.user  # initial focus

    def set_env(self):
        if 'OS_USERNAME' in os.environ.keys():
            self.userV.set(os.environ['OS_USERNAME'])
        if 'OS_PASSWORD' in os.environ.keys():
            self.paswV.set(os.environ['OS_PASSWORD'])
        if 'OS_AUTH_URL' in os.environ.keys():
            self.aurlV.set(os.environ['OS_AUTH_URL'])
        if 'v3' in os.environ['OS_AUTH_URL']:
            if 'OS_PROJECT_NAME' in os.environ.keys():
                self.projV.set(os.environ['OS_PROJECT_NAME'])
            if 'OS_PROJECT_ID' in os.environ.keys():
                self.pridV.set(os.environ['OS_PROJECT_ID'])
            else:
                self.pridV.set('Optional')
            if 'OS_TENANT_ID' in os.environ.keys():
                self.pridV.set(os.environ['OS_TENANT_ID'])
            if 'OS_USER_DOMAIN_NAME' in os.environ.keys():
                self.domaV.set(os.environ['OS_USER_DOMAIN_NAME'])
            else:
                self.domaV.set(os.environ['OS_USER_DOMAIN_NAME'])
        else:
            if 'OS_TENANT_NAME' in os.environ.keys():
                self.projV.set(os.environ['OS_TENANT_NAME'])
            if 'OS_TENANT_ID' in os.environ.keys():
                self.pridV.set(os.environ['OS_TENANT_ID'])
            else:
                self.pridV.set('Optional')
            if 'OS_REGION_NAME' in os.environ.keys():
                self.siteV.set(os.environ['OS_REGION_NAME'])


    def apply(self):
        if 'v3' in os.environ['OS_AUTH_URL']:
            self.result = {'OS_USERNAME': self.userV.get().rstrip(),
                           'OS_PASSWORD': self.paswV.get().rstrip(),
                           'OS_PROJECT_NAME': self.projV.get().rstrip(),
                           'OS_PROJECT_ID': self.pridV.get().rstrip(),
                           'OS_USER_DOMAIN_NAME': self.domaV.get().rstrip(),
                           'OS_AUTH_URL': self.aurlV.get().rstrip()}
        else:
            self.result = {'OS_USERNAME': self.userV.get().rstrip(),
                           'OS_PASSWORD': self.paswV.get().rstrip(),
                           'OS_TENANT_NAME': self.projV.get().rstrip(),
                           'OS_TENANT_ID': self.pridV.get().rstrip(),
                           'OS_REGION_NAME': self.siteV.get().rstrip(),
                           'OS_AUTH_URL': self.aurlV.get().rstrip()}



class PassBox(tkSimpleDialog.Dialog):
    """ gui for username/password entry (deprecated) """

    def body(self, master):


        # 2 segments user/pass and all

        Label(master, text="User:").grid(row=0,sticky=E)
        Label(master, text="Password:").grid(row=1,sticky=E)
        self.userV = StringVar()
        self.user = Entry(master, textvariable=self.userV)
        self.paswV = StringVar()
        self.pasw = Entry(master, textvariable=self.paswV, show="*")
        self.set_env()
        self.user.grid(row=0, column=1)
        self.pasw.grid(row=1, column=1)

        return self.user  # initial focus

    def set_env(self):
        if 'OS_USERNAME' in os.environ.keys():
            self.userV.set(os.environ['OS_USERNAME'])
        if 'OS_PASSWORD' in os.environ.keys():
            self.paswV.set(os.environ['OS_PASSWORD'])

    def apply(self):
        self.result = {'OS_USERNAME': self.userV.get().rstrip(),
                       'OS_PASSWORD': self.paswV.get().rstrip()}


if __name__ == '__main__':
    root = Tk()
    d = CredBox(root, 'all')

    if d.result:
        print d.result
