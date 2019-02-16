import os

from ast import Class, Method, MethodGroup, Type, ObjectType, Primitive
from codegen import get_method_name
from context import Context
from phase import Phase
from report import Report
from symbol import SymbolTable

HEADER = """
#ifndef {header_define}
#define {header_define}

#include <play.h>

{class_struct}

{methods}

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


class CGen(Phase):
    def run(self):
        Report().begin("CGen")
        for cls in SymbolTable().get_classes():
            self.gen_class(cls)

        Report().end()

    def gen_class(self, cls: Class):
        class_struct = ''
        header_define = (cls.qualified_name.replace('.', '_') + '_h').upper()
        if cls.is_native:
            class_struct = 'Class(' + cls.qualified_name.replace('.', '_') + ', {\n});'
        methods = []
        for member in cls.members.values():
            if isinstance(member, MethodGroup):
                for method in member.methods:
                    if method.is_native:
                        methods.append(self.gen_method(method))
        for member in cls.static_members.values():
            for method in member.methods:
                if method.is_native:
                    methods.append(self.gen_method(method))

        if class_struct or methods:
            header = os.path.join(Context().c_source_location, cls.qualified_name.replace('.', '/') + '.h')
            source = os.path.join(Context().c_source_location, cls.qualified_name.replace('.', '/') + '.c')
            folder = os.path.dirname(header)
            if not os.path.exists(folder):
                os.makedirs(folder)
            if not os.path.exists(header):
                with open(header, 'w') as f:
                    f.write(HEADER.format(header_define=header_define, class_struct=class_struct, methods='\n'.join(m + ';' for m in methods)))
            if not os.path.exists(source):
                with open(source, 'w') as f:
                    f.write(CODE.format(file=cls.qualified_name.split('.')[-1], methods='\n'.join(m + '{\n}' for m in methods)))

    def gen_method(self, method: Method):
        parameters = ['{} {}'.format(get_c_type_name(p.type), p.name) for p in method.parameters]
        if not method.is_static:
            parameters.insert(0, '{} {}'.format(get_c_type_name(ObjectType(method.owner)), 'this'))
        return 'NATIVE {} {}({})'.format(
            get_c_type_name(method.return_type),
            get_method_name(method),
            ', '.join(parameters))
