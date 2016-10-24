#!/usr/bin/env python

"""
Generate C code from object layouts and other deduced information.

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

from common import CommonOutput
from encoders import encode_bound_reference, encode_function_pointer, \
                     encode_instantiator_pointer, encode_path, encode_symbol
from os import listdir
from os.path import isdir, join, split
from referencing import Reference

def copy(source, target):

    "Copy a text file from 'source' to 'target'."

    if isdir(target):
        target = join(target, split(source)[-1])
    infile = open(source)
    outfile = open(target, "w")
    try:
        outfile.write(infile.read())
    finally:
        outfile.close()
        infile.close()

class Generator(CommonOutput):

    "A code generator."

    function_type = "__builtins__.core.function"

    table_name_prefixes = {
        "<class>" : "Class",
        "<module>" : "Module",
        "<instance>" : "Instance"
        }

    structure_size_prefixes = {
        "<class>" : "c",
        "<module>" : "m",
        "<instance>" : "i"
        }

    def __init__(self, importer, optimiser, output):
        self.importer = importer
        self.optimiser = optimiser
        self.output = output

    def to_output(self):

        "Write the generated code."

        self.check_output()
        self.write_structures()
        self.copy_templates()

    def copy_templates(self):

        "Copy template files to the generated output directory."

        templates = join(split(__file__)[0], "templates")

        for filename in listdir(templates):
            copy(join(templates, filename), self.output)

    def write_structures(self):

        "Write structures used by the program."

        f_consts = open(join(self.output, "progconsts.h"), "w")
        f_defs = open(join(self.output, "progtypes.c"), "w")
        f_decls = open(join(self.output, "progtypes.h"), "w")
        f_signatures = open(join(self.output, "main.h"), "w")
        f_code = open(join(self.output, "main.c"), "w")

        try:
            # Output boilerplate.

            print >>f_consts, """\
#ifndef __PROGCONSTS_H__
#define __PROGCONSTS_H__
"""
            print >>f_decls, """\
#ifndef __PROGTYPES_H__
#define __PROGTYPES_H__

#include "progconsts.h"
#include "types.h"
"""
            print >>f_defs, """\
#include "progtypes.h"
#include "main.h"
"""
            print >>f_signatures, """\
#ifndef __MAIN_H__
#define __MAIN_H__

#include "types.h"
"""
            print >>f_code, """\
#include <string.h>
#include "types.h"
#include "ops.h"
#include "progconsts.h"
#include "progtypes.h"
#include "progops.h"
#include "main.h"
"""

            # Generate structure size data.

            size_tables = {}

            for kind in ["<class>", "<module>", "<instance>"]:
                size_tables[kind] = {}

            for ref, structure in self.optimiser.structures.items():
                size_tables[ref.get_kind()][ref.get_origin()] = len(structure)

            size_tables = size_tables.items()
            size_tables.sort()

            for kind, sizes in size_tables:
                self.write_size_constants(f_consts, self.structure_size_prefixes[kind], sizes, 0)

            # Generate parameter table size data.

            min_sizes = {}
            max_sizes = {}

            for path, parameters in self.optimiser.parameters.items():
                argmin, argmax = self.get_argument_limits(path)
                min_sizes[path] = argmin
                max_sizes[path] = argmax

                # Record instantiator limits.

                if path.endswith(".__init__"):
                    path = path[:-len(".__init__")]
                    min_sizes[path] = argmin - 1
                    max_sizes[path] = argmax - 1

            self.write_size_constants(f_consts, "pmin", min_sizes, 0)
            self.write_size_constants(f_consts, "pmax", max_sizes, 0)

            # Generate attribute codes.

            self.write_code_constants(f_consts, self.optimiser.all_attrnames, self.optimiser.locations)

            # Generate table and structure data.

            function_instance_attrs = None
            objects = self.optimiser.attr_table.items()
            objects.sort()

            for ref, indexes in objects:
                attrnames = self.get_attribute_names(indexes)

                kind = ref.get_kind()
                path = ref.get_origin()
                table_name = encode_tablename(self.table_name_prefixes[kind], path)
                structure_size = encode_size(self.structure_size_prefixes[kind], path)

                # Generate structures for classes and modules.

                if kind != "<instance>":
                    structure = []
                    attrs = self.get_static_attributes(kind, path, attrnames)

                    # Set a special instantiator on the class.

                    if kind == "<class>":
                        attrs["__fn__"] = path
                        attrs["__args__"] = encode_size("pmin", path)

                        # Write instantiator declarations based on the
                        # applicable initialiser.

                        init_ref = attrs["__init__"]

                        # Signature: __attr __new_<name>(__attr[]);

                        print >>f_signatures, "__attr %s(__attr[]);" % encode_instantiator_pointer(path)

                        # Write instantiator definitions.

                        self.write_instantiator(f_code, path, init_ref)

                        # Write parameter table.

                        self.make_parameter_table(f_decls, f_defs, path, init_ref.get_origin())

                    self.populate_structure(Reference(kind, path), attrs, kind, structure)
                    self.write_structure(f_decls, f_defs, path, table_name, structure_size, structure)

                # Record function instance details for function generation below.

                else:
                    attrs = self.get_instance_attributes(path, attrnames)
                    if path == self.function_type:
                        function_instance_attrs = attrs

                # Write a table for all objects.

                table = []
                self.populate_table(Reference(kind, path), table)
                self.write_table(f_decls, f_defs, table_name, structure_size, table)

            # Generate function instances.

            functions = set()

            for ref in self.importer.objects.values():
                if ref.has_kind("<function>"):
                    functions.add(ref.get_origin())

            functions = list(functions)
            functions.sort()

            for path in functions:
                cls = self.function_type
                table_name = encode_tablename("Instance", cls)
                structure_size = encode_size(self.structure_size_prefixes["<instance>"], cls)

                # Set a special callable attribute on the instance.

                function_instance_attrs["__fn__"] = path
                function_instance_attrs["__args__"] = encode_size("pmin", path)

                # Produce two structures where a method is involved.

                ref = self.importer.get_object(path)
                parent_ref = self.importer.get_object(ref.parent())
                parent_kind = parent_ref and parent_ref.get_kind()

                # Populate and write each structure.

                if parent_kind == "<class>":

                    # An unbound version of a method.

                    structure = self.populate_function(path, function_instance_attrs, True)
                    self.write_structure(f_decls, f_defs, path, table_name, structure_size, structure)

                    # A bound version of a method.

                    structure = self.populate_function(path, function_instance_attrs, False)
                    self.write_structure(f_decls, f_defs, encode_bound_reference(path), table_name, structure_size, structure)

                # A normal function.

                structure = self.populate_function(path, function_instance_attrs, False)
                self.write_structure(f_decls, f_defs, path, table_name, structure_size, structure)

                # Write function declarations.
                # Signature: __attr <name>(__attr[]);

                print >>f_signatures, "__attr %s(__attr args[]);" % encode_function_pointer(path)

                # Write parameter table.

                self.make_parameter_table(f_decls, f_defs, path, path)

            # Output more boilerplate.

            print >>f_consts, """\

#endif /* __PROGCONSTS_H__ */"""

            print >>f_decls, """\

#define __FUNCTION_TYPE %s
#define __FUNCTION_INSTANCE_SIZE %s

#endif /* __PROGTYPES_H__ */""" % (
    encode_path(self.function_type),
    encode_size(self.structure_size_prefixes["<instance>"], self.function_type)
    )

            print >>f_signatures, """\

#endif /* __MAIN_H__ */"""

        finally:
            f_consts.close()
            f_defs.close()
            f_decls.close()
            f_signatures.close()
            f_code.close()

    def make_parameter_table(self, f_decls, f_defs, path, function_path):

        """
        Write parameter table details to 'f_decls' (to declare a table) and to
        'f_defs' (to define the contents) for the function with the given
        'path', using 'function_path' to obtain the parameter details. The
        latter two arguments may differ when describing an instantiator using
        the details of an initialiser.
        """

        table = []
        table_name = encode_tablename("Function", path)
        structure_size = encode_size("pmax", path)
        self.populate_parameter_table(function_path, table)
        self.write_parameter_table(f_decls, f_defs, table_name, structure_size, table)

    def write_size_constants(self, f_consts, size_prefix, sizes, padding):

        """
        Write size constants to 'f_consts' for the given 'size_prefix', using
        the 'sizes' dictionary to populate the definition, adding the given
        'padding' to the basic sizes.
        """

        print >>f_consts, "enum %s {" % encode_size(size_prefix)
        first = True
        for path, size in sizes.items():
            if not first:
                print >>f_consts, ","
            else:
                first = False
            f_consts.write("    %s = %d" % (encode_size(size_prefix, path), size + padding))
        print >>f_consts, "\n    };"

    def write_code_constants(self, f_consts, attrnames, locations):

        """
        Write code constants to 'f_consts' for the given 'attrnames' and
        attribute 'locations'.
        """

        print >>f_consts, "enum %s {" % encode_symbol("code")
        first = True
        for i, attrname in enumerate(attrnames):
            if not first:
                print >>f_consts, ","
            else:
                first = False
            f_consts.write("    %s = %d" % (encode_symbol("code", attrname), i))
        print >>f_consts, "\n    };"

        print >>f_consts, "enum %s {" % encode_symbol("pos")
        first = True
        for i, attrnames in enumerate(locations):
            for attrname in attrnames:
                if not first:
                    print >>f_consts, ","
                else:
                    first = False
                f_consts.write("    %s = %d" % (encode_symbol("pos", attrname), i))
        print >>f_consts, "\n    };"

    def write_table(self, f_decls, f_defs, table_name, structure_size, table):

        """
        Write the declarations to 'f_decls' and definitions to 'f_defs' for
        the object having the given 'table_name' and the given 'structure_size',
        with 'table' details used to populate the definition.
        """

        print >>f_decls, "extern const __table %s;\n" % table_name

        # Write the corresponding definition.

        print >>f_defs, "const __table %s = {\n    %s,\n    {\n        %s\n        }\n    };\n" % (
            table_name, structure_size,
            ",\n        ".join(table))

    def write_parameter_table(self, f_decls, f_defs, table_name, structure_size, table):

        """
        Write the declarations to 'f_decls' and definitions to 'f_defs' for
        the object having the given 'table_name' and the given 'structure_size',
        with 'table' details used to populate the definition.
        """

        print >>f_decls, "extern const __ptable %s;\n" % table_name

        # Write the corresponding definition.

        print >>f_defs, "const __ptable %s = {\n    %s,\n    {\n        %s\n        }\n    };\n" % (
            table_name, structure_size,
            ",\n        ".join([("{%s, %s}" % t) for t in table]))

    def write_structure(self, f_decls, f_defs, path, table_name, structure_size, structure):

        """
        Write the declarations to 'f_decls' and definitions to 'f_defs' for
        the object having the given 'path', the given 'table_name',  and the
        given 'structure_size', with 'structure' details used to populate the
        definition.
        """

        print >>f_decls, "extern __obj %s;\n" % encode_path(path)

        # Write an instance-specific type definition for instances of classes.
        # See: templates/types.h

        print >>f_decls, """\
typedef struct {
    const __table * table;
    unsigned int pos;
    __attr attrs[%s];
} %s;
""" % (structure_size, encode_symbol("obj", path))

        # Write the corresponding definition.

        print >>f_defs, "__obj %s = {\n    &%s,\n    %s,\n    {\n        %s\n    }};\n" % (
            encode_path(path), table_name, encode_symbol("pos", path),
            ",\n        ".join(structure))

    def get_parameters(self, ref):
        return self.importer.function_parameters[ref.get_origin()]

    def get_argument_limits(self, path):
        parameters = self.importer.function_parameters[path]
        defaults = self.importer.function_defaults.get(path)
        return len(parameters) - (defaults and len(defaults) or 0), len(parameters)

    def get_attribute_names(self, indexes):

        """
        Given a list of attribute table 'indexes', return a list of attribute
        names.
        """

        all_attrnames = self.optimiser.all_attrnames
        attrnames = []
        for i in indexes:
            if i is None:
                attrnames.append(None)
            else:
                attrnames.append(all_attrnames[i])
        return attrnames

    def get_static_attributes(self, kind, name, attrnames):

        """
        Return a mapping of attribute names to paths for attributes belonging
        to objects of the given 'kind' (being "<class>" or "<module>") with
        the given 'name' and supporting the given 'attrnames'.
        """

        attrs = {}

        for attrname in attrnames:
            if attrname is None:
                continue
            if kind == "<class>":
                path = self.importer.all_class_attrs[name][attrname]
            elif kind == "<module>":
                path = "%s.%s" % (name, attrname)
            else:
                continue

            # The module may be hidden.

            attr = self.importer.get_object(path)
            if not attr:
                module = self.importer.hidden.get(path)
                if module:
                    attr = Reference(module.name, "<module>")
            attrs[attrname] = attr

        return attrs

    def get_instance_attributes(self, name, attrnames):

        """
        Return a mapping of attribute names to references for attributes
        belonging to instances of the class with the given 'name', where the
        given 'attrnames' are supported.
        """

        consts = self.importer.all_instance_attr_constants[name]
        attrs = {}
        for attrname in attrnames:
            if attrname is None:
                continue
            const = consts.get(attrname)
            attrs[attrname] = const or Reference("<var>", "%s.%s" % (name, attrname))
        return attrs

    def populate_table(self, key, table):

        """
        Traverse the attributes in the determined order for the structure having
        the given 'key', adding entries to the attribute 'table'.
        """

        for attrname in self.optimiser.structures[key]:

            # Handle gaps in the structure.

            if attrname is None:
                table.append("0")
            else:
                table.append(encode_symbol("code", attrname))

    def populate_parameter_table(self, key, table):

        """
        Traverse the parameters in the determined order for the structure having
        the given 'key', adding entries to the attribute 'table'.
        """

        for value in self.optimiser.parameters[key]:

            # Handle gaps in the structure.

            if value is None:
                table.append(("0", "0"))
            else:
                name, pos = value
                table.append((encode_symbol("pcode", name), pos))

    def populate_function(self, path, function_instance_attrs, unbound=False):

        """
        Populate a structure for the function with the given 'path'. The given
        'attrs' provide the instance attributes, and if 'unbound' is set to a
        true value, an unbound method structure is produced (as opposed to a
        callable bound method structure).
        """

        cls = self.function_type
        structure = []
        self.populate_structure(Reference("<instance>", cls), function_instance_attrs, "<instance>", structure, unbound)

        # Append default members.

        self.append_defaults(path, structure)
        return structure

    def populate_structure(self, ref, attrs, kind, structure, unbound=False):

        """
        Traverse the attributes in the determined order for the structure having
        the given 'ref' whose members are provided by the 'attrs' mapping, in a
        structure of the given 'kind', adding entries to the object 'structure'.
        If 'unbound' is set to a true value, an unbound method function pointer
        will be employed, with a reference to the bound method incorporated into
        the special __fn__ attribute.
        """

        origin = ref.get_origin()

        for attrname in self.optimiser.structures[ref]:

            # Handle gaps in the structure.

            if attrname is None:
                structure.append("{0, 0}")

            # Handle non-constant and constant members.

            else:
                attr = attrs[attrname]

                if attrname == "__fn__":

                    # Provide bound method references and the unbound function
                    # pointer if populating methods in a class.

                    bound_attr = None

                    # Classes offer instantiators.

                    if kind == "<class>":
                        attr = encode_instantiator_pointer(attr)

                    # Methods offers references to bound versions and an unbound
                    # method function.

                    elif unbound:
                        bound_attr = encode_bound_reference(attr)
                        attr = "__unbound_method"

                    # Other functions just offer function pointers.

                    else:
                        attr = encode_function_pointer(attr)

                    structure.append("{%s, .fn=%s}" % (bound_attr and ".b=%s" % bound_attr or "0", attr))
                    continue

                elif attrname == "__args__":
                    structure.append("{.min=%s, .ptable=%s}" % (attr, encode_tablename("Function", origin)))
                    continue

                structure.append(self.encode_member(origin, attrname, attr, kind))

    def encode_member(self, path, name, ref, structure_type):

        """
        Encode within the structure provided by 'path', the member whose 'name'
        provides 'ref', within the given 'structure_type'.
        """

        kind = ref.get_kind()
        origin = ref.get_origin()

        # References to constant literals.

        if kind == "<instance>":
            attr_path = "%s.%s" % (path, name)

            # Obtain a constant value directly assigned to the attribute.

            if self.optimiser.constant_numbers.has_key(attr_path):
                constant_number = self.optimiser.constant_numbers[attr_path]
                constant_value = "const%d" % constant_number
                return "{&%s, &%s} /* %s */" % (constant_value, constant_value, name)

        # General undetermined members.

        if kind in ("<var>", "<instance>"):
            return "{0, 0} /* %s */" % name

        # Set the context depending on the kind of attribute.
        # For methods:          {&<path>, &<attr>}
        # For other attributes: {&<attr>, &<attr>}

        else:
            context = (kind == "<function>" and structure_type == "<class>" and \
                       "&%s" % encode_path(path) or "0") or \
                       kind == "<instance>" and "&%s" % encode_path(origin) or "0"
            return "{%s, &%s}" % (context, encode_path(origin))

    def append_defaults(self, path, structure):

        """
        For the given 'path', append default parameter members to the given
        'structure'.
        """

        for name, default in self.importer.function_defaults.get(path):
            structure.append(self.encode_member(path, name, default, "<instance>"))

    def write_instantiator(self, f_code, path, init_ref):

        """
        Write an instantiator to 'f_code' for instances of the class with the
        given 'path', with 'init_ref' as the initialiser function reference.

        NOTE: This also needs to initialise any __fn__ and __args__ members
        NOTE: where __call__ is provided by the class.
        """

        parameters = self.get_parameters(init_ref)
        arg_copy = "memcpy(&__tmp_args[1], args, %d * sizeof(__attr));" % (len(parameters) - 1)

        print >>f_code, """\
__attr %s(__attr args[])
{
    __attr __tmp_args[%d];
    __tmp_args[0] = __new(&%s, &%s, sizeof(%s));
    %s
    %s(__tmp_args);
    return __tmp_args[0];
}
""" % (
    encode_instantiator_pointer(path),
    len(parameters),
    encode_tablename("Instance", path), encode_path(path), encode_symbol("obj", path),
    len(parameters) - 1 and arg_copy or "",
    encode_function_pointer(init_ref.get_origin())
    )

def encode_size(table_type, path=None):
    return "__%ssize%s" % (table_type, path and "_%s" % encode_path(path) or "")

def encode_tablename(table_type, path):
    return "__%sTable_%s" % (table_type, encode_path(path))

# vim: tabstop=4 expandtab shiftwidth=4
