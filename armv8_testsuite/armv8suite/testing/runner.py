from __future__ import annotations
from functools import reduce
from pathlib import Path
import textwrap
import traceback
from typing import Any, Dict, List, Optional, Tuple

import subprocess as sp
import typing
from colorama import Fore

from result import Err, Ok, Result
from armv8suite.data import parsing
from armv8suite.data.cpu_state import CPU_State
from armv8suite.data.diffs import AssemblerDiffs
from armv8suite.data.parsing import ParseError

from armv8suite.data.result import (
    AssemblerResult,
    EmulatorResult,
    ResultType,
    Test,
    TestResult,
    write_process_state,
)
from armv8suite.testing.config import RunnerConfig
from armv8suite.testing.setup import STUDENT_MODE
from armv8suite.utils import is_defined
from armv8suite.utils.writer import StringWriter

###################################################################################################
""" Runner """


class RunnerResult:
    assembler: Dict[Test, AssemblerResult]
    emulator: Dict[Test, EmulatorResult]
    exceptions: Dict[Test, Exception]
    asm_summary: Dict[str, int]
    emu_summary: Dict[str, int]

    def __init__(
        self,
        assembler: Dict[Test, AssemblerResult],
        emulator: Dict[Test, EmulatorResult],
        exceptions: Dict[Test, Exception],
    ) -> None:
        self.assembler = assembler
        self.emulator = emulator
        self.exceptions = exceptions

        self.asm_summary = AssemblerResult.summarise(assembler.values())
        self.emu_summary = EmulatorResult.summarise(emulator.values())

    @staticmethod
    def _summarise(results: Dict[Test, TestResult]) -> Dict[str, int]:
        summary = {}
        summary["total"] = len(results)
        summary["correct"] = len([x for _, x in results.items() if x.result.is_ok()])
        summary["failed"] = len(
            [x for x in results.values() if x.result.value is ResultType.FAILED]
        )
        summary["incorrect"] = len(
            [x for x in results.values() if x.result.value is ResultType.INCORRECT]
        )
        return summary


###################################################################################################
""" Runner """


# def when_assemble(method):
#     @wraps(method)
#     def wrapper(self: Runner, *args, **kwargs) -> TestResult:
#         if self._emulator_only:
#             return
#         return method(self, *args, **kwargs)

#     return wrapper


# def when_emulate(method):
#     def wrapper(self: Runner, *args, **kwargs):
#         if self._assembler_only:
#             return
#         return method(self, *args, **kwargs)

#     return wrapper


class Runner:
    """Where to write test reports

    Attributes:
        cfg (RunnerConfig):
            Configuration for the runner
        id (Optional[int]):
            ID of the runner
        _logfile (Optional[Path]):
            File to write logs
        _assembler_results (Dict[Test, AssemblerResult]):
            Results of running the assembler on each test
        _emulator_results (Dict[Test, EmulatorResult]):
            Results of running the emulator on each test
        _exceptions (Dict[Test, Exception]):
            Exceptions raised during running of each test
    """

    def __init__(self, cfg: RunnerConfig, id: Optional[int] = None) -> None:
        if cfg is None:
            raise Exception("Runner not configured, cannot be initialised")
        self._cfg: RunnerConfig = cfg
        self._cfg.validate()

        self._logfile: Optional[Path] = self._cfg.logfile
        if id is not None:
            self.id: int = id
        self._assembler_results: Dict[Test, AssemblerResult] = {}
        self._emulator_results: Dict[Test, EmulatorResult] = {}
        self._exceptions: Dict[Test, Exception] = {}

        if self._cfg.is_multi_threaded:
            self._log_buffer: List[Tuple[tuple, Dict[str, Any]]] = []

    def _log(self, *args: object, **kwargs) -> None:
        if self._cfg.logfile:
            with open(self._cfg.logfile, "a") as f:
                print(*args, **kwargs, file=f)

        if self._cfg.verbose:
            if self._cfg.is_multi_threaded:
                self._log_buffer.append((args, kwargs))
            else:
                print(*args, **kwargs)

    def _log_exception(self, e: Exception):
        self._log(f"Exception: {e}")
        self._log("\n".join(traceback.format_exception(type(e), e, e.__traceback__)))

    def _log_test_result(self, result: TestResult):
        self._log(f"Test Result:\n{result}")

    def _log_when(self, when, *args, **kwargs):
        if when:
            if len(args) == 0:
                self._log(when, **kwargs)
            else:
                self._log(*args, **kwargs)

    def _log_pipe(self, p: sp.Popen[bytes]):
        if p.stdout:
            for line in p.stdout.readlines():
                line = line.decode()
                if line.endswith("\n"):
                    line = line[:-1]
                self._log(line)

    def _prepare_assembler_test(self, test: Test) -> Result[None, None]:
        """Generate expected assembly, binary and listing"""
        self._log(f"prepare assembly: {test}")

        if self._cfg.actual_only:
            return Ok()
        p = None
        try:
            with sp.Popen(
                [f"{self._cfg.toolchain_prefix}-as", test._path, "-o", test._exp_bin]
            ) as p:
                p.wait(self._cfg.process_wait_time)
                if p.returncode != 0:
                    return Err(None)

            with sp.Popen(
                [f"{self._cfg.toolchain_prefix}-objcopy", "-O", "binary", test._exp_bin]
            ) as p:
                p.wait(self._cfg.process_wait_time)
                if p.returncode != 0:
                    return Err(None)

            self._run_listing(test._exp_lst, test._exp_bin)

            return Ok(None)

        except sp.TimeoutExpired:
            if p is not None:
                p.kill()
            return Err(None)

    def _dump_process_state(self, process: sp.Popen | sp.CompletedProcess):
        l: StringWriter[str] = StringWriter()
        write_process_state(process, l)
        self._log(l)

    def _run_listing(self, listing: Optional[Path], binary: Path):
        if self._cfg.do_listings and listing is not None:
            with open(listing, "w") as lst, sp.Popen(
                [
                    f"{self._cfg.toolchain_prefix}-objdump",
                    "-b",
                    "binary",
                    "-m",
                    "aarch64",
                    "-D",
                    binary,
                ],
                stdout=lst,
            ) as p:
                p.wait(self._cfg.process_wait_time)
                if p.returncode != 0:
                    return Err(None)

    def _log_outcome(
        self, testtype: str, outcome: ResultType, test: Test, is_bad: bool = True
    ):
        self._log(
            f"\n{Fore.RED if is_bad else Fore.GREEN} {testtype} {outcome} {Fore.RESET}: test {test.name}"
        )

    def _process_assembler_out(
        self, test: Test, res: AssemblerResult, p: sp.Popen[bytes]
    ) -> AssemblerResult:
        """Assuming the assembler has been run, process the output and compare with expected"""
        p.wait(self._cfg.process_wait_time)
        if p.returncode != 0:
            res.log(f"Error: Running Assembler Failed with return code {p.returncode}")
            return res.with_result(ResultType.FAILED)

        if not test._act_bin.exists():
            res.log(f"Actual binary file not found: {test._act_bin}")
            return res.with_result(ResultType.FAILED)

        self._run_listing(test._act_lst, test._act_bin)
        diffs = AssemblerDiffs.compare_raw_bin(test._exp_bin, test._act_bin)

        if diffs:
            res.save_diffs(diffs)
            return res.with_result(ResultType.INCORRECT)

        return res.with_result(ResultType.CORRECT)

    def _handle_asm_timeout(
        self, p: sp.Popen[bytes], cmd: str, test: Test, res: AssemblerResult
    ) -> AssemblerResult:
        """Handle a timeout in the assembler"""
        p.kill()
        res.log("Error: Timeout")

        self._log(f"Timeout in test: {cmd}")
        self._log(f"\n{Fore.RED} ASSEMBLER CRASHED {Fore.RESET}: test {test._path}")
        return res.with_result(ResultType.FAILED)

    def _run_assembler_test(self, test: Test) -> AssemblerResult:
        """Run (student) assembler on test file `t`"""
        res = AssemblerResult(test)

        if self._cfg.emulator_only or self._cfg.expected_only:
            self._log("Skipping Assembler")
            return res.with_result(ResultType.CORRECT)

        cmd = [f"./{self._cfg.assembler}", test._path, test._act_bin]
        if not STUDENT_MODE and self._cfg.verbose:
            cmd.append("-v")
        cmd_str = reduce(lambda x, y: f"{x} {y}", cmd, "")
        self._log(f"run: {cmd_str}")
        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE) as p:
            try:
                res = self._process_assembler_out(test, res, p)
            except sp.TimeoutExpired:
                res = self._handle_asm_timeout(p, cmd_str, test, res)
            except Exception as e:
                self._log_exception(e)
                res.with_log_exception(e).with_result(ResultType.FAILED)
            res.save_process(p)

        self._log_outcome("ASSEMBLER", res.result, test, is_bad=res.result.is_err())
        self._log("Assembler Output:\n")
        self._log_test_result(res)
        return res

    def _prepare_emulator_test(
        self, test: Test
    ) -> Result[CPU_State, Optional[List[ParseError]]]:
        # Expected Emulation (this is expensive, so only done if the _log isn't available)

        cachefile = test._exp_out
        if cachefile.exists():
            expected_emulator_state = parsing.parse_out_file(cachefile)
        elif self._cfg.actual_only:
            raise Exception(f"Expected emulator output state not found at {cachefile}")
        else:
            return Err(None)

        return expected_emulator_state

    def _process_emulator_test(
        self,
        test: Test,
        res: EmulatorResult,
        exp_state: CPU_State,
        p: sp.Popen[bytes],
    ) -> EmulatorResult:
        p.wait(self._cfg.process_wait_time)

        if p.returncode != 0:
            res.log(f"Error: Running Emulator Failed with return code {p.returncode}")
            return res.with_result(ResultType.FAILED)

        if not test._act_out.exists():
            res.log(f"Actual .out file not found: {test._act_out}")
            return res.with_result(ResultType.FAILED)

        # Keeping Result changes local to this file
        parsed_out_state = parsing.parse_out_file(test._act_out)
        if parsed_out_state.is_err():
            errs: List[ParseError] = typing.cast(List[ParseError], parsed_out_state.err())
            
            p_errs = []
            for i, e in enumerate(errs):
                p_err = str(e).splitlines()
                p1, ps = p_err[0], p_err[1:]
                w = textwrap.TextWrapper(
                        width=80, initial_indent=f"    - ({i + 1}) ", subsequent_indent=" " * 10
                    )
                p_errs.extend(w.wrap(p1))

                w.initial_indent = w.subsequent_indent
                [p_errs.extend(w.wrap(p2)) for p2 in ps]

            # p_errs = "\n".join(p_errs)
            res.log(f"Error{'s' if len(errs) > 1 else ''} parsing .out File {test._act_out}:")
            res.logs(p_errs)
            return res.with_result(ResultType.FAILED)
        assert isinstance(parsed_out_state, Ok)

        out_state: CPU_State = parsed_out_state.ok()
        differences = exp_state.compare(out_state)

        if differences:
            res.save_diffs(differences)
            return res.with_result(ResultType.INCORRECT)

        return res.with_result(ResultType.CORRECT)

    def _handle_emu_timeout(
        self, p: sp.Popen[bytes], cmd: List[str], test: Test, res: EmulatorResult
    ) -> EmulatorResult:
        p.kill()
        res.log("Error: Timeout")

        self._log(f"Timeout in test: {cmd}")
        self._log_outcome("EMULATOR", ResultType.FAILED, test)
        return res.with_result(ResultType.FAILED)

    def _run_emulator_test(
        self, test: Test, exp_state: CPU_State, use_exp_bin: bool = False
    ) -> EmulatorResult:
        """Run expected and actual emulation on test file `as_file`."""
        res = EmulatorResult(test)
        if self._cfg.assembler_only or self._cfg.expected_only:
            self._log("Skipping Emulator")
            return res.with_result(ResultType.CORRECT)

        bin_to_run = test._exp_bin if use_exp_bin else test._act_bin

        cmd = [f"./{self._cfg.emulator}", bin_to_run, test._act_out]
        self._log(f'run: {reduce(lambda x, y: f"{x} {y}", cmd, "")}')

        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE) as p:
            try:
                res = self._process_emulator_test(test, res, exp_state, p)
            except sp.TimeoutExpired:
                res = self._handle_emu_timeout(p, cmd, test, res)
            except Exception as e:
                self._log(f"Exception in test {test}: {e}")
                res.with_log_exception(e).with_result(ResultType.FAILED)
            res.save_process(p)

        self._log_outcome("EMULATOR", res.result, test, is_bad=res.result.is_err())
        self._log_test_result(res)
        return res

    def _run_test(self, test: Test):
        """Runs expected/actual assembly and emulation tests for a single test in assembly file `t`"""
        self._log(f"Running test {test}")
        with open(test._path) as f:
            is_runnable = "RUNNABLE: False" not in f.readline()

        prep_res = self._prepare_assembler_test(test)
        if prep_res.is_err():
            self._log_outcome("PREPARE ASSEMBLER", ResultType.FAILED, test)
            return

        # Run the tests
        if not self._cfg.emulator_only:
            assembler_result = self._run_assembler_test(test)
            self._assembler_results[test] = assembler_result
            assembler_result.write_to_json(test._act_json)

        if (not is_runnable) or self._cfg.assembler_only:
            return

        exp_state = self._prepare_emulator_test(test)
        if not exp_state.is_ok():
            self._log_outcome("PREPARE EMULATOR", ResultType.FAILED, test)
            return

        elif not self._cfg.assembler_only:
            assert isinstance(exp_state, Ok)
            em_res = self._run_emulator_test(test, exp_state.ok(), use_exp_bin=True)
            self._emulator_results[test] = em_res
            em_res.write_to_json(test._act_json)

    def _flush_log_buffer(self):
        [print(*args, **kwargs) for args, kwargs in self._log_buffer]
        self._log_buffer = []

    def run(self) -> RunnerResult:
        for t in self._cfg.test_files:
            test = Test(t, self._cfg.testdir, self._cfg.actdir, self._cfg.expdir)
            try:
                self._run_test(test)
            except Exception as e:
                self._exceptions[test] = e
                print("Warning: Exception in test: ", test)
                print(
                    "\n".join(traceback.format_exception(type(e), e, e.__traceback__))
                )
            if self._cfg.is_multi_threaded:
                self._flush_log_buffer()
        return RunnerResult(
            self._assembler_results, self._emulator_results, self._exceptions
        )
