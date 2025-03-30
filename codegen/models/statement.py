from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from multiprocessing import Value
from typing import Optional, Sequence

from codegen.models.expr import ExceptionExpr, Expr, ExprFuncCall
from codegen.models.var import Var


class Statement(ABC):

    @abstractmethod
    def to_python(self):
        raise NotImplementedError()

    def to_typescript(self):
        raise NotImplementedError(self.__class__)


class NoStatement(Statement):
    def __repr__(self):
        return "NoStatement()"

    def to_python(self):
        return "pass"

    def to_typescript(self):
        return "{}"


@dataclass
class BlockStatement(Statement):
    # whether the block has its own environment or not -- meaning any variables declared inside the block will be
    # only visible inside the block
    has_owned_env: bool = True

    def to_python(self):
        raise Exception(
            "BlockStatement doesn't have any direct statement. You can use it to create scope for variables."
        )

    def to_typescript(self):
        raise Exception(
            "BlockStatement doesn't have any direct statement. You can use it to create scope for variables."
        )


class LineBreak(Statement):
    def to_python(self):
        return ""

    def to_typescript(self):
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

    def to_typescript(self):
        if self.module.find(".") != -1 and self.is_import_attr:
            module, attr = self.module.rsplit(".", 1)
            module = module.replace(".", "/")
            if self.alias is not None:
                return f"import {{ {attr} as {self.alias} }}  from '{module}';"
            return f"import {{ {attr} }} from '{module}';"
        else:
            raise NotImplementedError()


@dataclass
class DefFuncStatement(Statement):
    name: str
    args: Sequence[Var | tuple[Var, Expr]] = field(default_factory=list)
    return_type: Optional[Expr] = None
    is_async: bool = False
    is_static: bool = False
    comment: str = ""

    def to_python(self):
        sig = f"def {self.name}({', '.join([arg[0].to_python() + " = " + arg[1].to_python() if isinstance(arg, tuple) else arg.to_python() for arg in self.args])})"
        if self.return_type is not None:
            sig += f" -> {self.return_type.to_python()}"
        if self.is_async:
            sig = "async " + sig
        sig = sig + ":"
        if self.is_static:
            sig = "static " + sig
        if self.comment != "":
            sig = (
                sig
                + "\n\t"
                + '"""'
                + "\n\t".join(self.comment.split("\n"))
                + "\n\t"
                + '"""'
            )
        return sig

    def to_typescript(self):
        if self.is_async:
            keyword = "async "
        else:
            keyword = ""

        if self.is_static:
            keyword += "static "

        sig = (
            keyword
            + f"{self.name}({', '.join([arg[0].to_typescript() + " = " + arg[1].to_typescript() if isinstance(arg, tuple) else arg.to_typescript() for arg in self.args])})"
        )
        if self.return_type is not None:
            sig += f": {self.return_type.to_typescript()}"
        if self.comment != "":
            sig = (
                "\n".join("/// " + line for line in self.comment.split("\n"))
                + "\n"
                + sig
            )
        return sig


@dataclass
class DefClassStatement(Statement):
    name: str
    parents: list[Expr] = field(default_factory=list)

    def to_python(self):
        if len(self.parents) == 0:
            return f"class {self.name}:"
        return f"class {self.name}({', '.join(p.to_python() for p in self.parents)}):"

    def to_typescript(self):
        # export by default because we do not have way to make this class private yet.
        if len(self.parents) > 0:
            extend = f" extends {' '.join(p.to_typescript() for p in self.parents)}"
        else:
            extend = ""
        return f"export class {self.name}" + extend


@dataclass
class DefInterfaceStatement(Statement):
    name: str
    parents: list[Expr] = field(default_factory=list)

    def to_python(self):
        raise ValueError("Python does not have interfaces")

    def to_typescript(self):
        # export by default because we do not have way to make this class private yet.
        if len(self.parents) > 0:
            extend = f" extends {' '.join(p.to_typescript() for p in self.parents)}"
        else:
            extend = ""
        return f"export interface {self.name}" + extend


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

    def to_typescript(self):
        assert self.type is not None
        if self.value is None:
            return f"{self.name}: {self.type};"
        return f"{self.name}: {self.type} = {self.value.to_typescript()};"


@dataclass
class AssignStatement(Statement):
    var: Var | Expr
    expr: Expr

    def to_python(self):
        if isinstance(self.var, Var):
            return f"{self.var.get_name()} = {self.expr.to_python()}"
        else:
            assert isinstance(self.var, Expr)
            return f"{self.var.to_python()} = {self.expr.to_python()}"

    def to_typescript(self):
        if isinstance(self.var, Var):
            return f"{self.var.get_name()} = {self.expr.to_typescript()};"
        else:
            assert isinstance(self.var, Expr)
            return f"{self.var.to_typescript()} = {self.expr.to_typescript()};"


@dataclass
class SingleExprStatement(Statement):
    expr: Expr

    def to_python(self):
        return self.expr.to_python()

    def to_typescript(self):
        return self.expr.to_typescript()


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

    def to_typescript(self):
        return "break;"


@dataclass
class ReturnStatement(Statement):
    expr: Expr

    def to_python(self):
        return f"return {self.expr.to_python()}"

    def to_typescript(self):
        return f"return {self.expr.to_typescript()};"


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
