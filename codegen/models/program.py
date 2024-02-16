from __future__ import annotations

from dataclasses import dataclass

from codegen.models.ast import AST
from codegen.models.memory import Memory
from codegen.models.types import AST_ID


@dataclass(init=False)
class Program:
    root: AST
    memory: Memory

    def __init__(self):
        self.root = AST.root()
        self.memory = Memory()

    def get_ast_for_id(self, id: AST_ID) -> AST:
        ast = self.root.find_ast(id)
        if ast is None:
            raise KeyError(id)
        return ast
