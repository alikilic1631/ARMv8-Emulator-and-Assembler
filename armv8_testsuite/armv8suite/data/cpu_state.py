""" 
Data definitions for the emulator output state
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from armv8suite.data.diffs import EmulatorDiffs, NZMDiffs, PStateDiff, RegDiffs
from armv8suite.data.pstate import PState
from armv8suite.data.reg import Reg

###################################################################################################
""" CPU State """


@dataclass(slots=True)
class CPU_State:
    """Final CPU State"""

    regs: Dict[Reg, int]
    pstate: PState
    nz_mem: Dict[int, int]

    def dump(self, file: Path):
        """Write the CPU state to a file"""
        with open(file, "w") as f:
            f.write("Registers:\n")
            for reg in Reg:
                f.write(f"{reg.name:<7}= {self.regs[reg]:016x}\n")
            f.write(f"PSTATE : {self.pstate.pretty_str()}\n")
            f.write(f"Non-Zero Memory:\n")
            for addr in sorted(self.nz_mem.keys()):
                f.write(f"0x{addr:08x} : {self.nz_mem[addr]:08x}\n")

    def compare(self, act: "CPU_State") -> EmulatorDiffs:
        """
        Compares two CPU states and returns their difference, if any.

        Returns a tuple of (True, {}) if the states are equal,
        otherwise returns (False, diff) where diff is a dictionary of the differences.
        """
        
        r_diff = RegDiffs.compare(self.regs, act.regs)
        m_diff = NZMDiffs.compare(self.nz_mem, act.nz_mem)
        p_diff = PStateDiff.compare(self.pstate, act.pstate)

        return EmulatorDiffs(r_diff, m_diff, p_diff)
