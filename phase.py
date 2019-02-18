import os
from typing import List

from antlr4 import CommonTokenStream, FileStream

from ast import SourceFile, Package, Class, ObjectType, Field, Method, Parameter, Type, Block, ClassType
from type import ROOT_PACKAGE, BOOLEAN_TYPE, BYTE_TYPE, SHORT_TYPE, INT_TYPE, LONG_TYPE, FLOAT_TYPE, DOUBLE_TYPE, PLAY_PACKAGE, PRIMITIVES
from option import Option
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
        for src in Option().source_locations:
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
        Option().nodes[src] = parser.compilationUnit()
        package.source_files.append(src)


class EnterClass(Phase):
    def run(self):
        Report().begin("Enter class")
        self.enter(ROOT_PACKAGE)
        Report().end()

    def enter(self, package: Package):
        for src in package.source_files:
            self.enter_class(package, src, Option().nodes[src].classDeclaration())
        for child in package.children.values():
            if isinstance(child, Package):
                self.enter(child)

    def enter_class(self, package: Package, src: SourceFile, ctx: PlayParser.ClassDeclarationContext):
        cls = Class(ctx.IDENTIFIER().getText(), package, src)
        cls.is_interface = ctx.INTERFACE() is not None
        cls.is_native = ctx.NATIVE() is not None
        if cls.is_native and cls.is_interface:
            raise CompileException('interface {} cannot be native'.format(cls))
        Option().nodes[cls] = ctx
        package.put(cls)
        SymbolTable().enter_class(cls)


class ResolveImport(Phase):
    def run(self):
        Report().begin("Resolve import")
        for cls in SymbolTable().get_classes():
            self.resolve(cls.source)
        Report().end()

    def resolve(self, src: SourceFile):
        ctx: PlayParser.CompilationUnitContext = Option().nodes[src]
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
        ctx: PlayParser.ClassDeclarationContext = Option().nodes[cls]
        if ctx.classTypeList():
            for sc in ctx.classTypeList().classType():
                superclass = lookup_class(sc.IDENTIFIER().getText(), cls)
                if superclass.is_native:
                    raise CompileException('Cannot inherit from native class {}'.format(superclass))
                if superclass.is_interface:
                    cls.interfaces.append(superclass)
                elif cls.superclass:
                    raise CompileException("Class {} has more than one superclass".format(cls))
                elif superclass.is_native and superclass.qualified_name != 'play.Object':
                    raise CompileException("Cannot inherit native class {}".format(cls))
                else:
                    cls.superclass = superclass
        obj_cls = PLAY_PACKAGE.children['Object']
        if cls != obj_cls and not cls.is_interface and not cls.superclass:
            cls.superclass = obj_cls


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
            ctx: PlayParser.ClassDeclarationContext = Option().nodes[cls]
            for member in ctx.memberDeclaration():
                if member.methodDeclaration():
                    self.enter_method(cls, member.methodDeclaration())
                else:
                    self.enter_field(cls, member.fieldDeclaration())
            if not list(filter(lambda m: m.name == '<init>', cls.methods)):
                cls.methods.append(Method('<init>', cls, parameters=[], body=Block([])))
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
            raise CompileException('Native method {} in class {} cannot have body'.format(method.name, method.owner))
        if ctx.parameters():
            for v in ctx.parameters().variable():
                parameter_type = build_type(v.typeName(), cls)
                method.parameters.append(Parameter(v.IDENTIFIER().getText(), parameter_type))
        if ctx.typeName():
            method.return_type = build_type(ctx.typeName(), cls)
        Option().nodes[method] = ctx
        cls.put_method(method)

    def enter_field(self, cls: Class, ctx: PlayParser.FieldDeclarationContext):
        if cls.is_interface or cls.is_native:
            raise CompileException("Interface/native class {} cannot have fields".format(cls))
        field = Field(ctx.variable().IDENTIFIER().getText(), cls, build_type(ctx.variable().typeName(), cls))
        Option().nodes[field] = ctx
        cls.put_field(field)
