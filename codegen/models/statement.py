from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

import pandas as pd

from codegen.models.expr import Expr
from codegen.models.mem import Var


class Statement(ABC):

    @abstractmethod
    def to_python(self):
        raise NotImplementedError()


class NoStatement(Statement):
    def __repr__(self):
        return "NoStatement()"

    def to_python(self):
        return ""


class LineBreak(Statement):
    def to_python(self):
        return ""


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
class ForLoopStatement(Statement):
    item: Var
    iter: Expr

    def to_python(self):
        return f"for {self.item.get_name()} in {self.iter.to_python()}:"


@dataclass
class Comment(Statement):
    comment: str

    def to_python(self):
        return f"# {self.comment}"
