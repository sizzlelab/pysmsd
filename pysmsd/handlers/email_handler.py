#
# pysmsd.handler.print_handler.py
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

import sys
import logging
from pysmsd.handlers import BaseSMSHandler

from pysmsd import DB_PATH
from pysmsd.db import db

import smtplib
from email.mime.text import MIMEText

class Handler(BaseSMSHandler):
    def handle(self, db_path, id):
        m = db.get_in_message(db_path, id)
        logging.debug("in message: %s" % m['keyword'])
        if self.is_email(m['keyword']):
            frm = 'turunen@prometheus.hiit.fi'
            to = m['keyword']

            logging.debug("Sending email to %s" % to)
            msg = MIMEText(m['rest'])

            msg['Subject'] = 'Email from smsd: %s' % m['rest']
            msg['From'] = frm
            msg['To'] = to

            try:
                # Send the message via our own SMTP server, but don't include the
                # envelope header.
                s = smtplib.SMTP('localhost')
                s.sendmail(frm, [to], msg.as_string())
                s.quit()
            except:
                exctype, value = sys.exc_info()[:2]
                logging.error(exctype)
                logging.error(value)
                return

            logging.debug("Sent")
            
    def is_email(self, s):
        try:
            local, domain = s.rsplit('@', 1)
            host, tld = domain.rsplit('.', 1)
        except ValueError:
            return False

        return True

if __name__ == '__main__':
    h = Handler()
    print h.is_email('konker@gmail.com')
    print h.is_email('foo bar')

    frm = 'no-reply@localhost'
    to = 'konker@prometheus.hiit.fi'
    msg = MIMEText('Test message')

    msg['Subject'] = 'Test message'
    msg['From'] = frm
    msg['To'] = to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(frm, [to], msg.as_string())
    s.quit()

