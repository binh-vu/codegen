from __future__ import annotations

from codegen.models import AST, expr
from codegen.models.mem import Memory, Var


class BaseWriter:
    def __init__(self, prog: AST, mem: Memory):
        pass

    def create_record(self, prog: AST):
        pass

    def commit_record(self, prog: AST):
        pass

    def add_subject(self, prog: AST, val: expr.Expr):
        pass

    def add_property(self, prog: AST, prop: str, attr_val: expr.Expr):
        pass

    def finish(self, prog: AST):
        pass


class TTLWriter(BaseWriter):
    def __init__(self, prog: AST, mem: Memory):
        self.mem = mem
        self.g = Var.create(mem, "writer")
        prog.assign(self.g, expr.ExprFuncCall(expr.ExprIdent("create_rdf_graph"), []))

    def create_record(self, prog: AST):
        prog.expr(expr.ExprMethodCall(expr.ExprVar(self.g), "create_record", []))

    def commit_record(self, prog: AST):
        # not implemented yet
        prog.expr(expr.ExprMethodCall(expr.ExprVar(self.g), "commit_record", []))

    def add_subject(self, prog: AST, val: expr.Expr):
        prog.expr(expr.ExprMethodCall(expr.ExprVar(self.g), "add_subject", [val]))

    def add_property(self, prog: AST, prop: str, attr_val: expr.Expr):
        prog.expr(
            expr.ExprMethodCall(
                expr.ExprVar(self.g),
                "add_property",
                [expr.ExprConstant(prop), attr_val],
            )
        )

    def finish(self, prog: AST):
        prog.expr(expr.ExprMethodCall(expr.ExprVar(self.g), "finish", []))
