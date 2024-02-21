from __future__ import annotations

from dataclasses import dataclass, field

from codegen.models.ast import AST
from codegen.models.memory import Memory
from codegen.models.statement import BlockStatement, ImportStatement
from codegen.models.types import AST_ID


@dataclass(init=False)
class Program:
    root: AST
    memory: Memory
    import_manager: ImportManager

    def __init__(self):
        self.import_manager = ImportManager()
        self.memory = Memory()

        self.root = AST.root()
        self.root._add_stmt(self.import_manager)

    def get_ast_for_id(self, id: AST_ID) -> AST:
        ast = self.root.find_ast(id)
        if ast is None:
            raise KeyError(id)
        return ast


@dataclass
class ImportManager(BlockStatement):

    stmts: list[ImportStatement] = field(default_factory=list)

    def import_(self, module: str):
        if not any(stmt.module == module for stmt in self.stmts):
            self.stmts.append(ImportStatement(module))
