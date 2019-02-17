from typing import Dict, List

from ast import PackageChildType, Package, Class
from type import PLAY_PACKAGE
from util import singleton, CompileException


@singleton
class SymbolTable(object):
    def __init__(self):
        from type import ROOT_PACKAGE
        self.__symbols: Dict[str, PackageChildType] = {"": ROOT_PACKAGE, "play": PLAY_PACKAGE}

    def root_package(self) -> Package:
        return self.__symbols[""]

    def enter_package(self, package: str) -> Package:
        symbol = self.__symbols.get(package)
        if isinstance(symbol, Package):
            return symbol
        elif not symbol:
            owner = self.enter_package(package[:package.rfind('.')] if '.' in package else '')
            symbol = Package(package, owner)
            owner.put(symbol)
            self.__symbols[package] = symbol
            return symbol
        else:
            raise CompileException("Expect package symbol, but it is {}".format(symbol))

    def enter_class(self, cls: Class):
        qualified_name = cls.qualified_name
        if qualified_name in self.__symbols:
            raise CompileException("Duplicated class name {}".format(qualified_name))
        self.__symbols[qualified_name] = cls

    def get_classes(self) -> List[Class]:
        for k, v in self.__symbols.items():
            if isinstance(v, Class):
                yield v

    def get_packages(self) -> List[Package]:
        for k, v in self.__symbols.items():
            if isinstance(v, Package):
                yield v

    def get_class(self, qualified_name) -> Class:
        cls = self.__symbols.get(qualified_name)
        if not isinstance(cls, Class):
            raise CompileException("Cannot find class {}".format(qualified_name))
        return cls
