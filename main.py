import os

import flow
import phase
import translate
from codegen import Codegen
from context import Context
from report import Report


class Link(phase.Phase):
    def __init__(self):
        self.obj_files = ['build/play.ll']

    def run(self):
        for src in [Context().c_runtime_location, Context().c_source_location]:
            if not src.endswith('/'):
                src += '/'
            for root, dirs, files in os.walk(src):
                for file in files:
                    if not file.endswith('.c'):
                        continue
                    path = os.path.join(root, file)
                    Report().report("compile {}".format(path), lambda: self.compile(path, path[len(src):]))
        self.link()

    def compile(self, path, rel_path):
        target = 'build/' + rel_path.replace('.c', '.o')
        folder = os.path.dirname(target)
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.obj_files.append(target)
        os.system('clang -I {} -I {} -c {} -o {}'.format(Context().c_runtime_location, Context().c_source_location, path, target))

    def link(self):
        os.system('clang {} -o build/a.out'.format(' '.join(self.obj_files)))


class Compiler(object):
    def __init__(self):
        self.phases = [
            phase.Parse(),

            phase.EnterClass(),
            phase.ResolveImport(),
            phase.BuildHierarchy(),
            phase.CheckCircularDependency(),

            phase.EnterMember(),
            phase.CheckDuplicatedSignature(),
            phase.InheritMember(),
            translate.Translate(),
            flow.ControlFlowAnalyse(),
            Codegen(),
            # CGen(),
            Link(),
        ]

    def compile(self):
        for p in self.phases:
            p.run()


def main():
    ctx = Context()
    ctx.source_locations = ['play', 'test']
    ctx.bootstrap_class = 'Hello'
    ctx.code_gen_file = 'build/play.ll'
    ctx.c_runtime_location = 'native/runtime'
    ctx.c_source_location = 'native/class'
    Compiler().compile()


if __name__ == "__main__":
    main()
