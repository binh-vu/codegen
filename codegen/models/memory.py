from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, NamedTuple, Optional, cast

import pandas as pd
from codegen.models.types import (
    AST_ID,
    KEY,
    NO_AST_ID,
    NO_KEY,
    NO_SCOPE,
    REGISTER_TYPE,
    SCOPE,
    is_ast_same_or_ancestor_of,
)


@dataclass
class MemoryRecord:
    id: int
    name: str
    key: KEY
    scope: SCOPE
    type: REGISTER_TYPE


@dataclass
class Memory:
    counter: int = 0
    registers: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=["id", "name", "key", "scope", "type"],
        )
    )

    def register(
        self,
        name: str,
        key: KEY,
        scope: SCOPE,
        type: REGISTER_TYPE,
        strict: bool,
    ):
        """
        Args:
            strict: if True, raise an error if there is a register with the same name, key, and type.
        """
        if strict:
            matched_records = self.find(name=name, key=key, type=type)
        else:
            matched_records = self.find(name=name, key=key, scope=scope, type=type)

        if len(matched_records) > 0:
            raise ValueError(
                f"There is already a register with the same name={name}, key={key}, scope={scope} (if strict=True), and type={type}"
            )

        register_id = self.counter
        self.counter += 1
        self.registers.loc[register_id] = [register_id, name, key, scope, type]
        return register_id

    def remove_one(self, register_id: int) -> None:
        self.registers = self.registers.drop(register_id)

    def get_one(self, register_id: int) -> MemoryRecord:
        reg = self.registers.loc[register_id]
        return MemoryRecord(
            reg["id"], reg["name"], reg["key"], reg["scope"], reg["type"]
        )

    def update_scope(self, register_id: int, scope: SCOPE):
        self.registers.at[register_id, "scope"] = scope

    def find(
        self,
        *,
        name: Optional[str] = None,
        key: Optional[KEY] = None,
        scope: Optional[SCOPE] = None,
        type: Optional[REGISTER_TYPE] = None,
    ) -> list[MemoryRecord]:
        conditions = []
        if name is not None:
            conditions.append(self.registers["name"] == name)
        if key is not None:
            conditions.append(self.registers["key"] == key)
        if scope is not None:
            conditions.append(self.registers["scope"] == scope)
        if type is not None:
            conditions.append(self.registers["type"] == type)

        assert len(conditions) > 0
        query = conditions[0]
        for cond in conditions[1:]:
            query = query & cond

        res = self.registers[query]
        out = []
        for i in range(len(res)):
            x = res.iloc[i]
            out.append(
                MemoryRecord(x["id"], x["name"], x["key"], x["scope"], x["type"])
            )
        return out

    def find_one(
        self,
        *,
        name: Optional[str] = None,
        key: Optional[KEY] = None,
        scope: Optional[SCOPE] = None,
        type: Optional[REGISTER_TYPE] = None,
    ) -> MemoryRecord:
        res = self.find(name=name, key=key, scope=scope, type=type)
        if len(res) == 0:
            raise ValueError(
                f"Cannot find a register matched name={name}, key={key}, scope={scope}, type={type}"
            )
        if len(res) > 1:
            raise ValueError(
                f"Found multiple registers matched name={name}, key={key}, scope={scope}, type={type}"
            )
        return res[0]


class VarScope(NamedTuple):
    ast: AST_ID  # the ast that has a child, which is an assign statement, that the first time the variable is defined
    child_index: int  # the index of the child (assign statement)

    def is_subscope_of(self, scope: VarScope) -> bool:
        if scope.ast == self.ast:
            return scope.child_index <= self.child_index
        return is_ast_same_or_ancestor_of(scope.ast, self.ast)


@dataclass
class Var:  # variable
    name: str
    key: Optional[KEY]
    register_id: int
    scope: Optional[VarScope]

    def get_name(self) -> str:
        return f"{self.name}_{self.register_id}"

    def set_scope(self, mem: Memory, scope: VarScope):
        assert self.scope == None, "Cannot change the scope of a variable"
        assert (
            mem.get_one(self.register_id).scope == NO_SCOPE
        ), "Cannot change the scope of a variable"

        self.scope = scope
        mem.update_scope(self.register_id, scope)

    def delete(self, mem: Memory):
        mem.remove_one(self.register_id)

    @staticmethod
    def create(
        mem: Memory,
        name: str,
        key: KEY = NO_KEY,
        scope: Optional[VarScope] = None,
        strict: bool = True,
    ):
        return Var(
            name,
            key,
            mem.register(name, key, scope or NO_SCOPE, "var", strict),
            scope,
        )

    @staticmethod
    def deref(
        mem: Memory,
        *,
        name: Optional[str] = None,
        key: Optional[KEY] = None,
        scope: Optional[VarScope] = None,
    ) -> Var:
        reg = mem.find_one(name=name, key=key, scope=scope, type="var")
        if reg.scope == NO_SCOPE:
            scope = None
        else:
            scope = cast(VarScope, reg.scope)
        return Var(reg.name, reg.key, reg.id, scope)

    @staticmethod
    def find_by_scope(mem: Memory, scope: VarScope) -> list[Var]:
        """Find all variables that were defined in the given scope."""
        vars = []
        for reg in mem.find(type="var"):
            if reg.scope != NO_SCOPE and cast(VarScope, reg.scope).is_subscope_of(
                scope
            ):
                vars.append(Var(reg.name, reg.key, reg.id, cast(VarScope, reg.scope)))
        return vars
