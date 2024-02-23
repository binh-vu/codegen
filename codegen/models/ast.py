from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from codegen.models.expr import ExceptionExpr, Expr
from codegen.models.memory import Memory, Var, VarScope
from codegen.models.statement import (
    AssignStatement,
    BlockStatement,
    Comment,
    ContinueStatement,
    DefFuncStatement,
    ElseStatement,
    ExceptionStatement,
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

    def __call__(
        self, *args: Callable[[AST], Any] | Statement, return_self: bool = False
    ) -> Optional[AST]:
        """Allow to build the graph hierarchically"""
        return_val = None

        for fn in args:
            if isinstance(fn, Statement):
                self._add_stmt(fn)
            else:
                assert callable(fn)
                return_val = fn(self)

        if return_self:
            assert return_val is None, "Trying to return multiple asts at the same time"
            return self
        return return_val

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
        return self._add_stmt(SingleExprStatement(expr))

    def raise_exception(self, expr: ExceptionExpr):
        return self._add_stmt(ExceptionStatement(expr))

    def assign(self, mem: Memory, var: Var, expr: Expr):
        scope = self.next_var_scope()
        self._add_stmt(AssignStatement(var, expr))
        var.set_scope(mem, scope)

    def for_loop(self, mem: Memory, item: Var, iter: Expr):
        assert item.scope is None, "The variable is already assigned to a scope"
        ast = self._add_stmt(ForLoopStatement(item, iter))
        scope = ast.next_var_scope()
        item.set_scope(mem, scope)
        return ast

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

        if isinstance(self.stmt, BlockStatement):
            prog = ["\t" * level + stmt.to_python() + "\n" for stmt in self.stmt.stmts]
        else:
            prog = ["\t" * level + self.stmt.to_python()]

        for child in self.children:
            prog.append("\n")
            prog.append(child.to_python(level + 1))
        return "".join(prog)

    def next_var_scope(self) -> VarScope:
        """Get a scope for the next variable that will be have if it is assigned to this AST"""
        return VarScope(self.id, len(self.children))

    def has_statement_between_ast(self, stmtcls: type[Statement], end_ast_id: AST_ID):
        """Check if there is a statement of the given type the current AST and the end_ast (exclusive)"""
        for ast in self.children:
            for intermediate_ast in ast.find_ast_to(end_ast_id):
                if (
                    isinstance(intermediate_ast.stmt, stmtcls)
                    and intermediate_ast.id != end_ast_id
                ):
                    return True
        return False

    def find_ast_to(self, id: AST_ID):
        """Iterate through ASTs that lead to the AST with the given id (inclusive)"""
        if self.id == id:
            yield self
        else:
            for ast in self.children:
                if ast.find_ast(id) is not None:
                    yield from ast.find_ast_to(id)
                    break

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
