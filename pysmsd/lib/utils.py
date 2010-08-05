# -*- coding: utf-8 -*-

#
# pysmsd.lib.utils
#
# Copyright 2009 Helsinki Institute for Information Technology
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

import time
from calendar import timegm
from math import floor, ceil

def utcisoptime(s):
    '''Parse a string representing a UTC datetime according to ISO 8601 format.
    Milliseconds are ignored.
    The return value is a struct_time as returned by gmtime().'''
    s = s[0:19]
    return time.strptime(s, '%Y-%m-%dT%H:%M:%S')


def utcisoptimelocal(s):
    '''Parse a string representing a UTC datetime according to ISO 8601 format.
    Milliseconds are ignored.
    The return value is a struct_time as returned by localtime().'''
    return time.localtime(timegm(utcisoptime(s)))


def utcisostrlocal(s):
    '''Parse a string representing a UTC datetime according to ISO 8601 format and return a string representing the local time.
    Milliseconds are ignored.'''
    return time.strftime('%Y-%m-%d %H:%M', utcisoptimelocal(s))


def prettydate(s):
    '''
    // Takes an ISO time and returns a string representing how
    // long ago the date represents.
    // adapted from javascript by John Resig (jquery.com)
    function prettyDate(time){
        var date = new Date((time || "").replace(/-/g,"/").replace(/[TZ]/g," ")),
            diff = (((new Date()).getTime() - date.getTime()) / 1000),
            day_diff = Math.floor(diff / 86400);
                
        if ( isNaN(day_diff) || day_diff < 0 || day_diff >= 31 )
            return;
                
        return day_diff == 0 && (
                diff < 60 && "just now" ||
                diff < 120 && "1 minute ago" ||
                diff < 3600 && Math.floor( diff / 60 ) + " minutes ago" ||
                diff < 7200 && "1 hour ago" ||
                diff < 86400 && Math.floor( diff / 3600 ) + " hours ago") ||
            day_diff == 1 && "Yesterday" ||
            day_diff < 7 && day_diff + " days ago" ||
            day_diff < 31 && Math.ceil( day_diff / 7 ) + " weeks ago";
    }
    '''
    if not s:
        return ''

    # difference in seconds betwen given time and now
    diff = (time.time() - timegm(utcisoptime(s)))
    
    # difference in days
    day_diff = int(floor(diff / 86400))

    if day_diff == 0:
        if diff < 60: ret = _('just now')
        elif diff < 120: ret = _('1 minute ago') 
        elif diff < 3600: ret = _('%s minutes ago') % int(floor(diff / 60))
        elif diff < 7200: ret = _('1 hour ago') 
        elif diff < 86400: ret = _('%s hours ago') % int(floor(diff / 3600))
    elif day_diff == 1:
        ret = _('Yesterday')
    elif day_diff < 7:
        ret = _('%s days ago') % day_diff
    elif day_diff < 31:
        ret = _('%s weeks ago') % int(ceil(day_diff / 7))
    else:
        # parse and reformat for local time
        ret = utcisostrlocal(s)

    return ret
