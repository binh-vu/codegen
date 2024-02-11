from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from codegen.models.expr import Expr
from codegen.models.mem import Var
from codegen.models.statement import (
    AssignStatement,
    Comment,
    DefFuncStatement,
    ForLoopStatement,
    ImportStatement,
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

    def import_(self, module: str):
        self.children.append(
            AST(self.id + "_" + str(len(self.children)), ImportStatement(module))
        )

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

    def update_recursively(
        self, fn: Callable[[AST, Any], tuple[AST, Any, bool]], context: Any
    ):
        """Recursively updating the ast. It takes a function that works on the current tree and a context, returns a tuple of
        (new_tree, new_context, stop). This function returns the last AST that is updated.
        """
        ast = self
        stop = False
        while not stop:
            ast, context, stop = fn(ast, context)
        return ast

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
