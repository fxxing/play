import re

from ast import Statement


def underline_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def class_name(obj):
    return underline_case(obj.__class__.__name__)


class StatementVisitor(object):
    def visit(self, node: Statement):
        if 'visit_' + class_name(node) in dir(self):
            getattr(self, 'visit_' + class_name(node))(node)

        elif isinstance(node, (list, tuple)):
            for i, value in enumerate(node):
                self.visit(value)
        else:
            getattr(self, 'enter_' + class_name(node))(node)

            for field in node.fields:
                value = getattr(node, field)
                if value:
                    self.visit(value)

            getattr(self, 'leave_' + class_name(node))(node)

    def __getattr__(self, name):
        return self._missing

    def _missing(self, node):
        pass
