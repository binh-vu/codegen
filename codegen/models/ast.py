from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from codegen.models.expr import Expr
from codegen.models.mem import Var
from codegen.models.statement import (
    AssignStatement,
    Comment,
    DefFuncStatement,
    ForLoopStatement,
    LineBreak,
    NoStatement,
    SingleExprStatement,
    Statement,
)


@dataclass
class AST:
    id: str
    stmt: Statement
    children: list[AST] = field(default_factory=list)

    @staticmethod
    def root():
        return AST("root", NoStatement())

    def linebreak(self):
        self.children.append(AST(self.id + "_" + str(len(self.children)), LineBreak()))

    def comment(self, comment: str):
        self.children.append(
            AST(self.id + "_" + str(len(self.children)), Comment(comment))
        )

    def func(self, name: str, vars: list[Var]):
        tree = AST(
            self.id + "_" + str(len(self.children)), DefFuncStatement(name, vars)
        )
        self.children.append(tree)
        return tree

    def expr(self, expr: Expr):
        self.children.append(
            AST(
                self.id + "_" + str(len(self.children)),
                SingleExprStatement(expr),
            )
        )

    def assign(self, var: Var, expr: Expr):
        self.children.append(
            AST(self.id + "_" + str(len(self.children)), AssignStatement(var, expr))
        )

    def for_loop(self, item: Var, iter: Expr):
        tree = AST(
            self.id + "_" + str(len(self.children)), ForLoopStatement(item, iter)
        )
        self.children.append(tree)
        return tree

    def seq_stmts(self, iterfn: Callable, obj):
        it = iterfn(self, obj, 0)
        if it is None:
            return
        while True:
            prog, obj, index = it
            it = iterfn(prog, obj, index)
            if it is None:
                break
        return prog

    def nested_stmts(self, func: Callable, obj) -> tuple[AST, list[list[Var]]]:
        genvars = []
        it = func(self, obj, 0, [])
        if it is None:
            raise Exception("no code blocks to expand")

        while True:
            prog, depth, blockvars = it
            genvars.append(blockvars)
            it = func(prog, obj, depth, genvars)
            if it is None:
                break
        return prog, genvars

    def to_python(self, level: int = -1):
        """Convert the AST to python code"""
        if level == -1:
            assert self.id == "root"
            return "".join(
                [
                    child.to_python(level + 1)
                    + ("\n" if ci < len(self.children) - 1 else "")
                    for ci, child in enumerate(self.children)
                ]
            )

        prog = ["\t" * level + self.stmt.to_python()]
        for child in self.children:
            prog.append("\n")
            prog.append(child.to_python(level + 1))
        return "".join(prog)
