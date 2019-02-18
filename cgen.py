import os
from typing import List

from ast import Class, Method, Type, ObjectType, Primitive, Package
from codegen import mangle_method_name
from option import Option
from phase import Phase
from report import Report
from symbol import SymbolTable
from util import singleton

HEADER = """
#ifndef {header_define}
#define {header_define}

#include <play.h>

{class_struct}

#endif //{header_define}
"""
CODE = """
#include "{file}.h"

{methods}

"""


def get_c_type_name(type: Type) -> str:
    if not type:
        return 'void'
    if isinstance(type, ObjectType):
        return type.cls.qualified_name.replace('.', '_')
    elif isinstance(type, Primitive):
        return 'p' + type.name


class NativeGen(Phase):
    def run(self):
        Report().begin("NativeGen")

        for cls in SymbolTable().get_classes():
            self.gen_class(cls)

        Report().end()

    def gen_class(self, cls: Class):
        class_struct = ''
        header_define = (cls.qualified_name.replace('.', '_') + '_h').upper()
        methods = []
        if cls.is_native:
            class_struct = 'Class(' + cls.qualified_name.replace('.', '_') + ', {\n});'
            name = cls.qualified_name.replace('.', '_')
            methods.append('NATIVE {} {}()'.format(name, name + '_new'))
        for method in cls.methods + cls.static_methods:
            if method.is_native:
                methods.append(self.gen_method(method))

        if class_struct or methods:
            header = os.path.join(Option().c_source_location, cls.qualified_name.replace('.', '/') + '.h')
            source = os.path.join(Option().c_source_location, cls.qualified_name.replace('.', '/') + '.c')
            folder = os.path.dirname(header)
            if not os.path.exists(folder):
                os.makedirs(folder)
            if not os.path.exists(header):
                with open(header, 'w') as f:
                    f.write(HEADER.format(header_define=header_define, class_struct=class_struct))
            if not os.path.exists(source):
                with open(source, 'w') as f:
                    f.write(CODE.format(file=cls.qualified_name.split('.')[-1], methods='\n'.join(m + '{\n}' for m in methods)))

    def gen_method(self, method: Method):
        parameters = ['{} {}'.format(get_c_type_name(p.type), p.name) for p in method.parameters]
        if not method.is_static:
            parameters.insert(0, '{} {}'.format(get_c_type_name(ObjectType(method.owner)), 'this'))
        return 'NATIVE {} {}({})'.format(
            get_c_type_name(method.return_type),
            mangle_method_name(method),
            ', '.join(parameters))


@singleton
class RuntimeGen(Phase):
    def __init__(self):
        self.classes: List[Class] = []
        self.packages: List[Package] = []

    def run(self):
        Report().begin("RuntimeGen")

        table = SymbolTable()
        self.classes = sorted(table.get_classes(), key=lambda c: c.qualified_name)
        self.packages = sorted(table.get_packages(), key=lambda pkg: pkg.qualified_name)
        self.gen_global()

        Report().end()

    def gen_global(self):
        content = ['#include "const.h"']
        package_children = []
        package_list = ['NATIVE Package PACKAGES[] = {']
        for package in self.packages:
            child_packages = []
            child_classes = []
            for child in package.children.values():
                if isinstance(child, Package):
                    child_packages.append(child)
                else:
                    child_classes.append(child)
            name = package.qualified_name.replace('.', '_')
            if not name:
                name = "_root"
            package_children.append('int ' + name + '_packages[] = {' + ', '.join(str(self.packages.index(p)) for p in child_packages) + '};')
            package_children.append('int ' + name + '_classes[] = {' + ', '.join(str(self.classes.index(c)) for c in child_classes) + '};')
            package_list.append('    {' + '"{}", {}, {}_packages, {}, {}_classes'.format(package.qualified_name, len(child_packages), name, len(child_classes), name) + '},')
        package_list.append('};')
        content.extend(package_children)
        content.extend(package_list)

        externals = set()
        method_assigns = {}
        # class_assigns = []
        class_children = []
        class_list = ['NATIVE Class CLASSES[] = {']
        class_ids = []
        for i, cls in enumerate(self.classes):
            superclasses = cls.superclasses
            cls_name = cls.qualified_name.replace('.', '_')
            if cls.is_native:
                class_ids.append('int {}_id = {};'.format(cls_name, i))
            class_children.append('int ' + cls_name + '_superclasses[] = {' + ', '.join(str(self.classes.index(s)) for s in superclasses) + '};')
            class_children.append('Method ' + cls_name + '_methods[] = {')
            assigns = []
            method_assigns[cls_name + '_methods'] = assigns
            for method in cls.inherited_methods:
                externals.add('extern int ' + mangle_method_name(method) + ';')
                sig = ', '.join(str(p.type) for p in method.parameters)
                class_children.append('    {' + '"{}", {}, {}, "{}", NULL'.format(method.name, self.classes.index(method.owner), 0, sig) + '},')
                assigns.append(mangle_method_name(method))
            class_children.append('};')
            flag = 0
            if cls.is_interface:
                flag |= 1
            if cls.is_abstract:
                flag |= 2
            if cls.is_native:
                flag |= 4
            # new_method = cls.qualified_name.replace('.', '_') + '_new'
            # externals.add('extern int ' + new_method + ';')
            # class_assigns.append(new_method)
            class_list.append(
                '    {' + '"{}", {},  {}, {}, {}_superclasses, {}, {}_methods'.format(
                    cls.qualified_name, i, flag, len(superclasses), cls_name, len(cls.inherited_methods), cls_name) + '},')
        class_list.append('};')

        content.extend(class_ids)
        content.extend(externals)
        content.extend(class_children)
        content.extend(class_list)

        content.append('NATIVE void initConst() {')
        # for i, v in enumerate(class_assigns):
        #     content.append('    CLASSES[{}].new = &{};'.format(i, v))
        for k, l in method_assigns.items():
            for i, v in enumerate(l):
                content.append('    {}[{}].func = &{};'.format(k, i, v))

        content.append('}')
        with open(Option().const_file, 'w') as f:
            f.write('\n'.join(content))
