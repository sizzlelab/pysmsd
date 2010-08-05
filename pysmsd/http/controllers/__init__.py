# -*- coding: utf-8 -*-

#
# pysmsd.http.controllers.__init__
#
# Copyright 2010 Helsinki Institute for Information Technology
# and the authors.
#
# Authors:
#       Konrad Markus <konrad.markus@hiit.fi>
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

import cgi
import sys
import os
import re
import rfc822
import mimetypes
import gettext
import xml.sax.saxutils
from binascii import hexlify, unhexlify

from pysmsd.lib import json
from mako.lookup import TemplateLookup

class BaseController(object):
    # basically ../templates relative to the controllers directory
    BASE_TEMPLATE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.join('..', 'templates')))

    def __init__(self):
        self.lookup = TemplateLookup(directories=[BaseController.BASE_TEMPLATE_DIR], filesystem_checks=True, input_encoding='utf-8', output_encoding='utf-8', encoding_errors='replace', default_filters=['decode.utf8', 'h'])

    def load_view(self, view_name):
        return self.lookup.get_template(view_name)
                    
    def _get_mime_type(self, filename):
        if filename.endswith('.xpi'):
            return 'application/x-xpinstall'
        type, encoding = mimetypes.guess_type(filename)
        return type or 'text/plain'
    
    def _get_stat(self, path):
        mtime = os.stat(path).st_mtime
        size = os.stat(path).st_size
        return str(mtime), rfc822.formatdate(mtime), self._get_mime_type(path), str(size)

    def _sanitize(self, s):
        '''esacpes html entities'''
        return cgi.escape(s)



