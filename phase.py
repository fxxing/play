import os
from typing import List, Dict

from antlr4 import CommonTokenStream, FileStream

from ast import SourceFile, Package, Class, ObjectType, Field, Method, Parameter, MethodGroup, ClassMemberType, Type, Block
from builtin import ROOT_PACKAGE, BOOLEAN_TYPE, BYTE_TYPE, SHORT_TYPE, INT_TYPE, LONG_TYPE, FLOAT_TYPE, DOUBLE_TYPE, PLAY_PACKAGE, PRIMITIVES
from context import Context
from env import lookup_class
from parser.PlayLexer import PlayLexer
from parser.PlayParser import PlayParser
from report import Report
from symbol import SymbolTable
from util import CompileException


def build_type(ctx: PlayParser.TypeNameContext, start: Class) -> Type:
    if ctx.classType():
        return ObjectType(lookup_class(ctx.classType().IDENTIFIER().getText(), start))
    if ctx.BOOLEAN():
        return BOOLEAN_TYPE
    if ctx.BYTE():
        return BYTE_TYPE
    if ctx.SHORT():
        return SHORT_TYPE
    if ctx.INT():
        return INT_TYPE
    if ctx.LONG():
        return LONG_TYPE
    if ctx.FLOAT():
        return FLOAT_TYPE
    if ctx.DOUBLE():
        return DOUBLE_TYPE
    raise CompileException("Error")


class Phase(object):
    def run(self):
        raise NotImplementedError


class Parse(Phase):
    def run(self):
        Report().begin("Parsing")
        for src in Context().source_locations:
            if not src.endswith('/'):
                src += '/'
            for root, dirs, files in os.walk(src):
                for file in files:
                    if not file.endswith('.play'):
                        continue
                    path = os.path.join(root, file)
                    Report().report("parse {}".format(path), lambda: self.parse(path, path[len(src):]))
        Report().end()

    def parse(self, path, rel_path):
        package = ''
        if '/' in rel_path:
            package = rel_path[:rel_path.rfind('/')].replace('/', '.')
        package = SymbolTable().enter_package(package)
        src = SourceFile(path)
        parser = PlayParser(CommonTokenStream(PlayLexer(FileStream(path, encoding='utf-8'))))
        Context().nodes[src] = parser.compilationUnit()
        package.source_files.append(src)


class EnterClass(Phase):
    def run(self):
        Report().begin("Enter class")
        self.enter(ROOT_PACKAGE)
        Report().end()

    def enter(self, package: Package):
        for src in package.source_files:
            self.enter_class(package, src, Context().nodes[src].classDeclaration())
        for child in package.children.values():
            if isinstance(child, Package):
                self.enter(child)

    def enter_class(self, package: Package, src: SourceFile, ctx: PlayParser.ClassDeclarationContext):
        cls = Class(ctx.IDENTIFIER().getText(), package, src)
        cls.is_interface = ctx.INTERFACE() is not None
        cls.is_native = ctx.NATIVE() is not None
        if cls.is_native and cls.is_interface:
            raise CompileException('interface {} cannot be native'.format(cls.qualified_name))
        Context().nodes[cls] = ctx
        package.put(cls)
        SymbolTable().enter_class(cls)


class ResolveImport(Phase):
    def run(self):
        Report().begin("Resolve import")
        for cls in SymbolTable().get_classes():
            self.resolve(cls.source)
        Report().end()

    def resolve(self, src: SourceFile):
        ctx: PlayParser.CompilationUnitContext = Context().nodes[src]
        for i in ctx.importDeclaration():
            cls = SymbolTable().get_class(i.qualifiedName().getText())
            src.imports[cls.name] = cls


class BuildHierarchy(Phase):
    def run(self):
        Report().begin("Build hierarchy")
        for cls in SymbolTable().get_classes():
            self.build(cls)
        Report().end()

    def build(self, cls: Class):
        ctx: PlayParser.ClassDeclarationContext = Context().nodes[cls]
        if not ctx.classTypeList():
            return
        for sc in ctx.classTypeList().classType():
            superclass = lookup_class(sc.IDENTIFIER().getText(), cls)
            if superclass.is_native:
                raise CompileException('Cannot inherit from native class {}'.format(superclass.qualified_name))
            if superclass.is_interface:
                cls.interfaces.append(superclass)
            elif cls.superclass:
                raise CompileException("Class {} has more than one superclass".format(cls.qualified_name))
            else:
                cls.superclass = superclass
        if not cls.is_interface and not cls.superclass:
            cls.superclass = PLAY_PACKAGE.children['Object']


class CheckCircularDependency(Phase):
    def __init__(self):
        self.visited = set()
        self.checked = set()

    def run(self):
        Report().begin("Check circular dependency")
        for cls in SymbolTable().get_classes():
            if cls not in self.checked:
                self.check(cls, [])
        Report().end()

    def check(self, current: Class, path: List[Class]):
        if current in self.visited:
            return
        self.visited.add(current)
        superclasses = current.superclasses
        for sc in superclasses:
            try:
                index = path.index(sc)
                chain = []
                for c in path[index:]:
                    chain.append(c.qualified_name)
                chain.append(current.qualified_name)
                chain.append(path[index].qualified_name)
                raise CompileException("There's a circular hierarchy dependency: {}".format(' -> '.join(chain)))
            except:
                pass

        new_path = path + [current]
        for sc in superclasses:
            self.check(sc, new_path)
        self.checked.add(current)


def is_native_type(type: Type) -> bool:
    return type in PRIMITIVES or type.cls in {PLAY_PACKAGE.children['Object'], PLAY_PACKAGE.children['String']}

class EnterMember(Phase):
    def run(self):
        Report().begin("Enter member")
        for cls in SymbolTable().get_classes():
            ctx: PlayParser.ClassDeclarationContext = Context().nodes[cls]
            for member in ctx.memberDeclaration():
                if member.methodDeclaration():
                    self.enter_method(cls, member.methodDeclaration())
                else:
                    self.enter_field(cls, member.fieldDeclaration())
            if '<init>' not in cls.members:
                cls.members['<init>'] = MethodGroup('<init>', {Method('<init>', cls, block=Block([]))})
        Report().end()

    def enter_method(self, cls: Class, ctx: PlayParser.MethodDeclarationContext):
        name = ctx.IDENTIFIER().getText()
        if name == cls.name:
            name = '<init>'
        method = Method(name, cls)
        method.is_native = ctx.NATIVE() is not None
        method.is_static = ctx.STATIC() is not None
        method.is_abstract = not method.is_native and ctx.block() is None
        if method.is_native and ctx.block() is not None:
            raise CompileException('Native method {} in class {} cannot have body'.format(method.name, method.owner.qualified_name))
        if ctx.parameters():
            for v in ctx.parameters().variable():
                parameter_type = build_type(v.typeName(), cls)
                # if method.is_native:
                #     if not is_native_type(parameter_type):
                #         raise CompileException('native method {}.{} can only take primitive, String or Object as parameter'.format(cls.qualified_name, method.name))

                method.parameters.append(Parameter(v.IDENTIFIER().getText(), parameter_type))
        if ctx.typeName():
            method.return_type = build_type(ctx.typeName(), cls)
            # if method.is_native:
            #     if not is_native_type(method.return_type):
            #         raise CompileException('native method {}.{} can only return primitive, String or Object'.format(cls.qualified_name, method.name))
        # if ctx.classTypeList():
        #     for ct in ctx.classTypeList().classType():
        #         method.throws.append(lookup_class(ct.IDENTIFIER().getText(), cls))
        Context().nodes[method] = ctx
        cls.put(method)

    def enter_field(self, cls: Class, ctx: PlayParser.FieldDeclarationContext):
        if cls.is_interface:
            raise CompileException("Interface {} cannot have fields".format(cls.qualified_name))
        field = Field(ctx.variable().IDENTIFIER().getText(), cls, build_type(ctx.variable().typeName(), cls))
        Context().nodes[field] = ctx
        cls.put(field)


def has_same_signature(self: Method, other: Method) -> bool:
    # TODO move to method
    if len(self.parameters) != len(other.parameters):
        return False
    for i, p1 in enumerate(self.parameters):
        p2 = other.parameters[i]
        if p1.type != p2.type:
            return False
    return True


class CheckDuplicatedSignature(Phase):
    def run(self):
        Report().begin("Check duplicated signature")
        for cls in SymbolTable().get_classes():
            for child in cls.members.values():
                if isinstance(child, MethodGroup):
                    self.check(child)
            for child in cls.static_members.values():
                self.check(child)
        Report().end()

    def check(self, group: MethodGroup):
        methods = list(group.methods)
        for i, m1 in enumerate(methods):
            for j in range(i + 1, len(methods)):
                if has_same_signature(m1, methods[j]):
                    raise CompileException("method in class {} with name {} has same signature".format(m1.owner.qualified_name, m1.name))


class InheritMember(Phase):
    def run(self):
        Report().begin("Inherit member")
        for cls in SymbolTable().get_classes():
            self.inherit(cls)
        Report().end()

    def inherit(self, current: Class) -> Dict[str, ClassMemberType]:
        if current.inherited_members is not None:
            return current.inherited_members
        super_members: Dict[str, ClassMemberType] = {}
        for superclass in current.superclasses:
            self.union_super(super_members, self.inherit(superclass))

        inherited_members: Dict[str, ClassMemberType] = dict(current.members)
        for name, super_member in super_members.items():
            if name == '<init>':
                continue
            if isinstance(super_member, Field):
                if name in inherited_members and not super_member.is_private:
                    raise CompileException("Class {} override field {} of {}".format(current.qualified_name, name, super_member.owner.qualified_name))
            else:
                this_group = inherited_members.get(name)
                if not this_group:
                    this_group = MethodGroup(name)
                if not isinstance(this_group, MethodGroup):
                    raise CompileException("Class {} override {} of {} with different type".format(current.qualified_name, name, super_member.first.owner.qualified_name))
                new_methods = set(this_group.methods)
                self.inherit_from(new_methods, super_member.methods)
                inherited_members[name] = MethodGroup(name, new_methods)
        if not current.is_interface:
            for group in filter(lambda x: isinstance(x, MethodGroup), inherited_members.values()):
                if any(method.is_abstract for method in group.methods):
                    current.is_abstract = True
                    break
        current.inherited_members = inherited_members
        return current.inherited_members

    def inherit_from(self, found, methods):
        for m in methods:
            if not m.can_inherit():
                continue
            for nm in found:
                if self.is_same_method(m, nm):
                    break
            else:
                found.add(m)

    def is_same_method(self, m1: Method, m2: Method) -> bool:
        if has_same_signature(m1, m2):
            if m1.return_type != m2.return_type:
                raise CompileException("Class {} conflict method {} with different return type".format(m2.owner.qualified_name, m2.name))
            return True
        return False

    def union_super(self, members: Dict[str, ClassMemberType], union_members: Dict[str, ClassMemberType]):
        for name, union_member in union_members.items():
            if name in members:
                group = members[name]
                if isinstance(group, Field):
                    raise CompileException("Class {} override field {} in {} with method".format(
                        union_member.first.owner.qualified_name, group.owner.qualified_name, name))

                new_methods = {m for m in group.methods if m.can_inherit()}
                self.inherit_from(new_methods, union_member.methods)
            else:
                new_methods = {m for m in union_member.methods if not m.can_inherit()}
            members[name] = MethodGroup(name, new_methods)
