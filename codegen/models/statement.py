from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from codegen.models.expr import ExceptionExpr, Expr
from codegen.models.var import Var


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
    # whether the block has its own environment or not -- meaning any variables declared inside the block will be
    # only visible inside the block
    has_owned_env: bool = True

    def to_python(self):
        raise Exception(
            "BlockStatement doesn't have any direct statement. You can use it to create scope for variables."
        )


class LineBreak(Statement):
    def to_python(self):
        return ""


@dataclass
class ImportStatement(Statement):
    module: str
    is_import_attr: bool

    def to_python(self):
        if self.module.find(".") != -1 and self.is_import_attr:
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
class DefClassStatement(Statement):
    name: str

    def to_python(self):
        return f"class {self.name}:"


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


@dataclass
class PythonStatement(Statement):
    stmt: str

    def to_python(self):
        return self.stmt
