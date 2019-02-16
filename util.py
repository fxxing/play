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

