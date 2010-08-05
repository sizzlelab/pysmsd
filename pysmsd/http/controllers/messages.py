# -*- coding: utf-8 -*-

#
# pysmsd.http.controllers.messages
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

from __future__ import with_statement

import cgi
from webob import Response
from pysmsd.http.exc import HTTPBadRequestJSON 
from pysmsd.http.controllers import BaseController
from pysmsd.db import db


class Messages(BaseController):
    def in_message(self, req):
        #[TODO: should this be PUT?]
        if req.method == 'POST':
            view = self.load_view('ok.json')
            if view:
                db.mark_messages(req.environ['pysmsd.db.path'], req.environ['pysmsd.client.id'], req.urlvars['id'])
                return view.render()
            else:
                return None
        else:
            # GET
            view = self.load_view('message.json')
            if view:
                v = {}
                v['message'] = {}
                message = db.get_in_message(req.environ['pysmsd.db.path'], id=req.urlvars['id'])
                for k in message.keys():
                    v['message'][k] = message[k]

                return view.render(**v)
            else:
                return None


    def in_messages(self, req):
        #[TODO: should this be PUT?]
        if req.method == 'POST':
            view = self.load_view('ok.json')
            if view:
                ids = req.params.get('ids')
                if ids:
                    ids = ids.split(',')
                    db.mark_messages(req.environ['pysmsd.db.path'], req.environ['pysmsd.client.id'], ids)
                else:
                    return HTTPBadRequestJSON()

                return view.render()
            else:
                return None
        else:
            # GET
            view = self.load_view('messages.json')
            if view:
                include_marked = req.params.get('include_marked', False)
                v = {}
                v['messages'] = []
                messages = db.get_in_messages(req.environ['pysmsd.db.path'], keyword=req.GET.get('keyword'), include_marked=include_marked)
                for row in messages:
                    m = {}
                    for k in row.keys():
                        m[k] = row[k]

                    v['messages'].append(m)

                return view.render(**v)
            else:
                return None

    def out_message(self, req):
        if req.method == 'GET':
            view = self.load_view('message.json')
            if view:
                v = {}
                v['message'] = {}
                message = db.get_out_message(req.environ['pysmsd.db.path'], id=req.urlvars['id'])
                for k in message.keys():
                    v['message'][k] = message[k]

                return view.render(**v)
            else:
                return None
        else:
            return None


    def out_messages(self, req):
        if req.method == 'POST':
            view = self.load_view('ok.json')
            if view:
                # automatically (and silently) truncate to 159 chars
                # [FIXME: sends blank message when truncated to 160?]
                text = req.POST.get('text', '')
                text = text[:159]
                number = req.POST.get('number')
                replyto = req.POST.get('replyto')

                if (text and number):
                    # create message struct
                    message = {
                        'Text': text,
                        'SMSC': {'Location': 1},
                        'Number': number
                    }

                    #insert into database
                    if not db.insert_out_message(req.environ['pysmsd.db.path'], message, req.environ['pysmsd.client.id']):
                        return None

                    # mark the reply-to message if given
                    if replyto:
                        db.mark_message(req.environ['pysmsd.db.path'], req.environ['pysmsd.client.id'], replyto)

                    # send the message
                    req.environ['pysmsd.state_machine'].SendSMS(message)
                    return view.render()
                else:
                    return HTTPBadRequestJSON()
            else:
                return None
        else:
            # GET
            view = self.load_view('messages.json')
            if view:
                v = {}
                v['messages'] = []
                messages = db.get_out_messages(req.environ['pysmsd.db.path'])
                for row in messages:
                    m = {}
                    for k in row.keys():
                        m[k] = row[k]

                    v['messages'].append(m)

                return view.render(**v)
            else:
                return None



