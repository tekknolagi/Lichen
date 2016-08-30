#!/usr/bin/env python

"""
Reference abstractions.

Copyright (C) 2016 Paul Boddie <paul@boddie.org.uk>

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

class Reference:

    "A reference abstraction."

    def __init__(self, kind, origin=None, name=None):

        """
        Initialise a reference using 'kind' to indicate the kind of object,
        'origin' to indicate the actual origin of a referenced object, and a
        'name' indicating an alias for the object in the program structure.
        """

        if isinstance(kind, Reference):
            raise ValueError, (kind, origin)
        self.kind = kind
        self.origin = origin
        self.name = name

    def __repr__(self):
        return "Reference(%r, %r, %r)" % (self.kind, self.origin, self.name)

    def __str__(self):

        """
        Serialise the reference as '<var>' or a description incorporating the
        kind and origin.
        """

        if self.kind == "<var>":
            return self.kind
        else:
            return "%s:%s" % (self.kind, self.origin)

    def __hash__(self):

        "Hash instances using the kind and origin only."

        return hash((self.kind, self.get_origin()))

    def __cmp__(self, other):

        "Compare with 'other' using the kind and origin only."

        if isinstance(other, Reference):
            return cmp((self.kind, self.get_origin()), (other.kind, other.get_origin()))
        else:
            return cmp(str(self), other)

    def get_name(self):

        "Return the name used for this reference."

        return self.name

    def get_origin(self):

        "Return the origin of the reference."

        return self.kind != "<var>" and self.origin or None

    def get_kind(self):

        "Return the kind of object referenced."

        return self.kind

    def has_kind(self, kinds):

        """
        Return whether the reference describes an object from the given 'kinds',
        where such kinds may be "<class>", "<function>", "<instance>",
        "<module>" or "<var>".
        """

        if not isinstance(kinds, (list, tuple)):
            kinds = [kinds]
        return self.get_kind() in kinds

    def get_path(self):

        "Return the attribute names comprising the path to the origin."

        return self.get_origin().split(".")

    def static(self):

        "Return this reference if it refers to a static object, None otherwise."

        return not self.has_kind(["<var>", "<instance>"]) and self or None

    def final(self):

        "Return a reference to either a static object or None."

        static = self.static()
        return static and static.origin or None

    def instance_of(self):

        "Return a reference to an instance of the referenced class."

        return self.has_kind("<class>") and Reference("<instance>", self.origin) or None

    def as_var(self):

        """
        Return a variable version of this reference. Any origin information is
        discarded since variable references are deliberately ambiguous.
        """

        return Reference("<var>", None, self.name)

    def provided_by_module(self, module_name):

        "Return whether the reference is provided by 'module_name'."

        path = self.origin
        return not path or path.rsplit(".", 1)[0] == module_name

    def alias(self, name):

        "Alias this reference employing 'name'."

        return Reference(self.get_kind(), self.get_origin(), name)

def decode_reference(s, name=None):

    "Decode 's', making a reference."

    if isinstance(s, Reference):
        return s.alias(name)

    # Null value.

    elif not s:
        return Reference("<var>", None, name)

    # Kind and origin.

    elif ":" in s:
        kind, origin = s.split(":")
        return Reference(kind, origin, name)

    # Kind-only, origin is indicated name.

    elif s[0] == "<":
        return Reference(s, name, name)

    # Module-only.

    else:
        return Reference("<module>", s, name)

# vim: tabstop=4 expandtab shiftwidth=4
