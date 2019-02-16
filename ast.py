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
        self.interfaces = []
        self.members: Dict[str, ClassMemberType] = {}
        self.static_members: Dict[str, MethodGroup] = {}
        self.inherited_members: Dict[str, ClassMemberType] = None
        self.inherited_fields: List[Field] = None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def put(self, child):
        if isinstance(child, Method):
            members = self.static_members if child.is_static else self.members
            group = members.get(child.name)
            if group:
                if not isinstance(group, MethodGroup):
                    raise CompileException('Duplicated symbol {} in package {}'.format(child.name, self.qualified_name))
            else:
                group = MethodGroup(child.name)
                members[child.name] = group
            group.methods.add(child)
        elif child.name in self.members and self.members[child.name] != child:
            raise CompileException('Duplicated symbol {} in package {}'.format(child.name, self.qualified_name))
        else:
            self.members[child.name] = child

    def get_inherited_fields(self):
        if self.inherited_fields is not None:
            return self.inherited_fields
        super_fields = self.superclass.get_inherited_fields() if self.superclass else []
        this_fields = list(filter(lambda m: isinstance(m, Field), self.members.values()))
        self.inherited_fields = super_fields + this_fields
        return self.inherited_fields

    def subclass_of(self, cls):
        # type: (Class) -> bool
        for superclass in self.superclasses:
            if superclass.qualified_name == cls.qualified_name:
                return True
            if superclass.subclass_of(cls):
                return True
        return False

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
        return not (self.is_static or self.is_private)


class MethodGroup(object):
    def __init__(self, name: str, methods: Set[Method] = None):
        self.name = name
        self.methods: Set[Method] = methods if methods else set()

    @property
    def first(self):
        return list(self.methods)[0]


class Field(object):
    def __init__(self, name: str, owner: Class, type: Type):
        self.name = name
        self.type = type
        self.owner = owner
        self.initializer: Optional[Expr] = None

    @property
    def is_private(self):
        return self.name.startswith("__")


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
        return isinstance(other, ObjectType) and self.cls.qualified_name == other.cls.qualified_name

    def __repr__(self):
        return self.cls.qualified_name


class ClassType(ObjectType):
    def __init__(self, cls: Class):
        super().__init__(cls)


class Parameter(object):
    def __init__(self, name: str, type: Type):
        self.name = name
        self.type = type


ClassMemberType = Union[Field, MethodGroup]
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

    def __init__(self, expression: Expr, block: Block):
        self.expression = expression
        self.block = block


class WhileStatement(LoopStatement):
    def __init__(self, expression: Expr, block: Block):
        super().__init__(expression, block)


class BreakStatement(Statement):
    pass


class ContinueStatement(Statement):
    pass


class IfStatement(Statement):
    fields = ('block', 'otherwise')

    def __init__(self, expression: Expr, then: Block, otherwise: Optional[Block]):
        self.expression = expression
        self.then = then
        self.otherwise = otherwise


class AssignStatement(Statement):
    def __init__(self, var: Expr, expr: Expr):
        self.var = var
        self.expr = expr


class ReturnStatement(Statement):
    def __init__(self, expression: Expr):
        self.expression = expression


# class ThrowStatement(Statement):
#     def __init__(self, expression: Expr):
#         self.expression = expression


# class TryStatement(Statement):
#     fields = ('block', 'catches', 'finally_block')
#
#     class Catch(Statement):
#         fields = ('block',)
#
#         def __init__(self, var, types: Set[Class], block: Block):
#             self.var = var
#             self.types = types
#             self.block = block
#
#     def __init__(self, block: Block):
#         self.block = block
#         self.catches: List[TryStatement.Catch] = []
#         self.finally_block: Optional[Block] = None


class ExprStatement(Statement):
    def __init__(self, expr: Expr):
        self.expr = expr
