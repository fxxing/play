import hashlib
from typing import List

from llvmlite import ir

from ast import Class, Method, MethodGroup, Field, Type, ObjectType, Block, Statement, ExprStatement, WhileStatement, IfStatement, AssignStatement, ReturnStatement, Expr, \
    Variable, BinExpr, UnaryExpr, CastExpr, ClassCreation, MethodCall, ClassExpr, FieldAccess, Literal, Parameter
from builtin import BOOLEAN_TYPE, BYTE_TYPE, SHORT_TYPE, INT_TYPE, LONG_TYPE, FLOAT_TYPE, DOUBLE_TYPE, REAL_NUMBERS, PLAY_PACKAGE
from context import Context
from flow import is_terminal
from phase import Phase
from report import Report
from symbol import SymbolTable
from translate import lookup_method
from util import never_be_here, class_name

int1 = ir.IntType(1)
int8 = ir.IntType(8)
int16 = ir.IntType(16)
int32 = ir.IntType(32)
int64 = ir.IntType(64)


def create_type(type: Type) -> ir.Type:
    if not type:
        return ir.VoidType()
    if isinstance(type, ObjectType):
        return create_class_struct(type.cls).as_pointer()
    if type == BOOLEAN_TYPE:
        return ir.IntType(1)
    if type == BYTE_TYPE:
        return ir.IntType(8)
    if type == SHORT_TYPE:
        return ir.IntType(16)
    if type == INT_TYPE:
        return ir.IntType(32)
    if type == LONG_TYPE:
        return ir.IntType(64)
    if type == FLOAT_TYPE:
        return ir.FloatType()
    if type == DOUBLE_TYPE:
        return ir.DoubleType()


def create_class_struct(cls: Class) -> ir.Type:
    qualified_name = cls.qualified_name
    name = qualified_name.replace('.', '_')
    if name in ir.global_context.identified_types:
        return ir.global_context.get_identified_type(name)
    type = ir.global_context.get_identified_type(name)
    if cls.is_native:
        return type

    fields = cls.get_inherited_fields()
    elements = []
    for field in fields:
        elements.append(create_type(field.type))
    type.set_body(*elements)
    return type


def get_type_name(type: Type) -> str:
    if not type:
        return 'V'
    if isinstance(type, ObjectType):
        qualified_name = type.cls.qualified_name
        if qualified_name == 'play.String':
            return 'T'
        if qualified_name == 'play.Object':
            return 'O'
        return 'C{}$'.format(qualified_name.replace('.', '_'))
    if type == BOOLEAN_TYPE:
        return 'Z'
    if type == BYTE_TYPE:
        return 'B'
    if type == SHORT_TYPE:
        return 'S'
    if type == INT_TYPE:
        return 'I'
    if type == LONG_TYPE:
        return 'L'
    if type == FLOAT_TYPE:
        return 'F'
    if type == DOUBLE_TYPE:
        return 'D'


def get_method_name(method: Method) -> str:
    ret = [method.owner.qualified_name.replace('.', '_')]
    if method.is_static:
        ret.append('s')
    ret.append(method.name)
    ret.append(get_type_name(method.return_type))
    ret.append(''.join([get_type_name(p.type) for p in method.parameters]))
    return '_'.join(ret)


METHODS = {}

FUNCTIONS = {}


def get_function(module, name, return_type, types):
    if name not in FUNCTIONS:
        type = ir.FunctionType(return_type, types)
        # print(type)
        func = ir.Function(module, type, name=name)
        FUNCTIONS[name] = func
    return FUNCTIONS[name]


STRINGS = {}


def new_string(module, s):
    if s in STRINGS:
        return STRINGS[s]
    es = s.encode('utf-8')
    b = bytearray(es)
    b.append(0)
    n = len(b)
    value = ir.Constant(ir.ArrayType(ir.IntType(8), n), b)
    data = ir.GlobalVariable(module, value.type, name='str{}'.format(hashlib.md5(es).hexdigest()))
    data.linkage = 'internal'
    data.global_constant = True
    data.initializer = value
    STRINGS[s] = data
    return data


class BasicBlock(object):
    def __init__(self):
        self.block: ir.Block = None
        self.blocks: List[BasicBlock] = []

    def get_blocks(self):
        ret = [self.block]
        for b in self.blocks:
            ret.extend(b.get_blocks())
        return ret

    def __repr__(self):
        return self.block.name


class GenEnv(object):
    def __init__(self, method: Method):
        self.method = method
        self.scopes = []

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def enter(self, name: str, value: ir.Value):
        self.scopes[-1][name] = value

    def lookup(self, name) -> ir.Value:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]


class Codegen(Phase):
    def __init__(self):
        # TODO hash method
        self.module = ir.Module(name='play')
        self.builder: ir.IRBuilder = None
        self.current_method: Method = None
        self.env: GenEnv = None
        self.loop_context = []
        self.basic_blocks = []

    def run(self):
        obj_ptr = create_class_struct(PLAY_PACKAGE.children['Object']).as_pointer()
        str_ptr = create_class_struct(PLAY_PACKAGE.children['String']).as_pointer()
        get_function(self.module, 'new_string', str_ptr, [ir.PointerType(ir.IntType(8))])
        get_function(self.module, 'new_class', obj_ptr, [])
        get_function(self.module, 'cast', obj_ptr.as_pointer(), [obj_ptr])
        Report().begin("Codegen")
        for cls in SymbolTable().get_classes():
            self.gen_class(cls)

        Report().end()

        self.gen_main()

        with open(Context().code_gen_file, 'w') as f:
            f.write(str(self.module))

    def get_method(self, method: Method) -> ir.Function:
        name = get_method_name(method)
        if name not in METHODS:
            parameters = [create_type(p.type) for p in method.parameters]
            if not method.is_static:
                parameters.insert(0, create_class_struct(method.owner).as_pointer())
            type = ir.FunctionType(create_type(method.return_type), parameters)
            # print(type)
            func = ir.Function(self.module, type, name=get_method_name(method))
            METHODS[name] = func
        return METHODS[name]

    def gen_class(self, cls: Class):
        for member in cls.members.values():
            if isinstance(member, MethodGroup):
                for method in member.methods:
                    self.gen_method(method)

        for member in cls.static_members.values():
            for method in member.methods:
                self.gen_method(method)

    def gen_method(self, method: Method):
        self.current_method = method
        self.env = GenEnv(method)
        func = self.get_method(method)
        if not method.body:
            return
        self.env.push()
        for field in method.owner.get_inherited_fields():
            self.env.enter(field.name, field)
        self.env.push()

        entry = self.basic_block(func, 'entry')
        self.basic_blocks = [entry]
        self.builder = ir.IRBuilder(entry.block)
        # self.builder = ir.IRBuilder(func.append_basic_block('entry'))
        parameters = self.current_method.parameters[:]
        if not method.is_static:
            parameters.insert(0, Parameter('this', ObjectType(method.owner)))
        for i, arg in enumerate(self.builder.function.args):
            self.env.enter(parameters[i].name, arg)
        self.block(method.body)
        func.blocks = entry.get_blocks()
        max_i = len(func.blocks) - 1
        for i, block in enumerate(func.blocks):
            if not block.is_terminated:
                if i < max_i:
                    ir.IRBuilder(block).branch(self.builder.function.blocks[i + 1])
                else:
                    ir.IRBuilder(block).ret_void()
        self.env.pop()

        self.env.pop()

    def gen_main(self):
        type = ir.FunctionType(ir.IntType(32), [])
        # print(type)
        func = ir.Function(self.module, type, name='main')
        entry = func.append_basic_block('entry')
        builder = ir.IRBuilder(entry)
        bootstrap_class = SymbolTable().get_class(Context().bootstrap_class)
        method = lookup_method(bootstrap_class, 'main', [], is_static=True)
        builder.call(self.get_method(method), [])
        builder.ret(ir.Constant(ir.IntType(32), 0))

    def basic_block(self, func, name):
        block = BasicBlock()
        block.block = ir.Block(parent=func, name=name)
        if self.basic_blocks:
            self.basic_blocks[-1].blocks.append(block)
        return block

    def block(self, block: Block):
        self.env.push()
        for statement in block.statements:
            self.statement(statement)
            if is_terminal(statement):
                break
        self.env.pop()

    def statement(self, statement: Statement):
        getattr(self, class_name(statement))(statement)

    def while_statement(self, statement: WhileStatement):
        loop = self.basic_block(self.builder.function, 'while.loop')
        body = self.basic_block(self.builder.function, 'while.body')
        end = self.basic_block(self.builder.function, 'while.end')
        self.builder.branch(loop.block)

        self.builder = ir.IRBuilder(loop.block)
        self.basic_blocks.append(loop)
        cond = self.expr(statement.expr)
        self.basic_blocks.pop()
        self.builder.cbranch(cond, body.block, end.block)

        self.loop_context.append({'loop': loop.block, 'end': end.block})
        self.basic_blocks.append(body)
        self.builder = ir.IRBuilder(body.block)
        self.block(statement.block)
        self.basic_blocks.pop()
        if not self.builder.block.is_terminated:
            self.builder.branch(loop.block)
        self.loop_context.pop()

        self.basic_blocks.append(end)
        self.builder = ir.IRBuilder(end.block)

    def break_statement(self, _):
        self.builder.branch(self.loop_context[-1]['end'])

    def continue_statement(self, _):
        self.builder.branch(self.loop_context[-1]['loop'])

    def if_statement(self, statement: IfStatement):
        cond = self.expr(statement.expr)
        then = self.basic_block(self.builder.function, 'if.then')
        if statement.otherwise:
            otherwise = self.basic_block(self.builder.function, 'if.else')
        else:
            otherwise = None
        end = self.basic_block(self.builder.function, 'if.end')
        self.builder.cbranch(cond, then.block, (otherwise or end).block)

        self.builder = ir.IRBuilder(then.block)
        self.basic_blocks.append(then)
        self.block(statement.then)
        if not self.builder.block.is_terminated:
            self.builder.branch(end.block)
        self.basic_blocks.pop()

        if otherwise:
            self.builder = ir.IRBuilder(otherwise.block)
            self.basic_blocks.append(otherwise)
            self.block(statement.otherwise)
            self.builder.branch(end.block)
            self.basic_blocks.pop()

        self.basic_blocks.append(end)
        self.builder = ir.IRBuilder(end.block)

    def assign_statement(self, statement: AssignStatement):
        expr = self.expr(statement.expr)
        if isinstance(statement.var, Variable):
            var = self.assign_variable(statement.var)
        else:
            var = self.field_access(statement.var, load=False)
        self.builder.store(expr, var)

    def assign_variable(self, expr: Variable) -> ir.Value:
        var = self.env.lookup(expr.name)
        if isinstance(var, Field):
            return self.builder.gep(self.builder.function.args[0],
                                    [ir.Constant(int32, 0), ir.Constant(int32, self.current_method.owner.get_inherited_fields().index(var))], inbounds=True,
                                    name=var.name + '_ptr')
        if not var:
            var = self.builder.alloca(create_type(expr.type), name=expr.name)
            self.env.enter(expr.name, var)
        return var

    def return_statement(self, statement: ReturnStatement):
        if statement.expr:
            self.builder.ret(self.expr(statement.expr))
        else:
            self.builder.ret(None)

    def expr_statement(self, statement: ExprStatement):
        self.expr(statement.expr)

    def expr(self, expr: Expr) -> ir.Value:
        return getattr(self, class_name(expr))(expr)

    def variable(self, expr: Variable) -> ir.Value:
        var = self.env.lookup(expr.name)
        if isinstance(var, Field):
            ptr = self.builder.gep(self.builder.function.args[0], [ir.Constant(int32, 0), ir.Constant(int32, self.current_method.owner.get_inherited_fields().index(var))], inbounds=True,
                                   name=var.name + '_ptr')
            return self.builder.load(ptr, name=var.name)
        assert var
        return var

    def bin_expr(self, expr: BinExpr) -> ir.Value:
        is_float = expr.left.type in REAL_NUMBERS

        if expr.op in {'||', '&&'}:
            cond_ptr = self.builder.alloca(ir.IntType(1), name='cond_ptr')
            cond_left = self.basic_block(self.builder.function, 'cond.left')
            true = self.basic_block(self.builder.function, 'cond.true')
            false = self.basic_block(self.builder.function, 'cond.false')
            end = self.basic_block(self.builder.function, 'cond.end')
            if expr.op == '||':
                self.builder.cbranch(self.expr(expr.left), true.block, cond_left.block)
            else:
                self.builder.cbranch(self.expr(expr.left), cond_left.block, false.block)

            self.builder = ir.IRBuilder(true.block)
            self.builder.store(ir.Constant(ir.IntType(1), 1), cond_ptr)
            self.builder.branch(end.block)

            self.builder = ir.IRBuilder(false.block)
            self.builder.store(ir.Constant(ir.IntType(1), 0), cond_ptr)
            self.builder.branch(end.block)

            self.builder = ir.IRBuilder(cond_left.block)
            self.basic_blocks.append(cond_left)
            self.builder.cbranch(self.expr(expr.right), true.block, false.block)
            self.basic_blocks.pop()

            self.builder = ir.IRBuilder(end.block)
            return self.builder.load(cond_ptr, name='cond')
        if expr.op == '+':
            if is_float:
                return self.builder.fadd(self.expr(expr.left), self.expr(expr.right))
            return self.builder.add(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '-':
            if is_float:
                return self.builder.fsub(self.expr(expr.left), self.expr(expr.right))
            return self.builder.sub(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '*':
            if is_float:
                return self.builder.fmul(self.expr(expr.left), self.expr(expr.right))
            return self.builder.mul(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '/':
            if is_float:
                return self.builder.fdiv(self.expr(expr.left), self.expr(expr.right))
            return self.builder.sdiv(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '%':
            if is_float:
                return self.builder.frem(self.expr(expr.left), self.expr(expr.right))
            return self.builder.srem(self.expr(expr.left), self.expr(expr.right))
        if expr.op in {'<', '>', '<=', '>=', '==', '!='}:
            if is_float:
                return self.builder.fcmp_ordered(expr.op, self.expr(expr.left), self.expr(expr.right))
            return self.builder.icmp_signed(expr.op, self.expr(expr.left), self.expr(expr.right))
        if expr.op == '<<':
            return self.builder.shl(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '>>':
            return self.builder.lshr(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '>>>':
            return self.builder.ashr(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '|':
            return self.builder.or_(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '^':
            return self.builder.xor(self.expr(expr.left), self.expr(expr.right))
        if expr.op == '&':
            return self.builder.and_(self.expr(expr.left), self.expr(expr.right))
        never_be_here()

    def unary_expr(self, expr: UnaryExpr) -> ir.Value:
        if expr.op == '-':
            return self.builder.neg(self.expr(expr.expr))
        if expr.op in {'~', '!'}:
            return self.builder.not_(self.expr(expr.expr))
        return self.expr(expr.expr)

    def cast_expr(self, expr: CastExpr) -> ir.Value:
        obj_ptr = create_class_struct(PLAY_PACKAGE.children['Object']).as_pointer()
        return self.builder.bitcast(self.builder.call(FUNCTIONS['cast'], [self.builder.bitcast(self.expr(expr.expr), obj_ptr)]), create_type(expr.type))

    def class_creation(self, expr: ClassCreation) -> ir.Value:
        # FIXME real new
        return self.builder.bitcast(self.builder.call(FUNCTIONS['new_class'], []), create_class_struct(expr.cls).as_pointer())

    def method_call(self, expr: MethodCall) -> ir.Value:
        # TODO for member, invoke by lookup
        if isinstance(expr.select, ClassExpr):
            args = [self.expr(arg) for arg in expr.arguments]
            return self.builder.call(self.get_method(expr.method), args)
        if expr.select:
            args = [self.expr(arg) for arg in expr.arguments]
            args.insert(0, self.expr(expr.select))
            return self.builder.call(self.get_method(expr.method), args)
        # TODO lookup method in this/super
        raise NotImplementedError

    def field_access(self, expr: FieldAccess, load=True) -> ir.Value:
        if not expr.select:
            ptr = self.builder.gep(self.builder.function.args[0], [ir.Constant(int32, 0), ir.Constant(int32, expr.field.owner.get_inherited_fields().index(expr.field))], inbounds=True,
                                   name=expr.field.name + '_ptr')
            return self.builder.load(ptr, name=expr.field.name)

        ptr = self.builder.gep(self.expr(expr.select), [ir.Constant(int32, 0), ir.Constant(int32, expr.field.owner.get_inherited_fields().index(expr.field))], inbounds=True,
                               name=expr.field.name + '_ptr')
        if not load:
            return ptr
        return self.builder.load(ptr, name=expr.field.name)

    def literal(self, expr: Literal) -> ir.Value:
        if isinstance(expr.type, ObjectType):
            value = self.builder.bitcast(new_string(self.module, expr.value), ir.IntType(8).as_pointer())
            return self.builder.call(FUNCTIONS['new_string'], [value])
        else:
            return ir.Constant(create_type(expr.type), expr.value)
