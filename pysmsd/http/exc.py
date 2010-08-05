# -*- coding: utf-8 -*-

#
# pysmsd.http.exc
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

# TODO:
#   this probably needs to be refactored somewhat.
#   also some calls to these classes are passing in a message which is being ignored.

body500 = '''{
    "response": {
        "code": 500,
        "message": "Internal Error. Please try again."
    }
}'''

body400 = '''{
    "response": {
        "code": 400,
        "message": "Bad Request"
    }
}'''

body401 = '''{
    "response": {
        "code": 401,
        "message": "Unauthorized"
    }
}'''

body404 = '''{
    "response": {
        "code": 404,
        "message": "Not Found"
    }
}'''

class HTTPErrorJSON(object):
    def __init__(self, message=None):
        #[TODO: not used currently]
        self.message = message


class HTTPInternalServerErrorJSON(HTTPErrorJSON):
    def __call__(self, environ, start_response):
        start_response('500 Internal Server Error', [('Content-type', 'application/json')])
        yield body500

class HTTPBadRequestJSON(HTTPErrorJSON):
    def __call__(self, environ, start_response):
        start_response('400 Unauthorized', [('Content-type', 'application/json')])
        yield body400

class HTTPUnauthorizedJSON(HTTPErrorJSON):
    def __call__(self, environ, start_response):
        start_response('401 Unauthorized', [('Content-type', 'application/json')])
        yield body401

class HTTPNotFoundJSON(HTTPErrorJSON):
    def __call__(self, environ, start_response):
        start_response('404 Not Found', [('Content-type', 'application/json')])
        yield body404

