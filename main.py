import flow
import phase
import translate
from cgen import CGen
from codegen import Codegen
from context import Context


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
        ]

    def compile(self):
        for p in self.phases:
            p.run()


def main():
    ctx = Context()
    ctx.source_locations = ['play', 'test']
    ctx.c_source_location = 'native/class'
    ctx.bootstrap_class = 'Hello'
    Compiler().compile()


if __name__ == "__main__":
    main()
