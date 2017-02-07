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
#    This simply sets the mouse-over colors for buttons for us lazy ppl

Version = '0.1.2'


from Tkinter import Button


class Bbut:
    """ the blue button class """
    def __init__(self, parent, text, command):

        self.b = Button(parent,
                   text=text,
                   width = 10,
                   padx=3,
                   pady=3,
                   command=command,
                   activeforeground='white',
                   activebackground='blue'
                   )

    def pack(self, **kwargs):
        self.b.pack(**kwargs)

    def grid(self, **kwargs):
        self.b.grid(**kwargs)

class Rbut:
    """ the red button class """
    def __init__(self, parent, text, command):

        self.b = Button(parent,
                   text=text,
                   width = 10,
                   padx=3,
                   pady=3,
                   command=command,
                   activeforeground='white',
                   activebackground='red'
                   )

    def pack(self, **kwargs):
        self.b.pack(**kwargs)

    def grid(self, **kwargs):
        self.b.grid(**kwargs)

class Gbut:
    """ the green button class """

    def __init__(self, parent, text, command):

        self.b = Button(parent,
                   text=text,
                   width = 10,
                   padx=3,
                   pady=3,
                   command=command,
                   activeforeground='white',
                   activebackground='green'
                   )

    def pack(self, **kwargs):
        self.b.pack(**kwargs)

    def grid(self, **kwargs):
        self.b.grid(**kwargs)
