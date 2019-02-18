import contextlib
import hashlib
from typing import List, Union

from llvmlite import ir

from ast import Class, Method, Field, Type, ObjectType, Block, Statement, ExprStatement, WhileStatement, IfStatement, AssignStatement, ReturnStatement, Expr, \
    Variable, BinExpr, UnaryExpr, CastExpr, ClassCreation, MethodCall, ClassExpr, FieldAccess, Literal, Parameter
from context import Context
from flow import is_terminal
from phase import Phase
from report import Report
from symbol import SymbolTable
from type import REAL_NUMBERS, PLAY_PACKAGE
from util import never_be_here, class_name

int1 = ir.IntType(1)
int8 = ir.IntType(8)
int16 = ir.IntType(16)
int32 = ir.IntType(32)
int64 = ir.IntType(64)

ir_types = {
    'boolean': int1,
    'byte': int8,
    'short': int16,
    'int': int32,
    'long': int64,
    'float': ir.FloatType(),
    'double': ir.DoubleType(),
}


def create_type(type: Type) -> ir.Type:
    if not type:
        return ir.VoidType()
    if isinstance(type, ObjectType):
        return create_class_struct(type.cls).as_pointer()
    return ir_types[type.name]


def get_struct_size(struct: ir.IdentifiedStructType, packed=False):
    sizes = []
    for element in struct.elements:
        if isinstance(element, ir.PointerType):
            sizes.append(8)
        elif isinstance(element, ir.IntType):
            if element.width <= 8:
                sizes.append(1)
            elif element.width <= 16:
                sizes.append(2)
            elif element.width <= 32:
                sizes.append(4)
            elif element.width <= 64:
                sizes.append(8)
        elif isinstance(element, ir.FloatType):
            sizes.append(4)
        elif isinstance(element, ir.DoubleType):
            sizes.append(8)
    offset = 0
    if packed:
        offset = sum(sizes)
    else:
        for n in sizes:
            rem = offset % n
            if rem > 0:
                offset = offset - rem + n
            offset += n
    return offset


def create_class_struct(cls: Class) -> ir.Type:
    qualified_name = cls.qualified_name
    name = qualified_name.replace('.', '_')
    if name in ir.global_context.identified_types:
        return ir.global_context.get_identified_type(name)
    type = ir.global_context.get_identified_type(name)
    type.size = 0
    if cls.is_native:
        return type

    elements = [int32]
    elements.extend(create_type(field.type) for field in cls.inherited_fields)
    type.set_body(*elements)
    type.size = get_struct_size(type)
    return type


sig_type_name = {
    'boolean': 'Z',
    'byte': 'B',
    'short': 'S',
    'int': 'I',
    'long': 'L',
    'float': 'F',
    'double': 'D',
    'play.String': 'T',
    'play.Object': 'O',
}


def get_type_name(type: Type) -> str:
    if not type:
        return 'V'
    if type.name in sig_type_name:
        return sig_type_name[type.name]
    return 'C{}'.format(type.name.replace('.', '_'))


def get_method_name(method: Method) -> str:
    ret = [method.owner.qualified_name.replace('.', '_')]
    if method.is_static:
        ret.append('s')
    ret.append(method.owner.name if method.name == '<init>' else method.name)
    ret.append(get_type_name(method.return_type))
    ret.append(''.join([get_type_name(p.type) for p in method.parameters]))
    return '_'.join(ret)


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
    def __init__(self):
        self.scopes = []

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def enter(self, name: str, value: Union[ir.Value, Field]):
        self.scopes[-1][name] = value

    def lookup(self, name) -> ir.Value:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]


class Codegen(Phase):
    def __init__(self):
        self.module = ir.Module(name='play')
        self.builder: ir.IRBuilder = None
        self.current_method: Method = None
        self.env: GenEnv = None
        self.loop_context = []
        self.basic_blocks = []
        self.methods = {}
        self.functions = {}
        self.strings = {}

    def run(self):
        obj_ptr = create_class_struct(PLAY_PACKAGE.children['Object']).as_pointer()
        str_ptr = create_class_struct(PLAY_PACKAGE.children['String']).as_pointer()

        self.create_function(self.module, 'new', obj_ptr, [int32])
        self.create_function(self.module, 'newString', str_ptr, [int8.as_pointer()])
        self.create_function(self.module, 'cast', obj_ptr.as_pointer(), [obj_ptr, int32])
        self.create_function(self.module, 'loadMethod', int32.as_pointer(), [obj_ptr, int32])

        Report().begin("Codegen")
        for cls in SymbolTable().get_classes():
            self.gen_class(cls)

        Report().end()

        self.gen_main()

        with open(Context().code_gen_file, 'w') as f:
            f.write(str(self.module))

    def new_string(self, module, s):
        if s in self.strings:
            return self.strings[s]
        es = s.encode('utf-8')
        b = bytearray(es)
        b.append(0)
        n = len(b)
        value = ir.Constant(ir.ArrayType(ir.IntType(8), n), b)
        data = ir.GlobalVariable(module, value.type, name='str{}'.format(hashlib.md5(es).hexdigest()))
        data.linkage = 'internal'
        data.global_constant = True
        data.initializer = value
        self.strings[s] = data
        return data

    def create_function(self, module, name, return_type, types):
        type = ir.FunctionType(return_type, types)
        func = ir.Function(module, type, name=name)
        self.functions[name] = func

    @contextlib.contextmanager
    def new_env(self):
        self.env.push()
        yield
        self.env.pop()

    @contextlib.contextmanager
    def in_basic_block(self, basic_block):
        self.basic_blocks.append(basic_block)
        yield
        self.basic_blocks.pop()

    def get_method(self, method: Method) -> ir.Function:
        name = get_method_name(method)
        if name not in self.methods:
            parameters = [create_type(p.type) for p in method.parameters]
            if not method.is_static:
                parameters.insert(0, create_class_struct(method.owner).as_pointer())
            type = ir.FunctionType(create_type(method.return_type), parameters)
            func = ir.Function(self.module, type, name=get_method_name(method))
            self.methods[name] = func
        return self.methods[name]

    def gen_class(self, cls: Class):
        self.env = GenEnv()
        with self.new_env():
            for field in cls.inherited_fields:
                self.env.enter(field.name, field)
            self.gen_new(cls)
            for method in cls.methods + cls.static_methods:
                self.gen_method(method)

    def gen_new(self, cls):
        name = cls.qualified_name.replace('.', '_') + '_new'
        if name in self.methods:
            return self.methods[name]
        cls_type = create_class_struct(cls)
        return_type = cls_type.as_pointer()
        func_type = ir.FunctionType(return_type, [])
        func = ir.Function(self.module, func_type, name=name)
        self.methods[name] = func
        if cls.is_native:
            return self.methods[name]
        with self.new_env():
            builder = ir.IRBuilder(func.append_basic_block('entry'))
            ret = builder.call(self.functions['new'], [ir.Constant(int32, cls_type.size)])
            ret = builder.bitcast(ret, return_type)
            builder.call(self.gen_new_fields(cls), [ret])
            builder.ret(builder.bitcast(ret, return_type))

        return self.methods[name]

    def gen_new_fields(self, cls: Class):
        name = cls.qualified_name.replace('.', '_') + '_init'
        if name in self.methods:
            return self.methods[name]
        cls_type = create_class_struct(cls)
        func_type = ir.FunctionType(ir.VoidType(), [cls_type.as_pointer()])
        func = ir.Function(self.module, func_type, name=name)
        self.methods[name] = func
        if cls.is_native:
            return self.methods[name]

        with self.new_env():
            from cgen import RuntimeGen
            builder = ir.IRBuilder(func.append_basic_block('entry'))
            func = self.gen_new_fields(cls.superclass)
            builder.call(func, [builder.bitcast(builder.function.args[0], func.ftype.args[0])])

            ptr = builder.gep(builder.function.args[0], [
                ir.Constant(int32, 0), ir.Constant(int32, 0)
            ], inbounds=True, name='classId_ptr')
            builder.store(ir.Constant(int32, RuntimeGen().classes.index(cls)), ptr)

            for field in cls.fields:
                if field.initializer:
                    value = self.expr(field.initializer)
                    ptr = self.builder.gep(self.builder.function.args[0], [
                        ir.Constant(int32, 0), ir.Constant(int32, field.owner.inherited_fields.index(field) + 1)
                    ], inbounds=True, name=field.name + '_ptr')
                    builder.store(value, ptr)
            builder.ret_void()

        return self.methods[name]

    def gen_method(self, method: Method):
        self.current_method = method
        func = self.get_method(method)
        if not method.body:
            return

        with self.new_env():
            entry = self.basic_block(func, 'entry')
            self.basic_blocks = [entry]
            self.builder = ir.IRBuilder(entry.block)
            parameters = self.current_method.parameters[:]
            if not method.is_static:
                parameters.insert(0, Parameter('this', ObjectType(method.owner)))
            for i, arg in enumerate(self.builder.function.args):
                self.env.enter(parameters[i].name, arg)

            self.block(method.body)

            func.blocks = entry.get_blocks()
            for i, block in enumerate(func.blocks):
                if not block.is_terminated:
                    if i + 1 < len(func.blocks):
                        ir.IRBuilder(block).branch(self.builder.function.blocks[i + 1])
                    else:
                        ir.IRBuilder(block).ret_void()

    def gen_main(self):
        type = ir.FunctionType(int32, [])
        func = ir.Function(self.module, type, name='playMain')
        entry = func.append_basic_block('entry')
        builder = ir.IRBuilder(entry)

        bootstrap_class = SymbolTable().get_class(Context().bootstrap_class)
        method = bootstrap_class.lookup_method('main', [], is_static=True)
        builder.call(self.get_method(method), [])
        builder.ret(ir.Constant(int32, 0))

    def basic_block(self, func, name):
        block = BasicBlock()
        block.block = ir.Block(parent=func, name=name)
        if self.basic_blocks:
            self.basic_blocks[-1].blocks.append(block)
        return block

    def block(self, block: Block):
        with self.new_env():
            for statement in block.statements:
                self.statement(statement)
                if is_terminal(statement):
                    break

    def statement(self, statement: Statement):
        getattr(self, class_name(statement))(statement)

    def while_statement(self, statement: WhileStatement):
        loop = self.basic_block(self.builder.function, 'while.loop')
        body = self.basic_block(self.builder.function, 'while.body')
        end = self.basic_block(self.builder.function, 'while.end')
        self.builder.branch(loop.block)

        self.builder = ir.IRBuilder(loop.block)
        with self.in_basic_block(loop):
            cond = self.expr(statement.expr)
        self.builder.cbranch(cond, body.block, end.block)

        self.loop_context.append({'loop': loop.block, 'end': end.block})
        with self.in_basic_block(body):
            self.builder = ir.IRBuilder(body.block)
            self.block(statement.block)
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
        with self.in_basic_block(then):
            self.block(statement.then)
            if not self.builder.block.is_terminated:
                self.builder.branch(end.block)

        if otherwise:
            self.builder = ir.IRBuilder(otherwise.block)
            with self.in_basic_block(otherwise):
                self.block(statement.otherwise)
                self.builder.branch(end.block)

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
            return self.builder.gep(self.builder.function.args[0], [
                ir.Constant(int32, 0), ir.Constant(int32, self.current_method.owner.inherited_fields.index(var) + 1)
            ], inbounds=True, name=var.name + '_ptr')
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
            ptr = self.builder.gep(self.builder.function.args[0], [
                ir.Constant(int32, 0), ir.Constant(int32, self.current_method.owner.inherited_fields.index(var) + 1)
            ], inbounds=True, name=var.name + '_ptr')
            return self.builder.load(ptr, name=var.name)
        assert var
        return var

    def bin_expr(self, expr: BinExpr) -> ir.Value:
        is_float = expr.left.type in REAL_NUMBERS

        if expr.op in {'||', '&&'}:
            cond_ptr = self.builder.alloca(int1, name='cond_ptr')
            cond_left = self.basic_block(self.builder.function, 'cond.left')
            true = self.basic_block(self.builder.function, 'cond.true')
            false = self.basic_block(self.builder.function, 'cond.false')
            end = self.basic_block(self.builder.function, 'cond.end')
            if expr.op == '||':
                self.builder.cbranch(self.expr(expr.left), true.block, cond_left.block)
            else:
                self.builder.cbranch(self.expr(expr.left), cond_left.block, false.block)

            self.builder = ir.IRBuilder(true.block)
            self.builder.store(ir.Constant(int1, 1), cond_ptr)
            self.builder.branch(end.block)

            self.builder = ir.IRBuilder(false.block)
            self.builder.store(ir.Constant(int1, 0), cond_ptr)
            self.builder.branch(end.block)

            self.builder = ir.IRBuilder(cond_left.block)
            with self.in_basic_block(cond_left):
                self.builder.cbranch(self.expr(expr.right), true.block, false.block)

            self.basic_blocks.append(end)
            self.builder = ir.IRBuilder(end.block)
            return self.builder.load(cond_ptr, name='cond')

        left = self.expr(expr.left)
        right = self.expr(expr.right)
        if expr.op == '+':
            return self.builder.fadd(left, right) if is_float else self.builder.add(left, right)
        if expr.op == '-':
            return self.builder.fsub(left, right) if is_float else self.builder.sub(self, right)
        if expr.op == '*':
            return self.builder.fmul(left, right) if is_float else self.builder.mul(left, right)
        if expr.op == '/':
            return self.builder.fdiv(left, right) if is_float else self.builder.sdiv(left, right)
        if expr.op == '%':
            return self.builder.frem(left, right) if is_float else self.builder.srem(left, right)
        if expr.op in {'<', '>', '<=', '>=', '==', '!='}:
            return self.builder.fcmp_ordered(expr.op, left, right) if is_float else self.builder.icmp_signed(expr.op, left, right)
        if expr.op == '<<':
            return self.builder.shl(left, right)
        if expr.op == '>>':
            return self.builder.lshr(left, right)
        if expr.op == '>>>':
            return self.builder.ashr(left, right)
        if expr.op == '|':
            return self.builder.or_(left, right)
        if expr.op == '^':
            return self.builder.xor(left, right)
        if expr.op == '&':
            return self.builder.and_(left, right)
        never_be_here()

    def unary_expr(self, expr: UnaryExpr) -> ir.Value:
        if expr.op == '-':
            return self.builder.neg(self.expr(expr.expr))
        if expr.op in {'~', '!'}:
            return self.builder.not_(self.expr(expr.expr))
        return self.expr(expr.expr)

    def cast_expr(self, cast: CastExpr) -> ir.Value:
        obj_ptr = create_class_struct(PLAY_PACKAGE.children['Object']).as_pointer()
        if isinstance(cast.type, ObjectType):
            from cgen import RuntimeGen
            return self.builder.bitcast(self.builder.call(self.functions['cast'], [
                self.builder.bitcast(self.expr(cast.expr), obj_ptr), ir.Constant(int32, RuntimeGen().classes.index(cast.type.cls))
            ]), create_type(cast.type))

        return self.builder.bitcast(self.expr(cast.expr), create_type(cast.type))

    def class_creation(self, creation: ClassCreation) -> ir.Value:
        return self.builder.call(self.gen_new(creation.cls), [])

    def method_call(self, call: MethodCall) -> ir.Value:
        if isinstance(call.select, ClassExpr):
            args = [self.expr(arg) for arg in call.arguments]
            return self.builder.call(self.get_method(call.method), args)
        if call.select:
            if isinstance(call.select, Variable) and call.select.name in {'this', 'super'}:
                return self.invoke_direct(self.builder.function.args[0], call)
            if call.method.is_private:
                return self.invoke_direct(self.expr(call.select), call)
            return self.invoke_dynamic(self.expr(call.select), call)
        return self.invoke_direct(self.builder.function.args[0], call)

    def invoke_direct(self, this: ir.Value, call: MethodCall):
        method = self.get_method(call.method)
        args = [self.expr(arg) for arg in call.arguments]
        args.insert(0, self.builder.bitcast(this, method.ftype.args[0]))
        return self.builder.call(method, args)

    def invoke_dynamic(self, this: ir.Value, call: MethodCall):
        this = self.builder.load(this)
        obj_ptr = create_class_struct(PLAY_PACKAGE.children['Object']).as_pointer()
        method_id = call.method.owner.inherited_methods.index(call.method)
        method_ptr = self.builder.call(self.functions['loadMethod'], [self.builder.bitcast(this, obj_ptr), ir.Constant(int32, method_id)])
        parameters = [create_type(p.type) for p in call.method.parameters]
        function_type = ir.FunctionType(create_type(call.method.return_type), parameters)
        method = self.builder.bitcast(method_ptr, function_type.as_pointer())
        args = [self.expr(arg) for arg in call.arguments]
        return self.builder.call(method, args)

    def field_access(self, expr: FieldAccess, load=True) -> ir.Value:
        if not expr.select:
            ptr = self.builder.gep(self.builder.function.args[0], [
                ir.Constant(int32, 0), ir.Constant(int32, expr.field.owner.inherited_fields.index(expr.field) + 1)
            ], inbounds=True, name=expr.field.name + '_ptr')
            return self.builder.load(ptr, name=expr.field.name)

        ptr = self.builder.gep(self.expr(expr.select), [
            ir.Constant(int32, 0), ir.Constant(int32, expr.field.owner.inherited_fields.index(expr.field) + 1)
        ], inbounds=True, name=expr.field.name + '_ptr')
        if not load:
            return ptr
        return self.builder.load(ptr, name=expr.field.name)

    def literal(self, expr: Literal) -> ir.Value:
        if isinstance(expr.type, ObjectType):
            value = self.builder.bitcast(self.new_string(self.module, expr.value), int8.as_pointer())
            return self.builder.call(self.functions['newString'], [value])
        else:
            return ir.Constant(create_type(expr.type), expr.value)
