"""
Ways to report differences between expected and actual values for test output.

"""

from __future__ import annotations

# standard library
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Optional,
    TypeAlias,
    TypeVar,
    TypedDict,
)

# third party
from typing_extensions import Self

# local
from armv8suite.data.pstate import PState
from armv8suite.utils import map_optional
from armv8suite.utils.writer import StringWriter, Writer
from armv8suite.data.reg import Reg



def pad_str(s: str, length: int) -> str:
    """Pads a string with spaces to the left."""
    return ("  " * length) + s


def indent_writer(out: Writer[str]) -> Writer[str]:
    """Returns a Writer that indents all output by 2 spaces."""
    class IndentWriter(Writer[str]):
        def tell(self, t: str) -> None:
            out.tell(pad_str(t, 1))
    return IndentWriter()

###################################################################################################
""" Dict Utils """

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


###################################################################################################
""" Diff """

@dataclass
class Diff(Generic[V]):
    """
    Represents the difference between an expected and actual value.
    This is generic in V as there is a common way to represent differences between different types.
    """
    exp: V
    act: V

    def __str__(self):
        return f"Expected: {self.exp}\nActual: {self.act}"

    def to_dict(self, hexify: bool = True) -> Dict[str, V | str]:
        """
        Returns a dictionary representation of the Diff object with keys "exp" and "act".

        If hexify is True, then any integer values will be converted to a hex string.
        """
        exp, act = self.exp, self.act
        if hexify:
            if isinstance(self.exp, int):
                exp = hex(self.exp)
            if isinstance(self.act, int):
                act = hex(self.act)
        
        return {"exp": exp, "act": act}

    def map(self: Diff[V], f: Callable[[V], T]) -> Diff[T]:
        """ Functor map """
        return Diff(f(self.exp), f(self.act))

    @classmethod
    def from_dict(cls, d: Dict[str, V]) -> Self:
        """
        Create a Diff object from a dictionary containing (at least) the keys "exp" and "act".
        """
        if isinstance(d, Diff):
            return d
        return Diff(d["exp"], d["act"]) 
    
    def to_odiff(self) -> "ODiff[V]":
        return ODiff(self.exp, self.act)


class ODiff(Diff[Optional[V]]):
    """
    Represents the difference between an expected and actual value, where either value can be None.
    """
    @staticmethod
    def from_diff(d: Diff[V]) -> "ODiff[V]":
        return d.to_odiff()
    
    def map_optional(self, f: Callable[[V], T]) -> "ODiff[T]":
        return ODiff(map_optional(f, self.exp), map_optional(f, self.act))



###################################################################################################
""" Differences """

X = TypeVar("X", bound=Dict)

class Diffs(Generic[X], ABC):
    """
    A collection of differences between expected and actual values.
    """
    Dict: ClassVar[TypeAlias]
    JSON_Dict: ClassVar[TypeAlias]
    

    def __bool__(self) -> bool:
        """ Returns True if there are any differences. """
        return self.any_diffs()


    @abstractmethod
    def any_diffs(self) -> bool:
        """ Returns True if there are any differences. """
        pass

    @abstractmethod
    def _str_msg(self) -> str:
        """ Message to print before the differences. """
        pass

    def pretty(self) -> str:
        """ Returns a pretty string representation of the differences. """
        out: StringWriter[str] = StringWriter()
        self.to_writer(out, with_message=True)
        return out.to_string(join_with="\n")

    @abstractmethod
    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        pass

    def to_writer(self, out: Writer[str], with_message: bool = False) -> None:
        if not self:
            return
        if with_message:
            out.tell(self._str_msg())
        for i, act_tp in enumerate(["Actual", "Expected"]):
            self._to_writer(out, is_exp=i == 1, with_message=act_tp)

    @classmethod
    @abstractmethod
    def from_dict(cls, d: X) -> Self:
        pass

    @abstractmethod
    def _to_dict(
        self,
        recursive: bool,
        stringify_keys: bool,
        string_fuc: Callable[[Any], str],
        stringify_vals: bool,
        val_str_f: Callable[[Any], str],
    ) -> X:
        pass

    def to_dict(
        self,
        recursive: bool = False,
        stringify_keys: bool = False,
        key_str_f: Callable[[Any], str] = lambda x: str(x),
        stringify_vals: bool = False,
        val_str_f: Callable[[Any], str] = lambda x: str(x),
    ) -> X:
        return self._to_dict(recursive, stringify_keys, key_str_f, stringify_vals, val_str_f)


class DiffsDict(Dict[K, ODiff[V]], Diffs[Dict[K, Dict[str, V]]]):
    """ A collection of differences between expected and actual dictionaries. """
    Dict: ClassVar[TypeAlias] = Dict[K, Dict[str, V]]
    JSON_Dict: ClassVar[TypeAlias] = dict[str, dict[str, str]]


    def any_diffs(self) -> bool:
        return bool(dict(self))

    @classmethod
    def compare(cls, exp: Dict[K, V], act: Dict[K, V], null_val: Optional[V]=None) -> Self:
        """Compares two dictionaries and returns their difference in res"""
        res: Self = cls()
        for k in exp.keys() | act.keys():
            if k not in act:
                res[k] = ODiff(exp[k], null_val)
            elif k not in exp:
                res[k] = ODiff(null_val, act[k])
            elif k in act and exp[k] != act[k]:
                res[k] = ODiff(exp[k], act[k])
        return res

    def _to_dict(
        self,
        recursive: bool,
        stringify_keys: bool,
        key_str_f: Callable[[K], str],
        stringify_vals: bool,
        val_str_f: Callable[[V], str],
        
    ) -> Dict[K | str, Dict[str, V]] | Dict[K , Diff[V]]:
        key_str_f2 = key_str_f if stringify_keys else lambda x: x
        res = {}
        for k, v in self.items():
            if stringify_vals:
                res[key_str_f2(k)] =  v.map_optional(val_str_f)
            elif isinstance(v, Diff):
                res[key_str_f2(k)] = v.to_dict() if recursive else v
            elif isinstance(v, Diffs):
                res[key_str_f2(k)] = v.to_dict(recursive = True) if recursive else v
            else:
                res[key_str_f2(k)] = v
                
        return res


NZMems = Dict[int, int]
RegVals = Dict[Reg, int]


class NZMDiffs(DiffsDict[int, int]):
    def _str_msg(self) -> str:
        return "Non-zero Memory:"
    
    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        for k, v in self.items():
            val_str = prepare_hex_str(v.exp if is_exp else v.act)
            out.tell(f"0x{k:08x}: 0x{val_str}")

    @classmethod
    def from_dict(cls, d: NZMDiffs.JSON_Dict) -> NZMDiffs:
        return NZMDiffs({int(k, 16): Diff.from_dict(v).to_odiff().map_optional(lambda x: int(x, 16)) for k, v in d.items()})


class RegDiffs(DiffsDict[Reg, int]):
    def _str_msg(self) -> str:
        return "Registers:"
    
    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        for k, v in self.items():
            val_str = prepare_hex_str(v.exp if is_exp else v.act, hex_size=16)
            out.tell(f"{k.name:<3} = {val_str}")

    @classmethod
    def from_dict(cls, d: Dict) -> Self:
        if not d:
            return RegDiffs()
        res = {}
        for k, v in d.items():
            if isinstance(k, str):
                key = Reg.from_str(k)
            elif isinstance(k, Reg):
                key = k
            elif isinstance(k, int):
                key = Reg(k)
            else:
                raise Exception(f"Unknown key type: {type(k)}")

            if isinstance(v, Diff):
                val = v
            elif isinstance(v, Dict):
                val = Diff.from_dict(v)
            else:
                raise Exception(f"Unknown value type: {type(v)}")

            res[key] = val

        return RegDiffs(res)
    
def prepare_hex_str(val: Optional[int], hex_size=8) -> str:
    if val is not None:
        val_str = f"{val:0{hex_size}x}"
    else:
        val_str = "! No Value !"
    return val_str


class PStateDiff(Diff[PState], Diffs['PStateDiff']):
    
    Dict: ClassVar[TypeAlias] = Dict[str, str]
    JSON_Dict: ClassVar[TypeAlias] = dict[str, str]

    def any_diffs(self) -> bool:
        return True
    
    def _str_msg(self) -> str:
        return "PState:"
    
    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        out.tell(f"PState: {self.exp.pretty_str() if is_exp else self.act.pretty_str()}")

    def from_dict_str(self, d: Dict[str, str]) -> Self:
        return super().from_dict({k: PState.from_str(v) for k, v in d.items()})

    @staticmethod
    def from_dict(d: Dict[str, PState]) -> PStateDiff:
        return PStateDiff(d["exp"], d["act"])

    def to_dict(self, hexify: bool = True) -> Dict[str, PState | str]:
        return {"exp": self.exp.pretty_str(), "act": self.act.pretty_str()}

    def _to_dict(
        self,
        recursive: bool,
        stringify_keys: bool,
        string_fuc: Callable[[Any], str],
        stringify_vals: bool,
        val_str_f: Callable[[Any], str],
    ) -> Dict[str, str]:
        return Diff.to_dict(self.map(lambda x: x.pretty_str()), hexify=False)

    @staticmethod
    def compare(exp: PState, act: PState) -> Optional[PStateDiff]:
        if exp != act:
            return PStateDiff(exp, act)


###################################################################################################
""" Main Diffs """


class AssemblerDiffs(DiffsDict[int, int]):
    """ Diffs output by the assembler, comparing expected and actual binary files. """
    
    @classmethod
    def from_dict(cls, d: AssemblerDiffs.JSON_Dict) -> AssemblerDiffs:
        return AssemblerDiffs({int(k, 16): Diff.from_dict(v).to_odiff().map_optional(lambda x: int(x, 16)) for k, v in d.items()})
    
    def _str_msg(self) -> str:
        return "Assembler:"
    
    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        if not self:
            return
        if with_message:
            out.tell(with_message)
        for k, v in self.items():
            val_str = prepare_hex_str(v.exp if is_exp else v.act)
            out.tell(f"    {f'0x{k:x}':<6}: {val_str}")

    @staticmethod
    def compare_raw_bin(exp: Path, act: Path) -> AssemblerDiffs:
        """Compares two raw assembled binaries and returns their difference, if any"""
        diffs = AssemblerDiffs()
        with open(exp, "rb") as f1, open(act, "rb") as f2:
            """Compare non-zero words from start of files"""
            i = 0
            while True: #exp_word and act_word:
                exp_word = f1.read(4)
                act_word = f2.read(4)
                ew = int.from_bytes(exp_word, byteorder="little")
                aw = int.from_bytes(act_word, byteorder="little")
                if ew != aw:
                    diffs[i] = ODiff(ew, aw)
                    # Don't return yet, there might be more diffs

                i += 4
                if not (exp_word and act_word):
                    break

            """
            Sometimes, the ARM assembler will pad the end of `exp` with all zero instructions, 
            so is longer than `act`.
            In this case, check all remaining instructions in `exp` are zero.
            """

            j = 0
            if exp_word and not act_word:
                while exp_word:
                    exp_word = f1.read(4)
                    ew = int.from_bytes(exp_word, byteorder="little")
                    if ew != 0:
                        diffs[i + j] = ODiff(ew, None)
                    j += 4

        return diffs


class EmulatorDict(TypedDict, total=False):
    regs: RegVals
    nz_mem: NZMems
    pstate: PState

@dataclass(slots=True)
class EmulatorDiffs(Diffs["EmulatorDiffs"]):
    """ Diffs output by the emulator, comparing expected and actual register values, memory, and PState. """
    regs: RegDiffs
    nz_mem: NZMDiffs
    pstate: Optional[PStateDiff]
    
    REGS_KEY = "regs"
    NZ_MEM_KEY = "nz_mem"
    PSTATE_KEY = "pstate"
    
    class Dict(TypedDict, total=False):
        regs: RegDiffs.Dict
        nz_mem: NZMDiffs.Dict
        pstate: PStateDiff.Dict
        
    class JSON_Dict(TypedDict, total=False):
        regs: RegDiffs.JSON_Dict
        nz_mem: NZMDiffs.JSON_Dict
        pstate: PStateDiff.JSON_Dict

    def any_diffs(self) -> bool:
        return bool(self.regs) or bool(self.nz_mem) or bool(self.pstate)

    def __init__(
        self,
        regs: Optional[RegDiffs] = None,
        nz_mem: Optional[NZMDiffs] = None,
        pstate: Optional[PStateDiff] = None,
    ):
        self.regs: RegDiffs = RegDiffs() if regs is None else regs
        self.nz_mem: NZMDiffs = NZMDiffs() if nz_mem is None else nz_mem
        self.pstate: Optional[PStateDiff] = pstate


    def _str_msg(self) -> str:
        return "Emulator:"

    def compare(self, exp: EmulatorDict, act: EmulatorDict) -> EmulatorDiffs:
        regs, nz_mem, pstate = RegDiffs(), NZMDiffs(), None

        # TODO: handle cases when either exp or act is None

        if EmulatorDiffs.REGS_KEY in exp and EmulatorDiffs.REGS_KEY in act:
            regs = RegDiffs.compare(exp[EmulatorDiffs.REGS_KEY], act[EmulatorDiffs.REGS_KEY])

        if EmulatorDiffs.NZ_MEM_KEY in exp and EmulatorDiffs.NZ_MEM_KEY in act:
            nz_mem = NZMDiffs.compare(exp[EmulatorDiffs.NZ_MEM_KEY], act[EmulatorDiffs.NZ_MEM_KEY])

        if EmulatorDiffs.PSTATE_KEY in exp and EmulatorDiffs.PSTATE_KEY in act:
            pstate = PStateDiff.compare(exp[EmulatorDiffs.PSTATE_KEY], act[EmulatorDiffs.PSTATE_KEY])

        return EmulatorDiffs(regs, nz_mem, pstate)

    def _to_dict(
        self,
        recursive: bool,
        stringify_keys: bool,
        string_fuc: Callable[[Any], str],
        stringify_vals: bool,
        val_str_f: Callable[[Any], str]
        ) -> EmulatorDiffs.Dict:
        res: EmulatorDiffs.Dict = {}
        if self.nz_mem:
            res["nz_mem"] = self.nz_mem.to_dict(recursive=True)
        if self.regs:
            res["regs"] = self.regs.to_dict(stringify_keys=True, key_str_f=Reg.__str__, recursive=True)
        if self.pstate is not None:
            res["pstate"] = self.pstate.to_dict()
        return res

    def _to_writer(
        self, out: Writer[str], is_exp: bool, with_message: Optional[str] = None, indent: int = 0
    ) -> None:
        if not self.any_diffs():
            return
        if with_message:
            out.tell(with_message)
        if self.regs:
            self.regs._to_writer(indent_writer(out), is_exp)
        if self.pstate:
            self.pstate._to_writer(indent_writer(out), is_exp)
        if self.nz_mem:
            out.tell("Memory:")
            self.nz_mem._to_writer(indent_writer(out), is_exp)

    @staticmethod
    def from_dict(js: EmulatorDiffs.JSON_Dict) -> EmulatorDiffs:
        if "pstate" in js:
            pstate = PStateDiff.from_dict( {k: PState.from_str(v) for k, v in js["pstate"].items()} )
        else:
            pstate = None

        if "regs" in js:
            regs = RegDiffs.from_dict(js["regs"])
        else:
            regs = RegDiffs()

        if "nz_mem" in js:
            nz_mem = NZMDiffs.from_dict(js["nz_mem"])
        else:
            nz_mem = NZMDiffs()

        return EmulatorDiffs(regs, nz_mem, pstate)


