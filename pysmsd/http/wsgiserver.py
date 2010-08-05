# -*- coding: utf-8 -*-

#
# pysmsd.http.wsgiserver
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

import urllib
import sys
import logging
import re
from pysmsd.http.exc import HTTPInternalServerErrorJSON, HTTPUnauthorizedJSON, HTTPNotFoundJSON
import pysmsd.http.controllers.static
from pysmsd.db import db

from webob import Request, Response

from wsgiref.simple_server import make_server, WSGIRequestHandler
from cherrypy.wsgiserver import CherryPyWSGIServer

import mimetypes
mimetypes.init()                # workaround for issue 5853


class DBMiddleware(object):
    def __init__(self, path, application=None):
        self.application = application
        self.path = path

    def set_application(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['pysmsd.db.path'] = self.path
        return self.application(environ, start_response)

class StateMachineMiddleware(object):
    def __init__(self, state_machine, application=None):
        self.application = application
        self.state_machine = state_machine

    def set_application(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['pysmsd.state_machine'] = self.state_machine
        return self.application(environ, start_response)

class AuthMiddleware(object):
    def __init__(self, application=None):
        self.application = application

    def set_application(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        #  create webob Request
        req = Request(environ)
        req.charset = 'utf8'

        client_id = db.is_authorized(environ['pysmsd.db.path'], req.params.get('name', ''), req.params.get('password', ''))
        if client_id != None:
            environ['pysmsd.client.id'] = client_id
            environ['pysmsd.client.name'] = req.params.get('name')
            return self.application(environ, start_response)
        else:
            return HTTPUnauthorizedJSON()(environ, start_response)


class RouterException(Exception): pass

class Router(object):
    def __init__(self):
        self.routes = []
        self.module_base = None

    def add_route(self, template, controller, action, args=None):
        regex = re.compile('%s$' % template)
        self.routes.append((regex, controller, action, args))
    
    def serverside_redirect(self, controller, action, req):
        # load controller
        try:
            controller = self.load_controller(controller)
        except RouterException, e:
            logging.exception('wsgiserver: could not load controller.')
            logging.debug("\n" + '-' * 80)
            return HTTPNotFoundJSON('Could not load controller: %s' % e)(environ, start_response)
            
        if controller:
            # get the action
            try:
                logging.debug('--> Req: [%s]' % (req.path_url))
                action = getattr(controller, action)
                if action:
                    # execute action and get response
                    return action(req)
                else:
                    logging.debug('No such action (1)')
                    logging.debug("\n" + '-' * 80)
                    return HTTPNotFoundJSON('No such action')(environ, start_response)
            except Exception, e:
                logging.exception('No such action (2)')
                logging.debug("\n" + '-' * 80)
                return HTTPNotFoundJSON('No such action: %s' % e)(environ, start_response)
        else:
            logging.debug('No such controller')
            logging.debug("\n" + '-' * 80)
            return HTTPNotFoundJSON('No such controller')(environ, start_response)



    def load_controller(self, controller):
        module, cls = controller.rsplit('.', 1)

        cls = cls.capitalize()
        if self.module_base:
            module = '%s.%s' % (self.module_base, module)

        try:
            __import__(module)
        except:
            logging.error('Could not import module %s' % module)
            raise RouterException('Could not import module %s' % module)

        if sys.modules.has_key(module):
            if hasattr(sys.modules[module], cls):
                return getattr(sys.modules[module], cls)()
            else:
                logging.error('Module has no class %s' % cls)
                raise RouterException('Module has no class %s' % cls)
        else:
            logging.error('Could not import module %s' % module)
            raise RouterException('Could not import module %s' % module)

    def __call__(self, environ, start_response):
        # going through proxy messes up path_info, so fix it
        if environ['PATH_INFO'].startswith('http'):
            host_url = environ['wsgi.url_scheme']+'://'
            if environ.get('HTTP_HOST'):
                host_url += environ['HTTP_HOST']
            else:
                host_url += environ['SERVER_NAME']
                
                if environ['wsgi.url_scheme'] == 'https':
                    if environ['SERVER_PORT'] != '443':
                        host_url += ':'+environ['SERVER_PORT']
                else:
                    if environ['SERVER_PORT'] != '80':
                        host_url += ':'+environ['SERVER_PORT']

            environ['PATH_INFO'] = environ['PATH_INFO'][len(host_url):]

        #  create webob Request
        req = Request(environ)
        req.charset = 'utf8'

        # try to match a route
        for regex, controller, action, args in self.routes:
            matches = regex.search(req.path_url)
            if matches:
                # interpolate any backreferences into controller, action and args 
                controller = matches.expand(controller)
                action = matches.expand(action)
                
                # add in named groups from the regex
                req.urlvars = matches.groupdict()

                # add in unamed groups (this includes numerically keyed copies of the named groups)
                unamed_groups = matches.groups()
                req.urlvars.update(dict(zip(range(len(unamed_groups)), unamed_groups)))

                # interpolate backreferences into arg values and add to request
                if args:
                    args = dict([(k, urllib.unquote(matches.expand(v))) for k,v in args.items()])
                    req.urlvars.update(args)

                # add a reference to the router
                req.environ['pysmsd.router'] = self

                # load controller
                try:
                    controller = self.load_controller(controller)
                except RouterException, e:
                    logging.exception('wsgiserver: could not load controller.')
                    logging.debug("\n" + '-' * 80)
                    return HTTPNotFoundJSON('Could not load controller: %s' % e)(environ, start_response)
                    
                if controller:
                    # get the action
                    try:
                        logging.debug('--> Req: [%s]' % (req.path_url))
                        action = getattr(controller, action)
                        if action:
                            try:
                                # if auth is needed, validate
                                if req.urlvars.get('auth', 'no') == 'yes':
                                    client_id = db.is_authorized(req.environ['pysmsd.db.path'], req.params.get('name', ''), req.params.get('password', ''))
                                    if client_id != None:
                                        req.environ['pysmsd.client.id'] = client_id
                                        req.environ['pysmsd.client.name'] = req.params.get('name')
                                    else:
                                        return HTTPUnauthorizedJSON()(environ, start_response)

                                # execute action and get response
                                try:
                                    res = action(req)
                                except:
                                    return HTTPInternalServerErrorJSON()(environ, start_response)

                                if isinstance(res, basestring):
                                    if req.path_url[-4:] == 'json':
                                        res = Response(body=res, content_type='application/json')
                                    else:
                                        res = Response(body=res)

                                elif not res:
                                    logging.debug('No such action (0)')
                                    logging.debug("\n" + '-' * 80)
                                    return HTTPNotFoundJSON('No such action')(environ, start_response)

                                logging.debug('<-- res: %s %s' % (res.status, res.content_length))
                                return res(environ, start_response)
                            except:
                                logging.exception('wsgiserver: error executing action.')
                                logging.debug("\n" + '-' * 80)
                                return HTTPInternalServerErrorJSON('Error executing action')(environ, start_response)
                        else:
                            logging.debug('No such action (1)')
                            logging.debug("\n" + '-' * 80)
                            return HTTPNotFoundJSON('No such action')(environ, start_response)
                    except Exception, e:
                        logging.exception('No such action (2)')
                        logging.debug("\n" + '-' * 80)
                        return HTTPNotFoundJSON('No such action: %s' % e)(environ, start_response)
                else:
                    logging.debug('No such controller')
                    logging.debug("\n" + '-' * 80)
                    return HTTPNotFoundJSON('No such controller')(environ, start_response)

        # no matches
        logging.debug('No Match')
        logging.debug("\n" + '-' * 80)
        return HTTPNotFoundJSON()(environ, start_response)


class PysmsdWSGIRequestHandler(WSGIRequestHandler):
    """Just to make sure that log messages are at debug level"""
    def log_message(self, format, *args):
        logging.debug(format%args)


def serve(db_path, state_machine, host, port, cherrypy=True, ssl_cert=None, ssl_key=None):
    '''
    The main part of this configuration is the definition of routes.
    Routes have three components:
    1) a regular expression which the url is matched against (not including an query string). The regular expression is matched against the end of the url.
    2) a controller class that will handle the route. As a convienience module_base can be set to a common package prefix. Note that back references can be used here from 1). Also note that the class name will be automatically capitalized.
    3) an action; i.e. a method of the class specified in 2). This method must take one argument. This can also contain backreferences from 1)
    4) (optional) extra arguments that are passed to the action. This can contain backreferences from 1)
    '''

    router = Router()
    router.module_base = 'pysmsd.http.controllers'
    #                 Pattern                                                   Controller           Action    Extra args
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    router.add_route('/static/(.+)',                                           'static.Static',      'index',   {'path': r'\1', 'auth': 'no'})
    router.add_route('/messages/in.json',                                      'messages.Messages',  'in_messages', {'auth': 'yes'})
    router.add_route('/messages/in/(\d+).json',                                'messages.Messages',  'in_message', {'id': r'\1', 'auth': 'yes'})
    router.add_route('/messages/out.json',                                     'messages.Messages',  'out_messages', {'auth': 'yes'})
    router.add_route('/messages/out/(\d+).json',                               'messages.Messages',  'out_message', {'id': r'\1', 'auth': 'yes'})
    router.add_route('/',                                                      'index.Index',        'index', {'auth': 'no'})

    #authmw = AuthMiddleware(router)
    dbmw = DBMiddleware(db_path, router)
    smmw = StateMachineMiddleware(state_machine, dbmw)

    if cherrypy:
        if host == 'localhost':
            host = '127.0.0.1' # Force IPv4 to avoid problems with Firefox 2 on Mac OS X.
        if ssl_cert and ssl_key:
            CherryPyWSGIServer.ssl_certificate = ssl_cert
            CherryPyWSGIServer.ssl_private_key = ssl_key

        server = CherryPyWSGIServer((host, port), smmw, numthreads=10, timeout=30)
        router.server = server
        try:
            logging.info('starting cherrypy httpd daemon on port %s...', port)
            server.start()
        except KeyboardInterrupt:
            server.stop()

    else:
        httpd = make_server(host, port, dbmw, handler_class=PysmsdWSGIRequestHandler)
        try:
            logging.info('starting httpd daemon on port %s...', port)
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
