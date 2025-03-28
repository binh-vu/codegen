from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence

from codegen.models.expr import ExceptionExpr, Expr, ExprFuncCall
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
    alias: Optional[str] = None

    def to_python(self):
        if self.module.find(".") != -1 and self.is_import_attr:
            module, attr = self.module.rsplit(".", 1)
            stmt = f"from {module} import {attr}"
        else:
            stmt = f"import {self.module}"

        if self.alias is not None:
            stmt += f" as {self.alias}"
        return stmt


@dataclass
class DefFuncStatement(Statement):
    name: str
    args: Sequence[Var | tuple[Var, Expr]] = field(default_factory=list)
    return_type: Optional[Expr] = None
    is_async: bool = False

    def to_python(self):
        sig = f"def {self.name}({', '.join([arg[0].to_python() + " = " + arg[1].to_python() if isinstance(arg, tuple) else arg.to_python() for arg in self.args])})"
        if self.return_type is not None:
            sig += f" -> {self.return_type.to_python()}"
        if self.is_async:
            sig = "async " + sig
        return sig + ":"


@dataclass
class DefClassStatement(Statement):
    name: str
    parents: list[Expr] = field(default_factory=list)

    def to_python(self):
        if len(self.parents) == 0:
            return f"class {self.name}:"
        return f"class {self.name}({', '.join(p.to_python() for p in self.parents)}):"


@dataclass
class DefClassVarStatement(Statement):
    """Statement to define a variable with type"""

    # name of the variable
    name: str
    # type of the variable
    type: Optional[str]
    # value of the variable
    value: Optional[Expr] = None

    def to_python(self):
        if self.type is None:
            if self.value is None:
                return f"{self.name}"
            return f"{self.name} = {self.value.to_python()}"
        if self.value is None:
            return f"{self.name}: {self.type}"
        return f"{self.name}: {self.type} = {self.value.to_python()}"


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


@dataclass
class PythonDecoratorStatement(Statement):
    decorator: ExprFuncCall

    def to_python(self):
        if len(self.decorator.args) == 0:
            return f"@{self.decorator.func_name.to_python()}"
        return f"@{self.decorator.to_python()}"
