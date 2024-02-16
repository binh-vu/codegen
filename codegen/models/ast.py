from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from codegen.models.expr import Expr
from codegen.models.memory import Memory, Var, VarScope
from codegen.models.statement import (
    AssignStatement,
    Comment,
    DefFuncStatement,
    ElseStatement,
    ForLoopStatement,
    IfStatement,
    ImportStatement,
    LineBreak,
    NoStatement,
    ReturnStatement,
    SingleExprStatement,
    Statement,
)
from codegen.models.types import AST_ID


@dataclass
class AST:
    id: AST_ID
    stmt: Statement
    children: list[AST] = field(default_factory=list)
    _is_frozen: bool = (
        False  # whether to freeze the AST and disallow further modification
    )

    @staticmethod
    def root():
        return AST("root", NoStatement())

    def __call__(self, *args: Callable[[AST], Any] | Statement):
        """Allow to build the graph hierarchically"""
        for fn in args:
            if isinstance(fn, Statement):
                self._add_stmt(fn)
            else:
                assert callable(fn)
                fn(self)
        return self

    def freeze(self):
        self._is_frozen = True
        for child in self.children:
            child.freeze()

    def import_(self, module: str):
        self._add_stmt(ImportStatement(module))

    def return_(self, expr: Expr):
        self._add_stmt(ReturnStatement(expr))

    def linebreak(self):
        self._add_stmt(LineBreak())

    def comment(self, comment: str):
        self._add_stmt(Comment(comment))

    def func(self, name: str, vars: list[Var]):
        return self._add_stmt(DefFuncStatement(name, vars))

    def expr(self, expr: Expr):
        self._add_stmt(SingleExprStatement(expr))

    def assign(self, mem: Memory, var: Var, expr: Expr):
        scope = self.next_var_scope()
        self._add_stmt(AssignStatement(var, expr))
        var.set_scope(mem, scope)

    def for_loop(self, item: Var, iter: Expr):
        return self._add_stmt(ForLoopStatement(item, iter))

    def if_(self, condition: Expr):
        return self._add_stmt(IfStatement(condition))

    def else_(self):
        assert len(self.children) > 0 and isinstance(self.children[-1].stmt, Statement)
        return self._add_stmt(ElseStatement())

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

    def next_var_scope(self) -> VarScope:
        """Get a scope for the next variable that will be have if it is assigned to this AST"""
        return VarScope(self.id, len(self.children))

    def find_ast(self, id: AST_ID) -> Optional[AST]:
        """Find the AST with the given id"""
        if self.id == id:
            return self
        for child in self.children:
            ast = child.find_ast(id)
            if ast is not None:
                return ast
        return None

    def _add_stmt(self, stmt: Statement):
        if self._is_frozen:
            raise Exception("The AST is frozen and cannot be modified")
        ast = AST(self._next_child_id(), stmt)
        self.children.append(ast)
        return ast

    def _next_child_id(self):
        return self.id + "__" + str(len(self.children))
