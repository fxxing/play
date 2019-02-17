import re


def singleton(cls):
    __instance = {}

    def _singleton(*args, **kwargs):
        if cls not in __instance:
            __instance[cls] = cls(*args, **kwargs)
        return __instance[cls]

    return _singleton


class CompileException(Exception):
    pass


def never_be_here():
    assert 0, 'Can never be here'


def underline_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def class_name(obj):
    return underline_case(obj.__class__.__name__)