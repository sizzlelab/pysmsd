#
# pysmsmd/daemon/dispatcher.py
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

import os
import sys
import logging

PACKAGE = 'pysmsd.handlers.enabled'

#import pysmsd.handlers.enabled.print_handler


class DispatcherException(Exception):
    pass

class Dispatcher(object):
    def __init__(self, db_path):
        self.db_path = db_path

        # read in available handlers
        self.handlers = {}

        print os.path.join(os.path.dirname(__file__), '..', 'handlers', 'enabled')
        module = None
        for py in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'handlers', 'enabled')):
            if py[-3:] != '.py' or py == '__init__.py':
                continue

            module = "%s.%s" % (PACKAGE, py[:-3])
            print "Found handler: %s" % module
            cls = 'Handler'
            try:
                __import__(module, locals(), globals())
            except:
                logging.error('Could not import module %s' % module)
                raise DispatcherException('Could not import module %s' % module)

            if sys.modules.has_key(module):
                if hasattr(sys.modules[module], cls):
                    self.handlers[module] = getattr(sys.modules[module], cls)()
                else:
                    logging.error('Module has no class %s' % cls)
                    raise DispatcherException('Module has no class %s' % cls)
            else:
                logging.error('Could not import module %s' % module)
                raise DispatcherException('Could not import module %s' % module)

        del module


    def in_message(self, id):
        for module,handler in self.handlers.items():
            logging.debug("dispatch to module %s" % module)
            try:
                m = getattr(handler, 'handle')
                if m:
                    try:
                        m(self.db_path, id)
                    except:
                        logging.error('Error invoking handler %s' % module)
                        raise DispatcherException('Error invoking handler %s' % module)
                else:
                    logging.error('Handler %s has not handle() method' % module)
                    raise DispatcherException('Handler %s has not handle() method' % module)

            except:
                logging.error('Could not invoke handler %s' % module)
                raise DispatcherException('Could not invoke handler %s' % module)


