#!/usr/bin/env python

#
# pysmsd
#
# Copyright 2010 Helsinki Institute for Information Technology
# and the authors.
#
# Authors: Jani Turunen <jani.turunen@hiit.fi>
#          Konrad Markus <konrad.markus@hiit.fi>
#          Ken Rimey <rimey@hiit.fi>
#

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import sys
import socket
import logging

if sys.version < '2.5':
    sys.exit('Python 2.5 or 2.6 is required.')

import pathhack

from pysmsd import DB_PATH
from pysmsd.daemon.daemon import Daemon

def main(**kwargs):
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option('--poll_delay_secs', type='int', default=5,
                      help='delay in seconds for polling the phone'
                           ' (default is %default)')

    parser.add_option('--use_get_sms_status', dest='use_get_sms_status', default='True',
                      help='On some hardware, GetSMSStatus() wrongly reports the number of unread messages, so should not be used.')

    parser.add_option('--gammu_config', dest='gammu_config', default='gammurc',
                      help='location of the gammu config file')

    parser.add_option('--db', dest='db_path', default=DB_PATH,
                      help='location of database (default is %default)')

    parser.add_option('--nohttp', dest='http',
                      action='store_false', default=True,
                      help='disable the web interface')
    parser.add_option('--nocherrypy', dest='cherrypy',
                      action='store_false', default=True,
                      help='do not use the CherryPy WSGI server')
    parser.add_option('--http_port', type='int', default=33380,
                      help='which port to listen to for HTTP requests'
                           ' (default is %default)')
    parser.add_option('--http_host', default='localhost',
                      help='which interface to listen to for HTTP requests'
                           ' (default is %default)')

    parser.add_option('--ssl-cert', dest='ssl_cert', default=None,
                      help='Path to ssl certificate')

    parser.add_option('--ssl-key', dest='ssl_key', default=None,
                      help='Path to ssl private key')

    parser.add_option('--debug', action='store_true', default=False,
                      help='log debugging messages too')

    parser.add_option('--log', dest='logfile',
                      help='where to send log messages')

    options, args = parser.parse_args()
    if args:
        parser.error('incorrect number of arguments')

    if options.debug:
        logging.basicConfig(level=logging.DEBUG,
                            filename=options.logfile,
                            format='%(asctime)s [%(threadName)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO,
                            filename=options.logfile,
                            format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    daemon = Daemon(db_path = options.db_path,
         gammu_config = options.gammu_config,
         poll_delay_secs = options.poll_delay_secs,
         use_get_sms_status = (options.use_get_sms_status.lower() == 'true'),

         http = options.http,
         cherrypy = options.cherrypy,
         http_host = options.http_host,
         http_port = options.http_port,
         ssl_cert = options.ssl_cert,
         ssl_key = options.ssl_key)
    daemon.loop()


if __name__ == '__main__':
    main()
