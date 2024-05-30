from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PState:
    """Representation of an ARM64 CPU's PState flags"""

    N: bool
    Z: bool
    C: bool
    V: bool

    def __init__(self, N: bool, Z: bool, C: bool, V: bool):
        self.N = N
        self.Z = Z
        self.C = C
        self.V = V

    def pretty_str(self) -> str:
        printVal = lambda name: name if self.__getattribute__(name) else "-"
        return f"{printVal('N')}{printVal('Z')}{printVal('C')}{printVal('V')}"

    def _to_bits(self) -> int:
        return (self.N << 3) | (self.Z << 2) | (self.C << 1) | self.V
    
    @staticmethod
    def from_str(s: str) -> PState:
        """ Assumes `s` is a valid pstate string """
        assert len(s) == 4 , f"Invalid pstate string: {s}"
        
        
        def check_char(c: str, idx: int) -> bool:
            is_clear = s[idx] == "-"
            assert is_clear or s[idx].lower() == c.lower(), f"Invalid pstate string: {s}"
            return not is_clear

        return PState(*(check_char(c, i) for i, c in enumerate("nzcv")))


