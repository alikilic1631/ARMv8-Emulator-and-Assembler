from __future__ import annotations

# standard library
from abc import ABC, abstractmethod
from enum import Enum
import subprocess as sp
from pathlib import Path
from typing import (
    IO,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    TypedDict,
)
import typing
import json
import tempfile
import traceback

# pypi
from typing_extensions import Self

# local
from armv8suite.data.diffs import AssemblerDiffs, Diffs, EmulatorDiffs
from armv8suite.utils import SizedIterable
from armv8suite.utils.decorators import extend_error
from armv8suite.utils.writer import StringWriter, ListWriter, Writer

###################################################################################################
""" Test """

def write_process_state(process: sp.Popen[bytes] | sp.CompletedProcess, out: Writer[str]):
    if isinstance(process, sp.CompletedProcess):
        text, err = process.stdout, process.stderr
    else:
        text, err = process.communicate(b"\n")
    if text or err:
        out.tell("Process Output:\n")
    if text:
        out.tells(text.decode().split("\n"))
    if err:
        out.tells(err.decode().split("\n"))

###################################################################################################
""" Result Enums """


class ResultType(Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    FAILED = "FAILED"

    def __str__(self) -> str:
        return self.value

    def json_name(self) -> str:
        return self.value

    def __bool__(self) -> bool:
        return self.is_ok()

    def is_err(self) -> bool:
        return self is not ResultType.CORRECT

    def is_ok(self) -> bool:
        return self is ResultType.CORRECT
    
    @staticmethod
    def from_str(s: str) -> ResultType:
        """ Raises a ValueError if the string is not a valid ResultType. """
        return ResultType(s.upper())


class TestType(Enum):
    ASSEMBLER = "ASSEMBLER"
    EMULATOR = "EMULATOR"

    def key_name(self) -> str:
        return self.value.lower()
    
    @staticmethod
    def from_str(s: str) -> TestType:
        return TestType(s.upper())


###################################################################################################
""" Test """


class Test(object):
    def __init__(self, path: Path, rootdir: Path, actdir: Path, expdir: Path) -> None:
        super().__init__()
        self._path: Path = path

        sub_test = path.relative_to(rootdir)
        act_base = actdir / sub_test.with_suffix("")
        act_base.parent.mkdir(parents=True, exist_ok=True)

        exp_base = expdir / sub_test
        exp_base = exp_base.parent / f"{exp_base.stem}_exp"

        self.relative: Path = sub_test
        self.name: str = str(self.relative)

        self._act_json: Path = act_base.with_suffix(".json")
        self._act_lst: Path = act_base.with_suffix(".lst")
        self._act_bin: Path = act_base.with_suffix(".bin")
        self._act_out: Path = act_base.with_suffix(".out")
        self._exp_lst: Path = exp_base.with_suffix(".lst")
        self._exp_bin: Path = exp_base.with_suffix(".bin")
        self._exp_out: Path = exp_base.with_suffix(".out")

        self._assemble_only = False
        self._emulate_only = False

    def assemble_only(self) -> None:
        self._assemble_only = True

    def emulate_only(self) -> None:
        self._emulate_only = True

    def _open_file(self, outfile: Path, mode: str, do_open: bool) -> IO[Any]:
        if do_open:
            return outfile.open(mode)
        else:
            return tempfile.NamedTemporaryFile(mode=mode)

    def open_actual_listing(self) -> IO[Any]:
        return self._open_file(self._act_lst, "w", self._emulate_only)

    def open_expected_listing(self) -> IO[Any]:
        return open(self._exp_lst, "w", self._emulate_only)

    def open_actual_binary(self) -> IO[Any]:
        return open(self._act_bin, "wb", self._emulate_only)

    def open_expected_binary(self) -> IO[Any]:
        return open(self._exp_bin, "wb", self._emulate_only)

    def open_actual_out_state(self) -> IO[Any]:
        return open(self._act_out, "w", self._assemble_only)

    def open_expected_out_state(self) -> IO[Any]:
        return open(self._exp_out, "w", self._assemble_only)

    def __str__(self) -> str:
        return str(self._path)


###################################################################################################
""" Test Results """


D = TypeVar("D", EmulatorDiffs, AssemblerDiffs, covariant=True)
DDict = TypeVar("DDict", EmulatorDiffs.Dict, AssemblerDiffs.Dict)


class TestResult(Generic[D, DDict], ABC):
    # __slots__ = ["test", "type", "result", "diff", "_log", "_diff_class"]

    DIFF_KEY: str = "diff"
    LOG_KEY: str = "log"
    RESULT_KEY: str = "result"
    TEST_KEY: str = "test"

    class InnerDict(TypedDict, total=False):
        """ The info on the result """
        result: str
        log: List[str]
        diff: Dict

    class Dict(TypedDict, total=False):
        test: str
        inner: TestResult.InnerDict

    def __str__(self) -> str:
        return self.pretty()

    def diff_class(self) -> type[Diffs]:
        return self._diff_class

    def __init__(self, test: Test, ttype: TestType) -> None:
        self.test: Test = test
        self.type: TestType = ttype
        self.result: ResultType = None  # type: ignore
        self.diff: Optional[D] = None
        self._diff_class: type[Diffs] = (
            EmulatorDiffs if ttype is TestType.EMULATOR else AssemblerDiffs
        )
        self._log: List[str] = []

    def pretty(self) -> str:
        out = [f"Test: {self.test}", f"Type: {self.type.name}"]

        if self.result is not None:
            out.append(f"Result: {self.result}")
        if self.diff:
            out.append(self._diffs_to_str(self.diff))
            # if self.type is TestType.EMULATOR:
            #     out.append(self._(self.diff))
            # else:
        if self._log:
            out += ["Log: "] + self._log
        return "\n".join(out)

    @staticmethod
    def _diffs_to_str(diffs: D) -> str: # type: ignore
        sw: StringWriter[str] = StringWriter()
        diffs.to_writer(sw, with_message=True)
        return sw.to_string(join_with="\n")

    def diffs_to_str(self) -> str:
        if self.diff is None:
            return ""
        return self._diffs_to_str(self.diff)

    def write_to_json(self, result_json: Path) -> None:
        js: TestResult.Dict
        try:
            with open(result_json, "r") as f:
                js = TestResult.Dict(json.load(f))
        except:
            js = TestResult.Dict(test=str(self.test._path))

        _diff = self.diff.to_dict(recursive=True) if self.diff else None

        to_write = TestResult.InnerDict(
            result=str(self.result), 
            log=self._log if self._log else [], 
            diff=typing.cast(Dict, _diff)
        )

        # to_write: TestResult.InnerDict = {}
        # to_write[TestResult.RESULT_KEY] = str(self.result)
        # to_write[TestResult.LOG_KEY] = self._log if self._log else []
        # to_write[TestResult.DIFF_KEY] = (
        #     self.diff.to_dict(recursive=True) if self.diff else None
        # )
        js[self.type.key_name()] = to_write

        with open(result_json, "w") as f:
            json.dump(js, f, indent=4)

    @staticmethod
    @extend_error("When reading test result json")
    def from_json_tp(result_json: Path, test_type: TestType) -> TestResult:
        if test_type is TestType.ASSEMBLER:
            return AssemblerResult.from_json(result_json)
        else:
            return EmulatorResult.from_json(result_json)

    @classmethod
    @extend_error("When reading test result json")
    def from_json(cls, result_json: Path) -> Self:
        with open(result_json, "r") as f:
            js: Dict = json.load(f)

        return cls.from_dict(js)

    @staticmethod
    def from_dict_tp(js: Dict, test: Test, test_type: TestType) -> TestResult:
        if test_type is TestType.ASSEMBLER:
            return AssemblerResult.from_dict(js, test)
        else:
            return EmulatorResult.from_dict(js, test)

    @classmethod
    @abstractmethod
    def from_test(cls, test: Test) -> Self:
        pass

    @classmethod
    @abstractmethod
    def _diff_from_dict(cls, js: DDict) -> D:
        pass

    @classmethod
    @extend_error("When converting test result from dict")
    def from_dict(cls, js: TestResult.Dict, test: Test) -> Self:
        """ Turn a dictionary into a TestResult. The dictionary is usually from a json. """
        res = cls.from_test(test)

        js_sub: TestResult.InnerDict = js[res.type.key_name()]
        res.result = ResultType(js_sub[TestResult.RESULT_KEY])

        res._log = js_sub.get(TestResult.LOG_KEY, [])
        res.diff = js_sub.get(TestResult.DIFF_KEY, None)
        if res.diff:
            res.diff = cls._diff_from_dict(res.diff)
        return res

    def with_result(self, result: ResultType) -> Self:
        self.result: ResultType = result
        return self

    def with_log_exception(self, e: Exception) -> Self:
        es = traceback.format_exception(type(e), e, e.__traceback__)
        self._log += es
        return self

    def log(self, *args: str) -> None:
        self._log += args

    def logs(self, args: List[str]) -> None:
        self._log += args

    def save_diffs(self, diffs: D) -> None: # type: ignore
        self.diff = diffs

    def save_process(self, proc: sp.Popen[bytes]) -> None:
        wr: ListWriter[str] = ListWriter()
        write_process_state(proc, wr)
        self._log += wr.to_list()
        
    @classmethod
    def summarise(cls, results: SizedIterable[Self]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        summary["total"] = len(results)
        summary["correct"] = len([x for x in results if x.result is ResultType.CORRECT])
        summary["failed"] = len(
            [x for x in results if x.result is ResultType.FAILED]
        )
        summary["incorrect"] = len(
            [x for x in results if x.result is ResultType.INCORRECT]
        )
        return summary

class AssemblerResult(TestResult[AssemblerDiffs, AssemblerDiffs.Dict]):
    def __init__(self, test: Test) -> None:
        super().__init__(test, TestType.ASSEMBLER)

    @classmethod
    def from_test(cls, test: Test) -> AssemblerResult:
        return AssemblerResult(test)

    @classmethod
    def _diff_from_dict(cls, js: AssemblerDiffs.JSON_Dict) -> AssemblerDiffs:
        return AssemblerDiffs.from_dict(js)


class EmulatorResult(TestResult[EmulatorDiffs, EmulatorDiffs.Dict]):
    def __init__(self, test: Test) -> None:
        super().__init__(test, TestType.EMULATOR)

    @staticmethod
    def from_test(test: Test) -> EmulatorResult:
        return EmulatorResult(test)

    @classmethod
    def _diff_from_dict(cls, js: EmulatorDiffs.JSON_Dict) -> EmulatorDiffs:
        return EmulatorDiffs.from_dict(js)
