from ast import Variable, Class, Field, Expr, ClassExpr, FieldAccess
from builtin import PLAY_PACKAGE
from util import CompileException


class Env(object):
    def __init__(self, cls: Class):
        self.cls = cls
        self.scopes = []

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def enter(self, value: Variable):
        current = self.scopes[-1]
        old: Variable = current.get(value.name)
        if old and old.type != value.type:
            raise CompileException('Redefine variable {} with different type {}'.format(old.name, value.type))
        else:
            current[value.name] = value

    def lookup(self, name, static) -> Expr:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if not static:
            field = self.cls.inherited_members.get(name)
            if isinstance(field, Field):
                return FieldAccess(None, field)

        try:
            return ClassExpr(lookup_class(name, self.cls))
        except CompileException:
            pass
        raise CompileException('Cannot find symbol {}'.format(name))


def lookup_class(name: str, start: Class) -> Class:
    if name == start.name:
        return start
    if name in start.source.imports:
        return start.source.imports[name]
    found = start.owner.children.get(name)
    if isinstance(found, Class):
        return found
    if isinstance(PLAY_PACKAGE.children.get(name), Class):
        return PLAY_PACKAGE.children[name]
    # if name in Builtin().classes:
    #     return Builtin().classes[name]
    raise CompileException("Cannot find class {}".format(name))
