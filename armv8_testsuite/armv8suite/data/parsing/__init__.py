from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple

from result import Err, Ok, Result
from armv8suite.data.cpu_state import CPU_State
from armv8suite.data.pstate import PState
from armv8suite.data.reg import NUM_G_REGS, Reg, str_reg_list
from armv8suite.utils import result_tuple


class ParseError:
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"Parse Error: {self.msg}"


class LineParseError(ParseError):
    def __init__(self, line: str, msg: str, line_num: int):
        self.line = line
        self.line_num = line_num
        super().__init__(msg)

    def __str__(self):
        return f"Parse Error in line {self.line_num}:\n    | {self.line}\n{self.msg}"


class ParseErrors:
    class Reg(LineParseError):
        def __init__(self, line: str, line_num: int):
            msg = f"Invalid register line: '{line}'"
            super().__init__(line, msg, line_num)

    class RegVal(LineParseError):
        def __init__(self, line: str, val: str, line_num: int):
            msg = f"Invalid register value: {val}"
            super().__init__(line, msg, line_num)

    class GRegName(LineParseError):
        def __init__(self, line: str, reg: str, line_num: int):
            msg = f"Invalid general register number: '{reg}'"
            super().__init__(line, msg, line_num)

    class NBitVal(LineParseError):
        def __init__(self, line: str, bitwidth: int, val: str, line_num: int):
            msg = f"{bitwidth}-bit value out of range: '{val}'"
            super().__init__(line, msg, line_num)

    class NotHex(LineParseError):
        def __init__(self, line: str, val: str, line_num: int):
            msg = f"Invalid hex value: '{val}'"
            super().__init__(line, msg, line_num)

    class RegName(LineParseError):
        def __init__(self, line: str, reg: str, line_num: int):
            msg = f"Invalid register name: '{reg}'"
            super().__init__(line, msg, line_num)

    class PStateLine(LineParseError):
        def __init__(self, line: str, line_num: int):
            msg = f"Invalid PState line: '{line}'"
            super().__init__(line, msg, line_num)

    class PStateLen(LineParseError):
        def __init__(self, line: str, pstate: str, line_num: int):
            msg = f"PState value string must be 4 characters long: '{pstate}'"
            super().__init__(line, msg, line_num)

    class PStateChar(LineParseError):
        def __init__(self, line: str, idx: int, ch: str, line_num: int):
            msg = f"PState string must be '-' or '{ch}' at index {idx}"
            super().__init__(line, msg, line_num)

    class DuplicateReg(LineParseError):
        def __init__(self, line: str, reg: Reg, line_num: int):
            msg = f"Duplicate register: '{reg}'"
            super().__init__(line, msg, line_num)

    class DuplicateNZMAddr(LineParseError):
        def __init__(self, line: str, addr: int, line_num: int):
            msg = f"Duplicate Non-zero memory address: '{addr}'"
            super().__init__(line, msg, line_num)

    class DuplicatePState(LineParseError):
        def __init__(self, line: str, line_num: int):
            msg = f"Duplicate PState line: '{line}'"
            super().__init__(line, msg, line_num)

    class NZMemLine(LineParseError):
        def __init__(self, line: str, line_num: int):
            msg = f"Invalid Non-zero memory line: '{line}'"
            super().__init__(line, msg, line_num)

    class NZMemAddrNotMultipleOf4(LineParseError):
        def __init__(self, line: str, addr: int, line_num: int):
            msg = f"Non-zero memory address must be a multiple of 4: '{addr}'"
            super().__init__(line, msg, line_num)

    class IgnoredLine(LineParseError):
        def __init__(self, line: str, line_num: int):
            msg = f"Ignored line: '{line}'"
            super().__init__(line, msg, line_num)

    class CPURegs(ParseError):
        def __init__(self, regs: Set[Reg]):
            missing_regs = set(Reg).difference(regs)
            extra_regs = regs.difference(set(Reg))
            missing = sorted(list(missing_regs))
            extra = sorted(list(extra_regs))

            self.msg = (f"Missing registers: {str_reg_list(missing)}" if missing else "")  \
                + (f"Unknown registers: {str_reg_list(extra)}"   if extra else "")
            if not missing and not extra:
                self.msg = "Error parsing CPU registers"

    class CPU_PStateNotFound(ParseError):
        def __init__(self):
            super().__init__("No PState line found")

    class CPU_NZMem(ParseError):
        def __init__(self, msg: str):
            super().__init__(msg)
            
            
def parse_PState(line: str, line_num: int) -> Result[PState, LineParseError]:
    """Parses a PState line of the form 'NZCV' where each character is either '-' or 'N', 'Z', 'C', or 'V'"""
    toks = [x.strip() for x in line.split(":")]
    if len(toks) != 2:
        return Err(ParseErrors.PStateLine(line, line_num))
    _, pstate = toks
    if len(pstate) != 4:
        return Err(ParseErrors.PStateLen(line, pstate, line_num))

    def check_char(c: str, idx: int) -> Result[bool, LineParseError]:
        if pstate[idx] == "-":
            return Ok(False)
        if pstate[idx].lower() == c.lower():
            return Ok(True)
        else:
            return Err(ParseErrors.PStateChar(line, idx, c, line_num))

    return result_tuple(
        *(check_char(c, i) for i, c in enumerate("nzcv"))
    ).and_then(lambda x: Ok(PState(*x)))

def parse_g_reg(line: str, reg_num: str, line_num: int) -> Result[Reg, LineParseError]:
    """Parses a general register number of the form 'nn'"""
    if reg_num.isdigit():
        val = int(reg_num)
        if 0 <= val < NUM_G_REGS:
            return Ok(Reg(val))
    return Err(ParseErrors.GRegName(line, reg_num, line_num))


def parse_reg(line: str, name: str, line_num: int) -> Result[Reg, LineParseError]:
    """Parses a register name of the form 'Xnn' or 'PC'"""
    is_g_reg = re.search(r"(?<=X)([0-3])?[0-9]$", name, re.IGNORECASE)
    is_pc = re.search(r"^PC$", name, re.IGNORECASE)
    if is_g_reg and is_g_reg.group(0):
        return parse_g_reg(line, is_g_reg.group(0), line_num)
    elif is_pc:
        return Ok(Reg.PC)
    else:
        return Err(ParseErrors.RegName(line, name, line_num))


def parse_n_bit_value(
    line: str, value: str, bitwidth: int, line_num: int
) -> Result[int, LineParseError]:
    """Parses a n-bit hex value"""
    try:
        x = int(value, 16)
    except ValueError:
        return Err(ParseErrors.NotHex(line, value, line_num))
    if x < 0 or x > (2**bitwidth) - 1:
        return Err(ParseErrors.NBitVal(line, bitwidth, value, line_num))
    return Ok(x)




def parse_reg_value_line(line: str, line_num: int) -> Result[Tuple[Reg, int], LineParseError]:
    """Parses a line of the form 'Xnn = 0xnnnnnnnnnnnnnnnn'"""
    toks = [tok.strip() for tok in line.split("=")]
    if len(toks) != 2:
        return Err(ParseErrors.Reg(line, line_num))
    reg, x = toks
    reg_val = parse_reg(line, reg, line_num)
    x_val = parse_n_bit_value(line, x, 64, line_num)

    return result_tuple(reg_val, x_val)


def parse_nzm_line(line: str, line_num: int) -> Result[Optional[Tuple[int, int]], LineParseError]:
    """Parses a line of the form '0xnnnnnnnn : 0xnnnnnnnnnnnnnnnn'

    Ok(None) when just a filler line
    """
    toks = [tok.strip() for tok in line.split(":")]
    if len(toks) != 2:
        return Err(ParseErrors.NZMemLine(line, line_num))
    addr, val = toks
    addr_val = parse_n_bit_value(line, addr, 64, line_num)

    if (
        addr_val.is_err()
        and isinstance(addr_val.err(), ParseErrors.NotHex)
        and len(toks[1]) == 0
    ):
        return Ok(None)
    if addr_val.is_ok() and addr_val.unwrap() % 4 != 0:
        addr_val = Err(ParseErrors.NZMemAddrNotMultipleOf4(line, addr_val.unwrap(), line_num))
    mem_val = parse_n_bit_value(line, val, 32, line_num)

    return result_tuple(addr_val, mem_val)

class Parser():
    def __init__(self) -> None:
        self.line_num = 0

    def parse_out_file(self, actState: Path) -> Result[CPU_State, List[ParseError]]:
        """Parses the custom `.out` file to a CPU_State object"""
        pstate: Optional[Result[PState, ParseError]] = None
        ignored: List[ParseErrors.IgnoredLine] = []
        regs: Dict[Reg, int] = {}
        nzmem: Dict[int, int] = {}
        errs: List[ParseError] = []
        line_num = 0
        with open(actState, "r") as f:
            for line in f.readlines():
                line_num += 1
                if line.isspace() or len(line) == 0:
                    continue
                line = line.strip()
                if line.lower().startswith("pstate"):
                    if pstate is not None:
                        errs.append(ParseErrors.DuplicatePState(line, line_num))
                        continue
                    pstate = parse_PState(line, line_num)
                # Registers
                elif "=" in line:
                    res = parse_reg_value_line(line, line_num)
                    if res.is_err():
                        errs.append(res.unwrap_err())
                        continue
                    assert isinstance(res, Ok)
                    reg, val = res.ok()
                    if reg in regs:
                        errs.append(ParseErrors.DuplicateReg(line, reg, line_num))
                        continue
                    regs[reg] = val

                # Non-zero memory
                elif ":" in line:
                    res = parse_nzm_line(line, line_num)
                    if res.is_err():
                        errs.append(res.unwrap_err())
                        continue
                    elif res.ok() is None:
                        continue
                    addr, val = res.ok() # type: ignore
                    if addr in nzmem:
                        errs.append(ParseErrors.DuplicateNZMAddr(line, addr, line_num))
                        continue
                    nzmem[addr] = val
                else:
                    ignored.append(ParseErrors.IgnoredLine(line, line_num))

            if pstate is None:
                errs.append(ParseErrors.CPU_PStateNotFound())
            elif pstate.is_err():
                errs.append(pstate.unwrap_err())
            else:
                pstate = pstate.unwrap() # type: ignore

            if set(regs.keys()) != set(Reg):
                errs.append(ParseErrors.CPURegs(set(regs.keys())))

            if len(errs) == 0:
                assert isinstance(pstate, PState)
                return Ok(CPU_State(regs, pstate, nzmem))
            else:
                return Err(errs + ignored)

def parse_out_file(actState: Path) -> Result[CPU_State, List[ParseError]]:
    p = Parser()
    return p.parse_out_file(actState)
    