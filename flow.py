from typing import List

from ast import Method, Statement, LoopStatement, IfStatement, ReturnStatement, Block, BreakStatement, ContinueStatement, MethodGroup
from phase import Phase
from report import Report
from symbol import SymbolTable
from util import CompileException


def is_terminal(statement: Statement) -> bool:
    if isinstance(statement, (ReturnStatement, ContinueStatement, BreakStatement)):
        return True
    if isinstance(statement, IfStatement):
        if statement.otherwise:
            return is_terminal(statement.then) and is_terminal(statement.otherwise)
        return False
    if isinstance(statement, Block):
        statements = statement.statements[:]
        for s in statements:
            if is_terminal(s):
                return True
    return False


# TODO unwrap always true/false conditions
# TODO unwrap unnecessary casts
class ControlFlowAnalyse(Phase):
    def run(self):
        Report().begin("ControlFlowAnalyse")

        for cls in SymbolTable().get_classes():
            Report().report('analyse {}'.format(cls.qualified_name))
            for member in cls.members.values():
                if isinstance(member, MethodGroup):
                    for method in member.methods:
                        self.analyse(method)

            for member in cls.static_members.values():
                for method in member.methods:
                    self.analyse(method)

        Report().end()

    def analyse(self, method: Method):
        if not method.body:
            return
        self.check_inside_loop(method.body)
        self.check_has_return(method)

    def check_inside_loop(self, statement: Statement, loops: List[LoopStatement] = None):
        if not statement:
            return
        if not loops:
            loops = []
        if isinstance(statement, BreakStatement):
            if not loops:
                raise CompileException('break must inside loop')
        elif isinstance(statement, ContinueStatement):
            if not loops:
                raise CompileException('continue must inside loop')
        elif isinstance(statement, IfStatement):
            self.check_inside_loop(statement.then, loops)
            if statement.otherwise:
                self.check_inside_loop(statement.otherwise, loops)
        elif isinstance(statement, LoopStatement):
            self.check_inside_loop(statement.block, [] + [statement])
        elif isinstance(statement, Block):
            for s in statement.statements:
                self.check_inside_loop(s, loops)

    def check_has_return(self, method: Method):
        if method.body:
            if not is_terminal(method.body) and method.return_type:
                raise CompileException('method {} does not return in all branches'.format(method.name))
