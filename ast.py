import functools
from typing import List, Set, Dict, Union, Optional

from util import CompileException


class Package(object):
    def __init__(self, name: str, owner=None):
        self.name = name
        self.owner = owner
        self.source_files: List[SourceFile] = []
        self.children: Dict[str, PackageChildType] = {}

    def put(self, child):
        if child.name in self.children and self.children[child.name] != child:
            raise CompileException('Duplicated symbol {} in package {}'.format(child.name, self.qualified_name))
        self.children[child.name] = child

    @property
    def qualified_name(self) -> str:
        if not self.owner:
            return self.name
        qualified_name = self.owner.qualified_name
        if qualified_name:
            return qualified_name + '.' + self.name
        return self.name

    def __repr__(self):
        return self.qualified_name


class SourceFile(object):
    def __init__(self, name: str):
        self.name = name
        self.imports: Dict[str, Class] = {}


class Class(object):
    def __init__(self, name: str, owner: Package = None, source: SourceFile = None, **kwargs):
        self.name = name
        self.owner = owner
        self.source = source
        self.is_interface = False
        self.is_abstract = False
        self.is_native = False
        self.superclass: Optional[Class] = None
        self.interfaces: List[Class] = []
        self.fields: List[Field] = []
        self.methods: List[Method] = []
        self.static_methods: List[Method] = []
        self.__inherited_methods: List[Method] = None
        self.__inherited_fields: List[Field] = None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def put_method(self, method):
        methods = self.static_methods if method.is_static else self.methods
        for m in methods:
            if m.has_same_signature(method):
                raise CompileException('Duplicated method {} in class {}'.format(method.name, self))
        methods.append(method)

    def put_field(self, field):
        for f in self.fields:
            if f.name == field.name:
                raise CompileException('Duplicated field {} in class {}'.format(field.name, self))
        self.fields.append(field)

    @property
    def inherited_fields(self):
        # type: ()-> List[Field]
        if self.__inherited_fields is not None:
            return self.__inherited_fields
        super_fields = self.superclass.inherited_fields if self.superclass else []
        self.__inherited_fields = super_fields + self.fields
        return self.__inherited_fields

    @property
    def inherited_methods(self):
        # type: ()-> List[Method]
        if self.__inherited_methods is not None:
            return self.__inherited_methods
        methods = list(filter(lambda m: m.can_inherit(), self.superclass.inherited_methods)) if self.superclass else [][:]
        for interface in self.interfaces:
            for interface_method in interface.inherited_methods:
                replace_method = None
                for i, method in enumerate(methods):
                    if method.has_same_signature(interface_method):
                        if method.is_abstract and not interface_method.is_abstract:
                            replace_method = i
                        break
                else:
                    methods.append(interface_method)
                if replace_method:
                    methods[replace_method] = interface_method

        for this_method in self.methods:
            replace_method = None
            for i, method in enumerate(methods):
                if method.has_same_signature(this_method):
                    replace_method = i
                    break
            else:
                methods.append(this_method)
            if replace_method:
                methods[replace_method] = this_method

        def cmp_method(m1: Method, m2: Method) -> int:
            if m2.is_private:
                return -1
            elif m1.is_private:
                return 1
            return 0

        self.__inherited_methods = sorted(methods, key=functools.cmp_to_key(cmp_method))
        return self.__inherited_methods

    def subclass_of(self, cls):
        # type: (Class) -> bool
        for superclass in self.superclasses:
            if superclass == cls:
                return True
            if superclass.subclass_of(cls):
                return True
        return False

    def lookup_method(self, name: str, arguments, is_static=False):
        # type: (str, List[Type], bool) -> Method
        methods = self.static_methods if is_static else self.inherited_methods
        for method in methods:
            if method.name != name:
                continue
            if len(method.parameters) != len(arguments):
                continue
            for i, parameter in enumerate(method.parameters):
                if arguments[i] != parameter.type:
                    break
            else:
                return method

        raise CompileException('Cannot find method {} with parameters {}'.format(name, arguments))

    def lookup_super_method(self, name: str, arguments):
        # type: (str, List[Type]) -> Method
        method = self.superclass.lookup_method(name, arguments)
        if not method:
            for interface in self.interfaces:
                method = interface.lookup_method(name, arguments)
                if method.is_abstract:
                    method = None
        if method:
            return method
        raise CompileException('Cannot find method {} with parameters {}'.format(name, arguments))

    def lookup_field(self, name: str, silence=False):
        # type: (str) -> Field
        for field in self.inherited_fields:
            if field.name == name:
                return field
        if not silence:
            raise CompileException('Cannot find field {}'.format(name))

    @property
    def qualified_name(self) -> str:
        qualified_name = self.owner.qualified_name
        if qualified_name:
            return qualified_name + '.' + self.name
        return self.name

    @property
    def superclasses(self):
        # type: ()-> List[Class]
        return ([self.superclass] if self.superclass else []) + self.interfaces

    def __repr__(self):
        return self.qualified_name

    def __eq__(self, other):
        return self.qualified_name == other.qualified_name

    def __hash__(self):
        return hash(self.qualified_name)


class Type(object):
    pass


class Method(object):
    def __init__(self, name: str, owner: Class, **kwargs):
        self.name = name
        self.owner = owner
        self.is_static = False
        self.is_native = False
        self.is_abstract = False
        self.parameters: List[Parameter] = []
        self.return_type: Type = None
        # self.throws: List[Class] = []
        self.body: Block = None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return 'Method({})'.format(self.name)

    @property
    def is_private(self):
        return self.name.startswith("__")

    def can_inherit(self):
        return not (self.name == '<init>' or self.is_private)

    def has_same_signature(self, other) -> bool:
        # type: (Method) -> bool
        if self.name != other.name:
            return False
        if len(self.parameters) != len(other.parameters):
            return False
        for i, p1 in enumerate(self.parameters):
            p2 = other.parameters[i]
            if p1.type != p2.type:
                return False
        return True


class Field(object):
    def __init__(self, name: str, owner: Class, type: Type):
        self.name = name
        self.type = type
        self.owner = owner
        self.initializer: Optional[Expr] = None

    @property
    def is_private(self):
        return self.name.startswith("__")

    def __repr__(self):
        return 'Field({})'.format(self.name)


class Primitive(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Primitive) and self.name == other.name

    def __repr__(self):
        return self.name


class ObjectType(Type):
    def __init__(self, cls: Class):
        self.cls = cls

    def __eq__(self, other):
        return isinstance(other, ObjectType) and self.cls == other.cls

    def __repr__(self):
        return self.cls.qualified_name


class ClassType(ObjectType):
    def __init__(self, cls: Class):
        super().__init__(cls)


class Parameter(object):
    def __init__(self, name: str, type: Type):
        self.name = name
        self.type = type


PackageChildType = Union[Package, Class]


class Expr(object):
    def __init__(self):
        self.type: Type = None


class Variable(Expr):
    def __init__(self, name: str, type):
        super().__init__()
        self.name = name
        self.type: Type = type


class BinExpr(Expr):
    def __init__(self, op, left: Expr, right: Expr):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right


class UnaryExpr(Expr):
    def __init__(self, op: str, expr: Expr):
        super().__init__()
        self.op = op
        self.expr = expr
        self.type = expr.type


class CastExpr(Expr):
    def __init__(self, expr: Expr, type: Type):
        super().__init__()
        self.expr = expr
        self.type = type


class ClassCreation(Expr):
    def __init__(self, cls: Class, constructor: Method, arguments: List[Expr]):
        super().__init__()
        self.cls = cls
        self.constructor = constructor
        self.arguments = arguments
        self.type = ObjectType(cls)


class MethodCall(Expr):
    def __init__(self, select: Expr, method: Method, arguments: List[Expr]):
        super().__init__()
        self.select = select
        self.method = method
        self.arguments = arguments
        self.type = method.return_type


class ClassExpr(Expr):
    def __init__(self, cls: Class):
        super().__init__()
        self.cls = cls
        self.type = ClassType(cls)


class FieldAccess(Expr):
    def __init__(self, select: Optional[Expr], field: Field):
        super().__init__()
        self.select = select
        self.field = field
        self.type = field.type


class Literal(Expr):
    def __init__(self, value, type: Type):
        super().__init__()
        self.value = value
        self.type = type


class Statement(object):
    fields = ()


class Block(Statement):
    fields = ('statements',)

    def __init__(self, statements: List[Statement]):
        self.statements = statements


class LoopStatement(Statement):
    fields = ('block',)

    def __init__(self, expr: Expr, block: Block):
        self.expr = expr
        self.block = block


class WhileStatement(LoopStatement):
    def __init__(self, expr: Expr, block: Block):
        super().__init__(expr, block)


class BreakStatement(Statement):
    pass


class ContinueStatement(Statement):
    pass


class IfStatement(Statement):
    fields = ('block', 'otherwise')

    def __init__(self, expr: Expr, then: Block, otherwise: Optional[Block]):
        self.expr = expr
        self.then = then
        self.otherwise = otherwise


class AssignStatement(Statement):
    def __init__(self, var: Expr, expr: Expr):
        self.var = var
        self.expr = expr


class ReturnStatement(Statement):
    def __init__(self, expr: Expr):
        self.expr = expr


class ExprStatement(Statement):
    def __init__(self, expr: Expr):
        self.expr = expr
