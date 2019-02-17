from typing import List

from util import singleton


@singleton
class Context(object):
    def __init__(self):
        self.nodes = {}
        self.source_locations: List[str] = []
        self.code_gen_file = None
        self.const_file = None
        self.c_runtime_location = None
        self.c_source_location = None
        self.bootstrap_class = None
