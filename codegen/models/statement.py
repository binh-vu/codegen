from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from codegen.models.expr import ExceptionExpr, Expr
from codegen.models.memory import Var


class Statement(ABC):

    @abstractmethod
    def to_python(self):
        raise NotImplementedError()


class NoStatement(Statement):
    def __repr__(self):
        return "NoStatement()"

    def to_python(self):
        return "pass"


@dataclass
class BlockStatement(Statement):
    """A placeholder for a block of statements. It is used to group multiple same-level statements together."""

    stmts: list[Statement] = field(default_factory=list)

    def to_python(self):
        raise Exception(
            "BlockStatement won't provide the implementation. Users should invoke the implementation of each inner statement directly."
        )


class LineBreak(Statement):
    def to_python(self):
        return ""


@dataclass
class ImportStatement(Statement):
    module: str

    def to_python(self):
        if self.module.find(".") != -1:
            module, attr = self.module.rsplit(".", 1)
            return f"from {module} import {attr}"
        return f"import {self.module}"


@dataclass
class DefFuncStatement(Statement):
    name: str
    args: list[Var] = field(default_factory=list)

    def to_python(self):
        return f"def {self.name}({', '.join([arg.get_name() for arg in self.args])}):"


@dataclass
class AssignStatement(Statement):
    var: Var
    expr: Expr

    def to_python(self):
        return f"{self.var.get_name()} = {self.expr.to_python()}"


@dataclass
class SingleExprStatement(Statement):
    expr: Expr

    def to_python(self):
        return self.expr.to_python()


@dataclass
class ExceptionStatement(Statement):
    expr: ExceptionExpr  # we rely on special exception expr

    def to_python(self):
        return "raise " + self.expr.to_python()


@dataclass
class ForLoopStatement(Statement):
    item: Var
    iter: Expr

    def to_python(self):
        return f"for {self.item.get_name()} in {self.iter.to_python()}:"


@dataclass
class ContinueStatement(Statement):
    def to_python(self):
        return "continue"


@dataclass
class BreakStatement(Statement):
    def to_python(self):
        return "break"


@dataclass
class ReturnStatement(Statement):
    expr: Expr

    def to_python(self):
        return f"return {self.expr.to_python()}"


@dataclass
class IfStatement(Statement):
    cond: Expr

    def to_python(self):
        return f"if {self.cond.to_python()}:"


@dataclass
class ElseStatement(Statement):
    def to_python(self):
        return "else:"


@dataclass
class Comment(Statement):
    comment: str

    def to_python(self):
        return f"# {self.comment}"
