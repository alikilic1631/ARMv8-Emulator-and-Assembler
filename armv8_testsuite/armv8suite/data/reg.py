from __future__ import annotations

from enum import Enum, IntEnum, auto
from typing import List


class Reg(IntEnum):
    X00 = 0
    X01 = auto()
    X02 = auto()
    X03 = auto()
    X04 = auto()
    X05 = auto()
    X06 = auto()
    X07 = auto()
    X08 = auto()
    X09 = auto()
    X10 = auto()
    X11 = auto()
    X12 = auto()
    X13 = auto()
    X14 = auto()
    X15 = auto()
    X16 = auto()
    X17 = auto()
    X18 = auto()
    X19 = auto()
    X20 = auto()
    X21 = auto()
    X22 = auto()
    X23 = auto()
    X24 = auto()
    X25 = auto()
    X26 = auto()
    X27 = auto()
    X28 = auto()
    X29 = auto()
    X30 = auto()
    PC = auto()

    def __str__(self) -> str:
        return self.name
    
    @staticmethod
    def from_str(s: str) -> "Reg":
        return Reg[s]


_reg_names: list[str] = Reg._member_names_
_reg_dict: dict[str, Enum] = Reg._member_map_
NUM_REGS: int = len(_reg_names)
NUM_G_REGS: int = NUM_REGS - 1

def str_reg_list(regs: List[Reg]) -> str:
    return str([str(reg) for reg in regs])
