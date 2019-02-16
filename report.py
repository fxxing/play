import time

from util import singleton


@singleton
class Report(object):
    def __init__(self):
        self.stack = []

    def begin(self, name):
        print('\x1b[32m{}\x1b[20m'.format('    ' * len(self.stack) + name))
        self.stack.append((name, time.time() * 1000))

    def end(self):
        name, start = self.stack.pop()
        print('\x1b[32m{}done {} in {}ms\x1b[20m'.format('    ' * len(self.stack), name, (time.time() * 1000 - start)))

    def report(self, name, func=None):
        if func:
            start = time.time() * 1000
            func()
            print('\x1b[32m{}done {} in {}ms\x1b[20m'.format('    ' * len(self.stack), name, (time.time() * 1000 - start)))
        else:
            print('\x1b[32m{}{}\x1b[20m'.format('    ' * len(self.stack), name))
