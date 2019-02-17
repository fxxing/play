from typing import Tuple

from ast import *
from builtin import *
from builtin import INTEGER_NUMBERS, NUMBERS
from context import Context
from env import Env, lookup_class
from parser.PlayParser import PlayParser
from phase import Phase, build_type
from report import Report
from symbol import SymbolTable
from util import CompileException, never_be_here


def can_cast_to(self: Type, to_type: Type, force=False) -> bool:
    if not self:
        return not to_type
    if self == to_type:
        return True
    # TODO add cast
    if self == NULL_TYPE:
        return isinstance(to_type, ObjectType)
    if isinstance(self, Primitive):
        if isinstance(to_type, Primitive):
            return to_type.name in UPPER_CASTS.get(self.name)
        elif isinstance(to_type, ObjectType):
            return BOX_CASTS.get(self.name) == to_type.cls.qualified_name
    elif isinstance(self, ObjectType):
        if isinstance(to_type, Primitive):
            return BOX_CASTS.get(self.cls.qualified_name) == to_type.name
        elif isinstance(to_type, ObjectType):
            return True if force else self.cls.subclass_of(to_type.cls)
    return False


def lookup_method(cls: Class, name: str, arguments: List[Type], is_static=False) -> Method:
    # TODO move this to class
    members = cls.static_members if is_static else cls.inherited_members
    group = members.get(name)
    if not isinstance(group, MethodGroup):
        raise CompileException('Cannot find method {}'.format(name))
    for method in group.methods:
        if len(method.parameters) != len(arguments):
            continue
        for i, parameter in enumerate(method.parameters):
            if arguments[i] != parameter.type:
                break
        else:
            return method

    raise CompileException('Cannot find method {} with parameters {}'.format(name, arguments))


def lookup_field(self: Class, name: str) -> Field:
    # TODO move this to class
    field = self.inherited_members.get(name)
    if not isinstance(field, Field):
        raise CompileException('Cannot find field {}'.format(name))
    return field


def assert_type(actual, expect):
    if not isinstance(expect, (set, list)):
        expect = [expect]
    if actual not in expect:
        raise CompileException('Invalid type {}, expect {}'.format(actual, expect))


def upper_type(t1, t2):
    i1 = NUMBERS.index(t1)
    i2 = NUMBERS.index(t2)
    return NUMBERS[max(i1, i2)]


class Translate(Phase):
    def __init__(self):
        self.nodes = Context().nodes
        self.current_class: Class = None
        self.this_var: Variable = None
        self.super_var: Variable = None
        self.current_method: Method = None
        self.env: Env = None

    def run(self):
        Report().begin("Translate")
        for cls in SymbolTable().get_classes():
            Report().report('translate {}'.format(cls.qualified_name), lambda: self.translate(cls))
        Report().end()

        Context().nodes = {}

    def translate(self, cls: Class):
        self.current_class = cls
        self.this_var = Variable('this', ObjectType(self.current_class))
        self.super_var = Variable('super', ObjectType(self.current_class.superclass))
        self.env = Env(self.current_class)
        for member in cls.members.values():
            if isinstance(member, Field):
                self.translate_field(member)
            else:
                for method in member.methods:
                    self.translate_method(method)

        for member in cls.static_members.values():
            for method in member.methods:
                self.translate_method(method)

    def translate_field(self, field: Field):
        ctx: PlayParser.FieldDeclarationContext = self.nodes[field]
        if ctx.expression():
            expr = self.expression(ctx.expression())
            if not can_cast_to(expr.type, field.type):
                raise CompileException("Cannot assign to field {} with type {}".format(field.name, expr.type))
            field.initializer = expr

    def translate_method(self, method: Method):
        ctx: PlayParser.MethodDeclarationContext = self.nodes.get(method)
        if ctx and ctx.block():
            self.env.push()
            self.current_method = method
            for parameter in method.parameters:
                self.env.enter(Variable(parameter.name, parameter.type))
            method.body = self.block(ctx.block())
            self.env.pop()

    def block(self, ctx: PlayParser.BlockContext) -> Block:
        self.env.push()
        block = Block([self.statement(s) for s in ctx.statement()])
        self.env.pop()
        return block

    def expression(self, ctx: PlayParser.ExpressionContext) -> Expr:
        if ctx.logicalOrExpression():
            return self.logical_or_expression(ctx.logicalOrExpression())
        if ctx.methodCall():
            return self.method_call(ctx.methodCall(), self.expression(ctx.expression()))
        return self.field_access(ctx.IDENTIFIER().getText(), self.expression(ctx.expression()))

    def field_access(self, name: str, select: Expr) -> Expr:
        if select == self.super_var:
            raise CompileException('Cannot access field {} via super'.format(name))
        if not isinstance(select.type, ObjectType):
            raise CompileException("cannot lookup field in {}".format(select.type))
        return FieldAccess(select, lookup_field(select.type.cls, name))

    def bin_expr(self, op, left, right) -> Expr:
        # TODO make sure left and right have same primitive type
        if op in {'||', '&&'}:
            assert_type(left.type, BOOLEAN_TYPE)
            assert_type(right.type, BOOLEAN_TYPE)
            type = BOOLEAN_TYPE
        elif op == '+':
            if left.type == ObjectType(PLAY_PACKAGE.children['String']):
                string = PLAY_PACKAGE.children['String']
                right_type = right.type
                if isinstance(right_type, ObjectType):
                    if right_type.cls != string:
                        right_type = PLAY_PACKAGE.children['Object']
                return MethodCall(ClassExpr(string), lookup_method(string, 'concat', [right_type], is_static=True), [right])
            assert_type(left.type, NUMBERS)
            assert_type(right.type, NUMBERS)
            type = upper_type(left.type, right.type)
        elif op in {'-', '*', '/', '%'}:
            assert_type(left.type, NUMBERS)
            assert_type(right.type, NUMBERS)
            type = upper_type(left.type, right.type)
        elif op in {'<', '>', '<=', '>='}:
            assert_type(left.type, NUMBERS)
            assert_type(right.type, NUMBERS)
            type = BOOLEAN_TYPE
        elif op in {'<<', '>>', '>>>', '|', '^', '&'}:
            assert_type(left.type, INTEGER_NUMBERS)
            assert_type(right.type, INTEGER_NUMBERS)
            type = upper_type(left.type, right.type)
        elif op in {'==', '!='}:
            assert_type(left.type, INT_TYPE)
            assert_type(right.type, INT_TYPE)
            type = BOOLEAN_TYPE
        else:
            never_be_here()
            type = None
        expr = BinExpr(op, left, right)
        expr.type = type
        return expr

    def logical_or_expression(self, ctx: PlayParser.LogicalOrExpressionContext) -> Expr:
        if ctx.logicalOrExpression():
            return self.bin_expr(ctx.bop.text, self.logical_or_expression(ctx.logicalOrExpression()), self.logical_and_expression(ctx.logicalAndExpression()))
        return self.logical_and_expression(ctx.logicalAndExpression())

    def logical_and_expression(self, ctx: PlayParser.LogicalAndExpressionContext) -> Expr:
        if ctx.logicalAndExpression():
            return self.bin_expr(ctx.bop.text, self.logical_and_expression(ctx.logicalAndExpression()), self.inclusive_or_expression(ctx.inclusiveOrExpression()))
        return self.inclusive_or_expression(ctx.inclusiveOrExpression())

    def inclusive_or_expression(self, ctx: PlayParser.InclusiveOrExpressionContext) -> Expr:
        if ctx.inclusiveOrExpression():
            return self.bin_expr(ctx.bop.text, self.inclusive_or_expression(ctx.inclusiveOrExpression()), self.exclusive_or_expression(ctx.exclusiveOrExpression()))
        return self.exclusive_or_expression(ctx.exclusiveOrExpression())

    def exclusive_or_expression(self, ctx: PlayParser.ExclusiveOrExpressionContext) -> Expr:
        if ctx.exclusiveOrExpression():
            return self.bin_expr(ctx.bop.text, self.exclusive_or_expression(ctx.exclusiveOrExpression()), self.and_expression(ctx.andExpression()))
        return self.and_expression(ctx.andExpression())

    def and_expression(self, ctx: PlayParser.AndExpressionContext) -> Expr:
        if ctx.andExpression():
            return self.bin_expr(ctx.bop.text, self.and_expression(ctx.andExpression()), self.equality_expression(ctx.equalityExpression()))
        return self.equality_expression(ctx.equalityExpression())

    def equality_expression(self, ctx: PlayParser.EqualityExpressionContext) -> Expr:
        if ctx.equalityExpression():
            return self.bin_expr(ctx.bop.text, self.equality_expression(ctx.equalityExpression()), self.relational_expression(ctx.relationalExpression()))
        return self.relational_expression(ctx.relationalExpression())

    def relational_expression(self, ctx: PlayParser.RelationalExpressionContext) -> Expr:
        if ctx.relationalExpression():
            return self.bin_expr(ctx.bop.text, self.relational_expression(ctx.relationalExpression()), self.shift_expression(ctx.shiftExpression()))
        return self.shift_expression(ctx.shiftExpression())

    def shift_expression(self, ctx: PlayParser.ShiftExpressionContext) -> Expr:
        if ctx.shiftExpression():
            return self.bin_expr(ctx.bop.text, self.shift_expression(ctx.shiftExpression()), self.additive_expression(ctx.additiveExpression()))
        return self.additive_expression(ctx.additiveExpression())

    def additive_expression(self, ctx: PlayParser.AdditiveExpressionContext) -> Expr:
        if ctx.additiveExpression():
            return self.bin_expr(ctx.bop.text, self.additive_expression(ctx.additiveExpression()), self.multiplicative_expression(ctx.multiplicativeExpression()))
        return self.multiplicative_expression(ctx.multiplicativeExpression())

    def multiplicative_expression(self, ctx: PlayParser.MultiplicativeExpressionContext) -> Expr:
        if ctx.multiplicativeExpression():
            return self.bin_expr(ctx.bop.text, self.multiplicative_expression(ctx.multiplicativeExpression()), self.cast_expression(ctx.castExpression()))
        return self.cast_expression(ctx.castExpression())

    def cast_expression(self, ctx: PlayParser.CastExpressionContext) -> Expr:
        if ctx.unaryExpression():
            return self.unary_expression(ctx.unaryExpression())
        # unwrap if could
        expr = self.cast_expression(ctx.castExpression())
        type = build_type(ctx.typeName(), self.current_class)
        if not can_cast_to(expr.type, type, force=True):
            raise CompileException('Cannot cast type {} to {}'.format(expr.type, type))
        return CastExpr(expr, type)

    def unary_expression(self, ctx: PlayParser.UnaryExpressionContext) -> Expr:
        if ctx.primaryExpression():
            return self.primary_expression(ctx.primaryExpression())
        return self.unary_expr(ctx.uop.text, self.cast_expression(ctx.castExpression()))

    def unary_expr(self, op, expr: Expr) -> Expr:
        if op == '!':
            assert_type(expr.type, BOOLEAN_TYPE)
        elif op in {'+', '-'}:
            assert_type(expr.type, NUMBERS)
        elif op == '~':
            assert_type(expr.type, INTEGER_NUMBERS)
        return UnaryExpr(op, expr)

    def primary_expression(self, ctx: PlayParser.PrimaryExpressionContext) -> Expr:
        if self.current_method.is_static and ctx.THIS() or ctx.SUPER():
            raise CompileException('Cannot use this/super in static method')
        if ctx.methodCall():
            return self.method_call(ctx.methodCall())
        if ctx.classCreation():
            return self.class_creation(ctx.classCreation())
        if ctx.expression():
            return self.expression(ctx.expression())
        if ctx.THIS():
            return self.this_var
        if ctx.SUPER():
            return self.super_var
        if ctx.IDENTIFIER():
            return self.env.lookup(ctx.IDENTIFIER().getText(), self.current_method.is_static)
        if ctx.literal():
            return self.literal(ctx.literal())
        never_be_here()

    def class_creation(self, ctx: PlayParser.ClassCreationContext) -> Expr:
        cls = lookup_class(ctx.classType().IDENTIFIER().getText(), self.current_class)
        if cls.is_interface:
            raise CompileException("Cannot instantiate interface {}".format(cls.qualified_name))
        if cls.is_abstract:
            raise CompileException("Cannot instantiate abstract class {}".format(cls.qualified_name))
        arguments = self.expression_list(ctx.expressionList())
        types = [arg.type for arg in arguments]
        return ClassCreation(cls, lookup_method(cls, '<init>', types), arguments)

    def expression_list(self, ctx: PlayParser.ExpressionListContext) -> List[Expr]:
        if not ctx:
            return []
        return [self.expression(expr) for expr in ctx.expression()]

    def method_call(self, ctx: PlayParser.MethodCallContext, select: Expr = None) -> Expr:
        if self.current_method.is_static and ctx.THIS() or ctx.SUPER():
            raise CompileException('Cannot use this/super in static method')

        # TODO what to do when select is super?
        if select and (ctx.THIS() or ctx.SUPER()):
            raise CompileException('this() and super() cannot has prefix')
        arguments = self.expression_list(ctx.expressionList())
        types = [arg.type for arg in arguments]
        if ctx.THIS():
            method = lookup_method(self.current_class, '<init>', types)
        elif ctx.SUPER():
            method = lookup_method(self.current_class.superclass, '<init>', types)
            if method.is_private:
                raise CompileException('access private method in {}'.format(self.current_class.superclass.qualified_name))
        else:
            method_name = ctx.IDENTIFIER().getText()
            if select:
                if not isinstance(select.type, ObjectType):
                    raise CompileException("cannot lookup method in {}".format(select.type))
                method = lookup_method(select.type.cls, method_name, types, isinstance(select.type, ClassType))
                if method.is_private:
                    if not select.type.cls.qualified_name == self.current_class.qualified_name:
                        raise CompileException('access private method in {}'.format(select.type))
            else:
                method = lookup_method(self.current_class, method_name, types)
        return MethodCall(select, method, arguments)

    def literal(self, ctx: PlayParser.LiteralContext) -> Expr:
        if ctx.DECIMAL_LITERAL():
            return self.parse_integer(ctx.DECIMAL_LITERAL().getText(), 10)
        if ctx.HEX_LITERAL():
            return self.parse_integer(ctx.HEX_LITERAL().getText(), 16)
        if ctx.OCT_LITERAL():
            return self.parse_integer(ctx.OCT_LITERAL().getText(), 8)
        if ctx.BINARY_LITERAL():
            return self.parse_integer(ctx.BINARY_LITERAL().getText(), 2)
        if ctx.FLOAT_LITERAL():
            return self.parse_real(ctx.FLOAT_LITERAL().getText())
        if ctx.BYTE_LITERAL():
            return self.parse_byte(ctx.BYTE_LITERAL().getText())
        if ctx.STRING_LITERAL():
            return self.parse_string(ctx.STRING_LITERAL().getText())
        if ctx.BOOL_LITERAL():
            return self.parse_bool(ctx.BOOL_LITERAL().getText())
        if ctx.NULL_LITERAL():
            return self.null()
        never_be_here()

    def parse_integer(self, value: str, base):
        value = value.replace('_', '')
        if value.lower().endswith('l'):
            value = int(value[:-1], base)
            type = LONG_TYPE
            if value > 0x7FFFFFFFFFFFFFFF or value < -0x8000000000000000:
                raise CompileException('int out of range {}'.format(value))
        else:
            value = int(value, base)
            if value > 0x7FFFFFFF or value < -0x80000000:
                raise CompileException('int out of range {}'.format(value))
            type = INT_TYPE
        return Literal(value, type)

    def parse_real(self, value: str):
        value = value.replace('_', '')
        if value.lower().endswith('d'):
            value = float(value[:-1])
            type = DOUBLE_TYPE
        else:
            if value.endswith('f'):
                value = float(value[:-1])
            else:
                value = float(value)
            type = FLOAT_TYPE
        return Literal(value, type)

    def parse_byte(self, value: str):
        return Literal(ord(eval(value)), BYTE_TYPE)

    def parse_string(self, value: str):
        return Literal(eval(value), ObjectType(PLAY_PACKAGE.children['String']))

    def parse_bool(self, value: str):
        if value == 'true':
            return Literal(True, BOOLEAN_TYPE)
        if value == 'false':
            return Literal(False, BOOLEAN_TYPE)
        raise CompileException('Invalid boolean type')

    def null(self):
        return Literal(None, NULL_TYPE)

    def statement(self, ctx: PlayParser.StatementContext) -> Statement:
        if ctx.ifStatement():
            return self.if_statement(ctx.ifStatement())
        if ctx.whileStatement():
            return self.while_statement(ctx.whileStatement())
        if ctx.breakStatement():
            return BreakStatement()
        if ctx.continueStatement():
            return ContinueStatement()
        if ctx.returnStatement():
            return self.return_statement(ctx.returnStatement())
        if ctx.assignStatement():
            return self.assign_statement(ctx.assignStatement())
        if ctx.expression():
            return ExprStatement(self.expression(ctx.expression()))
        if ctx.block():
            return self.block(ctx.block())
        never_be_here()

    def if_statement(self, ctx: PlayParser.IfStatementContext) -> Statement:
        # unwrap always condition
        condition = self.expression(ctx.expression())
        if not condition.type == BOOLEAN_TYPE:
            raise CompileException("if expression must be boolean expression")
        else_ifs: List[Tuple[Expr, Block]] = []
        for else_if_ctx in ctx.elifClause():
            cond = self.expression(else_if_ctx.expression())
            if not cond.type == BOOLEAN_TYPE:
                raise CompileException("if expression must be boolean expression")
            else_ifs.append((cond, self.block(else_if_ctx.block())))
        otherwise = None
        if ctx.elseClause():
            otherwise = self.block(ctx.elseClause().block())
        if else_ifs:
            return IfStatement(condition, self.block(ctx.block()), Block([self.build_else(else_ifs, otherwise)]))
        else:
            return IfStatement(condition, self.block(ctx.block()), otherwise)

    def build_else(self, else_ifs: List[Tuple[Expr, Block]], otherwise: Optional[Block]) -> Statement:
        condition, block = else_ifs[0]
        else_ifs = else_ifs[1:]
        if else_ifs:
            return IfStatement(condition, block, Block([self.build_else(else_ifs, otherwise)]))
        else:
            return IfStatement(condition, block, otherwise)

    def while_statement(self, ctx: PlayParser.WhileStatementContext) -> Statement:
        expr = self.expression(ctx.expression())
        if not expr.type == BOOLEAN_TYPE:
            raise CompileException("while expression must be boolean expression")
        return WhileStatement(expr, self.block(ctx.block()))

    def return_statement(self, ctx: PlayParser.ReturnStatementContext) -> Statement:
        expr = self.expression(ctx.expression()) if ctx.expression() else None
        return_type = expr.type if expr else None
        if not can_cast_to(return_type, self.current_method.return_type):
            raise CompileException('Cannot return type {} for method {}, expect {}'.format(return_type, self.current_method.name, self.current_method.return_type))
        return ReturnStatement(expr)

    def assign_statement(self, ctx: PlayParser.AssignStatementContext) -> Statement:
        if ctx.IDENTIFIER():
            target = ctx.IDENTIFIER().getText()
            expr = self.expression(ctx.expression(0))
            type = build_type(ctx.typeName(), self.current_class) if ctx.typeName() else None
            if type:
                if not can_cast_to(expr.type, type):
                    raise CompileException('Cannot assign type {} to {}'.format(expr.type, type))
            else:
                type = expr.type  # infer type
            var = Variable(target, type)
            self.env.enter(var)
            return AssignStatement(var, expr)
        else:
            var = self.expression(ctx.expression(0))
            if not isinstance(var, FieldAccess):
                raise CompileException('left value must be variable or field')
            return AssignStatement(var, self.expression(ctx.expression(1)))
