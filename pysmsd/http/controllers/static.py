# -*- coding: utf-8 -*-

#
# pysmsd.http.controllers.static
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

from webob import Response
from webob.exc import HTTPNotModified, HTTPForbidden
from pysmsd.http.controllers import BaseController

import sys
import os
import time
import rfc822

class Static(BaseController):
    def index(self, req):
        """ Handle GET and HEAD requests for static files. Directory requests are not allowed"""
        static_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../static/'))

        # filter out ..
        try:
            static_path = req.urlvars['path'].replace('/..', '')
        except:
            return HTTPForbidden()

        path = os.path.join(static_dir, static_path) 
        if os.path.isdir(path):
            return HTTPForbidden()

        if req.method == 'GET' or req.method == 'HEAD':
            if os.path.isfile(path):
                etag, modified, mime_type, size = self._get_stat(path)

                res = Response()
                res.headers['content-type'] = mime_type
                res.date = rfc822.formatdate(time.time())
                res.last_modified = modified
                res.etag = etag

                if_modified_since = req.headers.get('HTTP_IF_MODIFIED_SINCE')
                if if_modified_since:
                    if rfc822.parsedate(if_modified_since) >= rfc822.parsedate(last_modified):
                        return HTTPNotModified()

                if_none_match = req.headers.get('HTTP_IF_NONE_MATCH')
                if if_none_match:
                    if if_none_match == '*' or etag in if_none_match:
                        return HTTPNotModified()

                # set the response body
                if req.method == 'GET':
                    fd = open(path, 'rb')
                    if 'wsgi.file_wrapper' in req.environ:
                        res.app_iter = req.environ['wsgi.file_wrapper'](fd)
                        res.content_length = size
                    else:
                        res.app_iter = iter(lambda: fd.read(8192), '')
                        res.content_length = size
                else:
                    res.body = ''

                return res
            else:
                return None
        else:
            return None
        
