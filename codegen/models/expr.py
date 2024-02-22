from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from codegen.models.memory import Var


class Expr(ABC):
    @abstractmethod
    def to_python(self):
        raise NotImplementedError()


class ExceptionExpr(Expr):
    pass


@dataclass
class ExprConstant(Expr):
    constant: Any

    def to_python(self):
        return ExprConstant.constant_to_python(self.constant)

    @staticmethod
    def constant_to_python(val: Any):
        if isinstance(val, bool) or val is None:
            return str(val)
        if isinstance(val, (str, int, float)):
            return json.dumps(val)
        if isinstance(val, list):
            return (
                "[" + ", ".join([ExprConstant.constant_to_python(v) for v in val]) + "]"
            )
        if isinstance(val, dict):
            return (
                "{"
                + ", ".join(
                    [
                        f"{ExprConstant.constant_to_python(k)}: {ExprConstant.constant_to_python(v)}"
                        for k, v in val.items()
                    ]
                )
                + "}"
            )
        if isinstance(val, set):
            return (
                "{" + ", ".join([ExprConstant.constant_to_python(v) for v in val]) + "}"
            )


@dataclass
class ExprIdent(Expr):
    ident: str

    def to_python(self):
        return self.ident


@dataclass
class ExprVar(Expr):  # a special identifier
    var: Var

    def to_python(self):
        return self.var.get_name()


@dataclass
class ExprFuncCall(Expr):
    func_name: Expr
    args: list[Expr]

    def to_python(self):
        return f"{self.func_name.to_python()}({', '.join([arg.to_python() for arg in self.args])})"


@dataclass
class ExprMethodCall(Expr):
    object: Expr
    method: str
    args: list[Expr]

    def to_python(self):
        if self.method == "__contains__" and len(self.args) == 1:
            return f"{self.args[0].to_python()} in {self.object.to_python()}"
        return f"{self.object.to_python()}.{self.method}({', '.join([arg.to_python() for arg in self.args])})"


@dataclass
class ExprNotEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} != {self.right.to_python()}"


@dataclass
class ExprLessThanOrEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} < {self.right.to_python()}"


@dataclass
class ExprEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} == {self.right.to_python()}"


@dataclass
class ExprNegation(Expr):
    expr: Expr

    def to_python(self):
        return f"not {self.expr.to_python()}"


class PredefinedFn:
    @dataclass
    class tuple(Expr):
        items: Sequence[Expr]

        def to_python(self):
            return f"({', '.join([item.to_python() for item in self.items])})"

    @dataclass
    class item_getter(Expr):
        collection: Expr
        item: Expr

        def to_python(self):
            return f"{self.collection.to_python()}[{self.item.to_python()}]"

    @dataclass
    class len(Expr):
        collection: Expr

        def to_python(self):
            return f"len({self.collection.to_python()})"

    @dataclass
    class range(Expr):
        start: Expr
        end: Expr
        step: Optional[Expr] = None

        def to_python(self):
            if self.step is not None:
                return f"range({self.start.to_python()}, {self.end.to_python()}, {self.step.to_python()})"
            return f"range({self.start.to_python()}, {self.end.to_python()})"

    @dataclass
    class set_contains(Expr):
        set_: Expr
        item: Expr

        def to_python(self):
            return f"({self.item.to_python()}) in {self.set_.to_python()}"

    @dataclass
    class list_append(Expr):
        lst: Expr
        item: Expr

        def to_python(self):
            return f"{self.lst.to_python()}.append({self.item.to_python()})"

    @dataclass
    class has_item(Expr):
        collection: Expr
        item: Expr

        def to_python(self):
            return f"({self.item.to_python()}) in {self.collection.to_python()}"

    @dataclass
    class base_error(ExceptionExpr):
        msg: str

        def to_python(self):
            return f"Exception('{self.msg}')"

    @dataclass
    class key_error(ExceptionExpr):
        msg: str

        def to_python(self):
            return f"KeyError('{self.msg}')"
