#!/usr/bin/env python

"""
String objects.

Copyright (C) 2015, 2016 Paul Boddie <paul@boddie.org.uk>

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __builtins__.operator import _binary_op, _negate
from __builtins__.sequence import itemaccess
import native

class basestring(itemaccess):

    "The base class for all strings."

    def __init__(self):

        "Initialise the string."

        # Note the __data__ member. Since strings are either initialised from
        # literals or converted using routines defined for other types, no form
        # of actual initialisation is performed here.

        self.__data__ = None

    def __iadd__(self, other):

        "Return a new string for the operation."

        return _binary_op(self, other, native._str_add)

    __add__ = __radd__ = __iadd__

    def __mul__(self, other): pass
    def __rmul__(self, other): pass
    def __mod__(self, other): pass
    def __rmod__(self, other): pass

    def __lt__(self, other):

        "Return a new boolean for the comparison."

        return _binary_op(self, other, native._str_lt)

    def __gt__(self, other):

        "Return a new boolean for the comparison."

        return _binary_op(self, other, native._str_gt)

    def __le__(self, other):

        "Return a new boolean for the comparison."

        return _negate(self.__gt__(other))

    def __ge__(self, other):

        "Return a new boolean for the comparison."

        return _negate(self.__lt__(other))

    def __eq__(self, other):

        "Return a new boolean for the comparison."

        return _binary_op(self, other, native._str_eq)

    def __ne__(self, other):

        "Return a new boolean for the comparison."

        return _negate(self.__eq__(other))

    def __len__(self):
        return native._str_len(self)

    def __str__(self):

        "Return a string representation."

        return self

    def __repr__(self):

        "Return a program representation."

        # NOTE: To be implemented with proper quoting.
        b = buffer(['"', self, '"'])
        return str(b)

    def __bool__(self):
        return native._str_nonempty(self)

    def endswith(self, s): pass
    def find(self, sub, start=None, end=None): pass
    def index(self, sub, start=None, end=None): pass
    def join(self, l): pass
    def lower(self): pass
    def lstrip(self, chars=None): pass
    def replace(self, old, new, count=None): pass
    def rfind(self, sub, start=None, end=None): pass
    def rsplit(self, sep=None, maxsplit=None): pass
    def rstrip(self, chars=None): pass
    def split(self, sep=None, maxsplit=None): pass
    def splitlines(self, keepends=False): pass
    def startswith(self, s): pass
    def strip(self, chars=None): pass
    def upper(self): pass

    # Special implementation methods.

    def __get_single_item__(self, index):

        "Return the item at the normalised (positive) 'index'."

        self._check_index(index)
        return native._str_substr(self, index, 1)

class string(basestring):
    pass

class unicode(basestring):
    def encode(self, encoding): pass

def str(obj):

    "Return the string representation of 'obj'."

    # Class attributes of instances provide __str__.

    return obj.__str__()

# vim: tabstop=4 expandtab shiftwidth=4
