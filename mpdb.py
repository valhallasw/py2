#!/usr/bin/env python

# Pdb Improvements
#
# This is a Google Summer of Code project
# Student: Matthew J. Fleming
# Mentor: Robert L. Bernstein
"""
This module provides improvements over the Python Debugger (Pdb) by building
on the work done by Rocky Bernstein in The Extended Python Debugger.
This module allows,

- debugging of applications running in a separate process to the debugger
- debugging of applications on a remote machine
- debugging of threaded applications.
"""

import os
from optparse import OptionParser
import pdb as pydb
from pdb.gdb import Restart
import sys
import time
import thread
import traceback

__all__ = ["MPdb", "pdbserver", "target", "thread_debugging"]
__version__ = "0.1alpha"

line_prefix = '\n-> '

class MPdb(pydb.Pdb):
    """ This class extends the command set and functionality of the
    Python debugger and provides support for,

    - debugging separate processes
    - debugging applications on remote machines
    - debugging threaded applications
    """
    def __init__(self, completekey='tab', stdin=None, stdout=None):
        """ Instantiate a debugger.

        The optional argument 'completekey' is the readline name of a
        completion key; it defaults to the Tab key. If completekey is
        not None and the readline module is available, command completion
        is done automatically. The optional arguments stdin and stdout
        are the objects that data is read from and written to, respectively.
        """
        pydb.Pdb.__init__(self, completekey, stdin, stdout)
        self.orig_stdin = self.stdin
        self.orig_stdout = self.stdout
        self.prompt = '(MPdb)'
        self.target = 'local'  # local connections by default
        self.lastcmd = ''
        self.connection = None

        # We need to be in control of self.stdin
        self.use_rawinput = False

    def _rebind_input(self, new_input):
        self.stdin = new_input

    def _rebind_output(self, new_output):
        self.stdout.flush()
        self.stdout = new_output
        if not hasattr(self.stdout, 'flush'):
            self.stdout.flush = lambda: None

    def help_mpdb(self, *arg):
        help()

    def _pdbserver_hook(self, addr):
        """This method allows a pdbserver to be created from inside the
        'default' debugger. This may be needed for instance, if this process
        receives a signal to start debugging from another process.
        """
        mpdb.pdbserver(addr, self)

def pdbserver(addr, m):
    """ This method sets up a pdbserver debugger that allows debuggers
    to connect to 'addr', which a protocol-specific address, i.e.
    tcp = 'tcp mydomainname.com:9876'
    serial = 'serial /dev/ttyC0'
    """
    from mremote import RemoteWrapperServer
    m = RemoteWrapperServer(m)
    m.do_pdbserver(addr)
    while True:
        try:
            m._runscript(m.mainpyfile)
            if m._user_requested_quit: break
        except Restart:
            sys.argv = list(m._program_sys_argv)
            m.msg('Restarting')

# The value of 'opts' dictates whether we call do_target or do_attach, there
# were two separate top-level routines for these options, but apart from
# choosing which do_* to call, the code was the same so it made sense to merge.
def target(addr, opts, mpdb):
    """ Connect this debugger to a pdbserver at 'addr'. 'addr' is
    a protocol-specific address. i.e.
    tcp = 'tcp mydomainname.com:9876'
    serial = 'serial /dev/ttyC0'

    'opts' an the OptionParser object. If opts.target is True, call do_target.
    If opts.pid is true, call do_attach.
    """
    if opts.target:
        from mremote import RemoteWrapperClient
        mpdb = RemoteWrapperClient(mpdb)
        mpdb.do_target(addr)
    elif opts.pid:
        from mproc import ProcessWrapper
        mpdb = ProcessWrapper(mpdb)
        pid = addr[:addr.find(' ')]
        addr = addr[addr.find(' ')+1:]
        mpdb.do_set('target ' + addr)
        mpdb.do_attach(pid)
    while True:
        try:
            mpdb.cmdloop()
            if mpdb._user_requested_quit: break
        except:
            break

def thread_debugging(m):
    """ Setup this debugger to handle threaded applications."""
    import mthread
    mthread.init(m)
    while True:
        try:
            m._runscript(m.mainpyfile)
            if m._user_requested_quit: break
        except Restart:
            sys.argv = list(m._program_sys_argv)
            m.msg('Restarting')
        except:
            m.msg(traceback.format_exc())
            break

# Moving this out of this file makes things 'awkward', for instance
# the outter file has to know about how to setup a pdbserver.
def process_debugging(sig=None, protocol=None, addr=None):
    """ Allow debugging of other processes. This routine should
    be imported and called near the top of the program file.
    It sets up signal handlers that are used to create a pdbserver
    that a debugging client can attach to. The address of the pdbserver
    is returned a string.

    The optional argument 'sig', specifies which signal will be
    used for running process debugging. If 'sig' is not specified
    the SIGUSR1 signal is used. The optional argument 'protocol' is
    the protocol used to create a pdbserver. The optional argument 'addr'
    is the address used to create a pdbserver. The argument must
    containa protocol and protocol-specific address. See the
    docstring for pdbserver and target for more details.
    """
    import signal
    if not sig:
        sig = signal.SIGUSR1

    # Save the old signal handler
    global old_handler

    # Set up the new signal handler
    old_handler = signal.signal(sig, signal_handler)

    global pdbserver_addr

    if protocol is not None:
        proto = protocol
    else:
        proto = 'mconnection.MConnectionServerFIFO'
        
    if addr is not None:
        pdbserver_addr = proto + " " + addr
    else:
        from tempfile import gettempdir
        tmp = gettempdir() + "/" + str(os.getpid()) + "mpdb"
        pdbserver_addr = proto + " " + tmp
    return pdbserver_addr

def signal_handler(signum, frame):
    """ This signal handler replaces the programs signal handler
    for the 'signum' signal (by default SIGUSR1). When a program
    receives this signal, it creates a pdbserver.
    Debugger clients can then attach to this pdbserver via it's pid.
    """
    m = MPdb()
    m._sys_argv = list(sys.argv)
    m.reset()
    m.running = True
    m.currentframe = frame

    # Clear up namespace
    del frame.f_globals['mpdb']

    from mremote import RemoteWrapperServer
    m = RemoteWrapperServer(m)
    m.do_pdbserver(pdbserver_addr)
    m.set_trace(frame)

    import signal
    signal.signal(signum, old_handler)
    

def main():
    """ Main entry point to this module. """
    mpdb = MPdb()
    
    from pydb.pydb import process_options
    from optparse import make_option

    opt_list = [
        make_option("-t", "--target", dest="target",
                      help="Specify a target to connect to. The arguments" \
                      + " should be of form, 'protocol address'."),
        make_option("--pdbserver", dest="pdbserver",
                      help="Start the debugger and execute the pdbserver " \
                      + "command. The arguments should be of the form," \
                      + " 'protocol address scriptname'."),
        make_option("-d", "--debug-thread", action="store_true",
                      help="Turn on thread debugging."),
        make_option("--pid", dest="pid", help="Attach to running process PID.")
        ]
        
    opts = process_options(mpdb, "mpdb", os.path.basename(sys.argv[0])
                           ,  __version__, opt_list)

    mpdb._sys_argv = list(sys.argv)

    if not sys.argv:
        # No program to debug
        mpdb.mainpyfile = None
    else:
        mpdb._program_sys_argv = list(sys.argv)

        mpdb.mainpyfile = mpdb._program_sys_argv[0]
        
        if not os.path.exists(mpdb.mainpyfile):
            print 'Error:', mpdb.mainpyfile, 'does not exist'

        # Replace mpdb's dir with script's dir in front of
        # module search path.
        sys.path[0] = mpdb.main_dirname = os.path.dirname(mpdb.mainpyfile)

    if opts.target:
        target(opts.target, opts, mpdb)
        sys.exit()
    elif opts.pdbserver:
        pdbserver(opts.pdbserver, mpdb)
        sys.exit()
    elif opts.debug_thread:
        thread_debugging(mpdb)
        sys.exit()
    elif opts.pid:
        target(opts.pid, opts, mpdb)
        sys.exit()

    while 1:
        try:
            if mpdb.mainpyfile:
                mpdb._runscript(mpdb.mainpyfile)
            else:
                mpdb._wait_for_mainpyfile = True
                mpdb.interaction(None, None)
                
            if mpdb._user_requested_quit:
                break
            mpdb.msg("The program finished and will be restarted")
        except Restart:
            if mpdb._program_sys_argv:
                sys.argv = list(mpdb._program_sys_argv)
                mpdb.msg('Restarting %s with arguments:\n\t%s'
                     % (mpdb.filename(mpdb.mainpyfile),
                        ' '.join(mpdb._program_sys_argv[1:])))
            else: break
            
        except SystemExit:
            # In most cases SystemExit does not warrant a post-mortem session.
            mpdb.msg("The program exited via sys.exit(). " + \
                  "Exit status:",sys.exc_info()[1])
        except:
            mpdb.msg(traceback.format_exc())
            mpdb.msg("Uncaught exception. Entering post mortem debugging")
            mpdb.msg("Running 'cont' or 'step' will restart the program")
            t = sys.exc_info()[2]
            while t.tb_next != None:
                t = t.tb_next
                mpdb.interaction(t.tb_frame,t)
                mpdb.msg("Post mortem debugger finished. The " + \
                      mpdb.mainpyfile + " will be restarted")

if __name__ == '__main__':
    main()


