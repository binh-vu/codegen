from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import pandas as pd

KEY = str | tuple
REGISTER_TYPE = Literal["var"]


@dataclass
class Memory:
    registers: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(columns=["id", "name", "key", "type"])
    )

    def register(self, name: str, key: Optional[KEY], type: REGISTER_TYPE):
        register_id = len(self.registers)
        self.registers.loc[register_id] = [register_id, name, key, type]
        return register_id

    def get_one(self, register_id: int) -> pd.Series:
        return self.registers.iloc[register_id]

    def find_one(
        self, *, name: Optional[str], key: Optional[KEY], type: REGISTER_TYPE
    ) -> int:
        if key is None:
            assert name is not None
            query = (self.registers["name"] == name) & (self.registers["type"] == type)
        elif name is None:
            assert key is not None
            query = (self.registers["key"] == key) & (self.registers["type"] == type)
        else:
            query = (
                (self.registers["name"] == name)
                & (self.registers["key"] == key)
                & (self.registers["type"] == type)
            )
        res = self.registers[query]
        if len(res) == 0:
            raise ValueError(
                f"Cannot find register of {type} for {name} with key {key}"
            )
        if len(res) > 1:
            raise ValueError(
                f"Found multiple registers of {type} for {name} with key {key}"
            )
        return res.iloc[0]["id"]


@dataclass
class Var:  # variable
    name: str
    key: Optional[KEY]
    register_id: int

    def get_name(self) -> str:
        return f"{self.name}_{self.register_id}"

    @staticmethod
    def create(mem: Memory, name: str, key: Optional[KEY] = None):
        return Var(name, key, mem.register(name, key, "var"))

    @staticmethod
    def deref(mem: Memory, *, name: Optional[str] = None, key: Optional[KEY] = None):
        regid = mem.find_one(name=name, key=key, type="var")
        record = mem.get_one(regid)
        return Var(record["name"], record["key"], regid)
