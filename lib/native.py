#!/usr/bin/env python

"""
Native library functions. None of these are actually defined here. Instead,
native implementations are substituted when each program is built.

Copyright (C) 2011, 2015, 2016 Paul Boddie <paul@boddie.org.uk>

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

# Environment support.

def _exit(status): pass
def _get_argv(): pass
def _get_path(): pass

# Identity testing.

def _is(x, y): pass
def _is_not(x, y): pass

# Integer operations.

def _int_add(self, other): pass
def _int_div(self, other): pass
def _int_mod(self, other): pass
def _int_mul(self, other): pass
def _int_neg(self): pass
def _int_pow(self, other): pass
def _int_sub(self, other): pass

def _int_and(self, other): pass
def _int_or(self, other): pass
def _int_xor(self, other): pass

def _int_lt(self, other): pass
def _int_gt(self, other): pass
def _int_eq(self, other): pass
def _int_ne(self, other): pass

def _int_str(self): pass

# String operations.

def _str_add(self, other): pass
def _str_eq(self, other): pass
def _str_gt(self, other): pass
def _str_lt(self, other): pass
def _str_len(self): pass
def _str_nonempty(self): pass
def _str_ord(self): pass
def _str_substr(self, start, size): pass

# List operations.

def _list_init(size): pass
def _list_setsize(self, size): pass
def _list_append(self, value): pass
def _list_concat(self, other): pass
def _list_len(self): pass
def _list_nonempty(self): pass
def _list_element(self, index): pass
def _list_setelement(self, index, value): pass

# Dictionary operations.

def _dict_init(size): pass
def _dict_bucketsize(self, index): pass
def _dict_key(self, index, element): pass
def _dict_value(self, index, element): pass
def _dict_additem(self, index, key, value): pass
def _dict_setitem(self, index, element, key, value): pass
def _dict_keys(self): pass
def _dict_values(self): pass

# Buffer operations.

def _buffer_str(self): pass

# Method binding.

def _get_using(callable, instance): pass

# Introspection.

def _object_getattr(obj, name, default): pass
def _isinstance(obj, cls): pass
def _issubclass(obj, cls): pass

# Input/output.

def _read(fd, n): pass
def _write(fd, str): pass

# vim: tabstop=4 expandtab shiftwidth=4
