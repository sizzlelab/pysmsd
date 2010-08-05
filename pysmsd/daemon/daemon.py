#
# pysmsd.py
#
# Copyright 2010 Helsinki Institute for Information Technology
# and the authors.
#
# Authors: Jani Turunen <jani.turunen@hiit.fi>
#          Konrad Markus <konrad.markus@hiit.fi>
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
#

import pathhack

import time
import logging
from threading import Thread

import gammu
from pysmsd.db import db
from pysmsd.daemon.dispatcher import Dispatcher

class Daemon(object):
    def __init__(self, db_path, gammu_config, poll_delay_secs,
                 use_get_sms_status=True,
                 http=True, cherrypy=True,
                 http_host='127.0.0.1', http_port=33380,
                 ssl_cert=None, ssl_key=None):

        self.db_path = db_path
        self.poll_delay_secs = poll_delay_secs
        self.use_get_sms_status = use_get_sms_status
        self.dispatcher = Dispatcher(self.db_path)

        self.enable_http = http
        self.cherrypy = cherrypy

        self.http_host = http_host
        self.http_port = http_port

        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        # initialize phone communication
        self.init_phone(gammu_config)

        # initialize http interface
        if self.enable_http:
            self.start_http()
            time.sleep(0.2) # Give the HTTP server a little time to start up.


    def loop(self):
        try:
            while True:
                '''
                There are two approaches to fetching the incoming SMS messages, governed by use_get_sms_status.
                Use the method that works with your hardware.
                On some hardware, GetSMSStatus() wrongly reports the number of unread messages, so should not be used.
                '''
                if self.use_get_sms_status:
                    status = self.state_machine.GetSMSStatus()
                    if status['SIMUnRead'] > 0:
                        x = status['SIMUsed']
                        n = status['SIMUnRead']
                        for i in range(x, x + n):
                            self.fetch_message('SM', i)
                                
                    if status['PhoneUnRead'] > 0: 
                        x = status['PhoneUsed']
                        n = status['PhoneUnRead']
                        for i in range(x, x + n):
                            self.fetch_message('ME', i)

                else:
                    for mem in self.inboxes.keys():
                        i = 0
                        while True:
                            try:
                                m = self.state_machine.GetSMS(self.inboxes[mem], i)
                            except Exception as ex:
                                # no more messages
                                break
                                
                            if m:
                                # process the message
                                if m[0]['State'] == 'UnRead':
                                    self.fetch_message(mem, i)
                            else:
                                # no more messages
                                break

                            i = i + 1

                time.sleep(self.poll_delay_secs)
        except KeyboardInterrupt:
            self.stop()
        except Exception as ex:
            #[TODO: logging]
            logging.exception(ex)
            self.stop()

    def fetch_message(self, memory_type, i):
        # retrieve and format the message
        m = self.state_machine.GetSMS(self.inboxes[memory_type], i)
        self.state_machine.DeleteSMS(self.inboxes[memory_type], i)
        m = self.format_message(m)

        # add it to the database
        id = db.insert_in_message(self.db_path, m)

        # dispatch to any loaded handlers
        try:
            self.dispatcher.in_message(id)
        except DispatcherException as e:
            logging.exception("Dispatcher failed")

    def format_message(self, raw):
        ret = {}
        ret['Number'] = raw[0]['Number']
        ret['Text'] = raw[0]['Text']
        ret['Keyword'], ret['Rest'] = self._parse_keyword(ret['Text'])
        ret['Received'] = raw[0]['DateTime']
        ret['Length'] = raw[0]['Length']
        ret['Coding'] = raw[0]['Coding']
        return ret

    def _parse_keyword(self, text):
        (keyword, sep, rest) = text.strip().partition(' ')
        return keyword.lower(), rest

    def init_phone(self, gammu_config):
        try:
            self.state_machine = gammu.StateMachine()

            # acquire device configuration and initialize
            if gammu_config:
                self.state_machine.ReadConfig(0, 0, gammu_config)
            else:
                self.state_machine.ReadConfig()
            self.state_machine.Init()

            # save box reference into inboxes dict,
            # assumes that there is only 1 inbox for each memory type
            f = 0
            self.inboxes = { }
            folders = self.state_machine.GetSMSFolders()
            for folder in folders:
                if folder['Inbox']:
                    self.inboxes[folder['Memory']] = f
                f = f + 1
            
            logging.debug(self.inboxes)

        except KeyboardInterrupt:
            self.stop()
        except Exception as ex:
            #[TODO: logging]
            logging.exception(ex)
            self.stop()

    def start_http(self):
        from pysmsd.http.wsgiserver import serve

        args = self.db_path, self.state_machine, self.http_host, self.http_port, self.cherrypy, self.ssl_cert, self.ssl_key
        self.http_thread = Thread(target=serve, args=args,
                                  name='http-thread')
        self.http_thread.setDaemon(True)
        self.http_thread.start()

    def stop(self):
        #[TODO: clean up code here? close db etc?]
        logging.debug("Stopping")
        exit(-1)
