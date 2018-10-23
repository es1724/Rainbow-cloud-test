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
version = '0.5.0'

from cStringIO import StringIO
import os
import sys
import re



def read_rc(rcfile):
    print('reading [%s]' % rcfile)

def read_list_file(lfile):
    slist = []
    if not os.path.isfile(lfile):
        print('file [%s] does not exist' % lfile)
        return slist
    #print('reading [%s]' % lfile)
    lf = open(lfile)
    for line in lf:
        l =line.strip()
        if not l.startswith("#"):
            slist.append(l.rstrip())
    return slist

def filter_list(pattern, list):
    """ fiter_list(pattern) - give <pattern> return a list of
        items matching using regex
    """
    pat = re.compile(pattern)
    l = []
    for i in list:
      if pat.search(i):
        l.append(i)
    return l


class Capture(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

if __name__ == '__main__':
    l = read_list_file('site.list')
    for line in l:
        print('[%s]' % line.rstrip())
