from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from codegen.models.mem import Var


class Expr(ABC):
    @abstractmethod
    def to_python(self):
        raise NotImplementedError()


@dataclass
class ExprConstant(Expr):
    constant: str | int | bool | float

    def to_python(self):
        return json.dumps(self.constant)


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
        return f"{self.object.to_python()}.{self.method}({', '.join([arg.to_python() for arg in self.args])})"


class PredefinedFn:
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

        def to_python(self):
            return f"range({self.start.to_python()}, {self.end.to_python()})"
