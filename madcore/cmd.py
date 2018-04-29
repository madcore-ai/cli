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

from static import Static
import subprocess
import os
import sys
import time
import getpass


class Cmd(object):

    @staticmethod
    def local_run_realtime(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # Poll process for new output until finished
        while True:
            nextline = proc1.stdout.readline()
            if nextline == '' and proc1.poll() is not None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        output = proc1.communicate()

        if proc1.returncode != 0:
            Static.msg_bold("FAIL", name.upper())
            sys.stdout.write(output[1])
            raise SystemExit(32)

    @staticmethod
    def local_run_realtime_continue_on_fail(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # Poll process for new output until finished
        while True:
            nextline = proc1.stdout.readline()
            if nextline == '' and proc1.poll() is not None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        output = proc1.communicate()
        if proc1.returncode != 0:
            Static.msg_bold("FAIL {0}".format(name.upper()), output[1])

    @staticmethod
    def local_run_long(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

        while proc1.returncode is None:
            for line in proc1.stdout:
                sys.stdout.write(line)
            proc1.poll()

        if proc1.returncode != 0:
            Static.msg_bold("FAIL", name.upper())
            for line in iter(proc1.stderr.readline, ''):
                sys.stdout.write(line)
            raise SystemExit(32)

    @staticmethod
    def local_sudo_prompt_run(name, cmd):
        password = None
        if not os.geteuid() == 0:
            print
            print "You must be root to run this command."
            print
            password = getpass.getpass()
            print

        #proc1 = subprocess.Popen(['sudo', '-p', '-k', '-S', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc1 = subprocess.Popen('/usr/bin/sudo -p -k -S {0}'.format(cmd), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc1.communicate(input='{0}\n'.format(password))

        if proc1.returncode != 0:
            Static.msg_bold("Password failed most likely. Possibly some other error. Inspect below.", name.upper())
            print out
            raise SystemExit(32)


    @staticmethod
    def local_run_get_out(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        out = proc1.communicate()

        if proc1.returncode != 0:
            Static.msg_bold("FAIL", name.upper())
            sys.stdout.write(out[1])
            raise SystemExit(32)

        return out[0].replace('\n','')

    @staticmethod
    def local_run_get_out_raw(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        out = proc1.communicate()

        if proc1.returncode != 0:
            Static.msg_bold("FAIL", name.upper())
            sys.stdout.write(out[1])
            raise SystemExit(32)

        return out[0]

    @staticmethod
    def local_run_long_until_success(name, cmd):
        attempt = 1
        while attempt < 101:
            try:
                if attempt > 1:
                    Static.msg("RETRYING", "VALIDATE in 15s")
                    time.sleep(15)

                Cmd.local_run_long(name, cmd)
                return
            except:
                attempt += 1


    @staticmethod
    def local_run_long_until_ready(name, cmd):
        result = False
        while not result:
            proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
            proc1.wait()

            for line in iter(proc1.stdout.readline, ''):
                if not "ready: true" in line:
                    Static.msg("Waiting for", name.upper())
                    time.sleep(10)
                    continue

            Static.msg("Success for", name.upper())
            return

    @staticmethod
    def local_run_return_bool(name, cmd):
        proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        proc1.wait()

        if proc1.returncode == 0:
            return True
        else:
            return False

