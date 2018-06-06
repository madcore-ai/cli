"""
MIT License

Copyright (c) 2016-2018 Madcore Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import subprocess
import datetime
from termcolor import colored
#import urllib3
#import requests
#import requests.exceptions
import time


class Static(object):


    @staticmethod
    def figlet(msg):
        prov_cmd = "figlet -w 160 {0}".format(msg)
        proc = subprocess.Popen(prov_cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        out = ''
        for line in iter(proc.stdout.readline, ''):
            out += line
        print out

    @staticmethod
    def figletcyber(msg):
        prov_cmd = "figlet -f {0} {1}".format(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cybermedium.flf"), msg)
        proc = subprocess.Popen(prov_cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        out = ''
        for line in iter(proc.stdout.readline, ''):
            out += line
        print out

    @staticmethod
    def msg(in_service, in_msg):
        print colored(str(datetime.datetime.now()), 'cyan'), \
            colored(':', 'white'), \
            colored(in_service, 'yellow'), \
            colored('>>', 'white'), \
            colored(in_msg, 'green')

    @staticmethod
    def msg_bold(in_service, in_msg):
        print colored(str(datetime.datetime.now()), 'cyan'), \
            colored(':', 'white'), \
            colored(in_service, 'red'), \
            colored('>>', 'white'), \
            colored(in_msg, 'red', attrs=['bold'])

    # TO BE EDITED
    @staticmethod
    def wait_until_url_is_up(self, url, log_msg=None, verify=False, timeout=600, sleep_time=10):
        elapsed_sec = 0
        while True:
            try:
                response = requests.get(url, verify=verify, timeout=timeout)
                response.raise_for_status()
                return True
            except Exception:
                if log_msg:
                    #self.logger.info(log_msg)
                    pass
                elapsed_sec += sleep_time
                if elapsed_sec > timeout:
                    break
                time.sleep(sleep_time)

        return False

