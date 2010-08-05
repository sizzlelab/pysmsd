#
# pysmsd.lib.json
#
# Copyright 2009 Helsinki Institute for Information Technology
# and the authors.
#
# Authors: Ken Rimey <rimey@hiit.fi>
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

from __future__ import absolute_import

try:
    import json                 # Python 2.6
except ImportError:
    import simplejson as json   # Python 2.5

dumps = json.dumps

def loads(s, *args, **kwargs):
    # When its argument is of type str, loads() decodes strings as
    # either str or unicode depending on whether simplejson's speedups
    # are installed (at least this is true in simplejson 2.0.7).  It
    # always decodes strings as unicode when the argument to loads()
    # is of type unicode.
    if isinstance(s, str):
        s = s.decode('utf-8')
    return json.loads(s, *args, **kwargs)
