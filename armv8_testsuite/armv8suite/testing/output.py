from __future__ import annotations

from armv8suite.data.result import ResultType, Test, TestResult, TestType


STUDENT_MODE = True

# standard library
from pathlib import Path
from typing import Dict, Optional
import json

# third party
from colorama import Fore

# local
from armv8suite.testing.runner import RunnerResult


class JSONPrinter:
    _results: RunnerResult
    _outfile: Path
    
    def __init__(self, results: RunnerResult, outfile: Path) -> None:
        self._results = results
        self._outfile = outfile
        
    @property
    def outfile(self) -> Path:
        return self._outfile
    
    @property
    def results(self) -> RunnerResult:
        return self._results
    
    def write(self, assemble_only: bool=False, emulate_only: bool=False):
        js = {}
        if self.outfile.exists():
            try:
                with open(self.outfile, "r") as f:
                    js = json.load(f)
            except Exception as e:
                print(f"Error loading json file: {e}")
                raise e

        if not assemble_only:
            js["emulator_summary"] = self._results.emu_summary
            js[TestType.EMULATOR.key_name()] = {
                str(name): str(value.result)
                for name, value in self._results.emulator.items()
            }
        if not emulate_only:
            js["assembler_summary"] = self._results.asm_summary
            js[TestType.ASSEMBLER.key_name()] = {
                str(name): str(value.result)
                for name, value in self._results.assembler.items()
            }

        with open(self.outfile, "w") as f:
            json.dump(js, f, indent=4)


class PrettyPrinter:
    failures_only: bool = False
    results: Optional[RunnerResult] = None
    _assembler_only: bool = False
    _emulator_only: bool = False
    outfile: Optional[Path] = None

    def with_failures_only(self) -> PrettyPrinter:
        self.failures_only = True
        return self

    def with_results(self, results: RunnerResult) -> PrettyPrinter:
        self.results = results
        return self

    def with_outfile(self, outfile: Path) -> PrettyPrinter:
        self.outfile = outfile
        return self

        # Formats success or fail string

    def _right_or_wrong(self, succeeded: bool, success: str, fail: str) -> str:
        """Formats success or fail string.

        Returns a string in green if b is True, red if False
        """
        return (Fore.GREEN + success if succeeded else Fore.RED + fail) + Fore.RESET

    def _tell_summary(
        self, component_name: str, component_results: Dict[Test, TestResult]
    ):
        # Format Summary
        self.tell(f"———————————————————————\n{component_name} Summary:\n\n")

        maxTestNameLen = max(
            [len("test")] + [len(x.name) for x in component_results.keys()]
        )
        self.tell(f"{'Test':{maxTestNameLen}}  Correct  Incorrect  Failed  Total\n")

        total = len(component_results)
        failed = incorrect = correct = 0

        for result in component_results.values():
            if result.result.is_ok():
                correct += 1
            elif result.result.value is ResultType.FAILED:
                failed += 1
            else:
                incorrect += 1

        self.tell(
            f"\n{'Total':{maxTestNameLen}}  {correct:>7}  {incorrect:>9}  {failed:>6}  {total:>5}\n"
        )

    def _tell_results(
        self, component_name: str, component_results: Dict[Test, TestResult]
    ) -> None:
        self.tell(f"———————————————————————\n{component_name} Tests:\n")
        if len(component_results) == 0:
            self.tell(f"  {Fore.CYAN}None{Fore.RESET}\n")
            return
        # Fixes formatting if a test name is too long
        fmt_length = max(
            (len(test.name) for test in component_results.keys()), default=0
        )

        all_passed: bool = True
        for test, result in sorted(component_results.items(), key=lambda x: x[0].name):
            name = test.name
            completed = result.result.is_ok() or (
                result.result.is_err() and (result.result.value is not ResultType.FAILED)
            )
            completed_result = self._right_or_wrong(completed, "SUCCEEDED", "FAILED")
            correct_result = (
                self._right_or_wrong(result.result.is_ok(), "CORRECT", "INCORRECT")
                if completed
                else "-"
            )
            if (not self.failures_only) or result.result.is_err():
                self.tell(
                    f"   {name:{fmt_length}}:   {completed_result:{19}} {correct_result:}\n"
                )
            if result.result.is_err():
                all_passed = False
        if all_passed:
            self.tell(f"  {Fore.GREEN}All tests passed!{Fore.RESET}\n")

    def tell(self, s: str, *args, **kwargs):
        self._print(s, *args, end="", **kwargs)

    def _tell_results_when(
        self,
        when: bool,
        component_name: str,
        component_results: Dict[Test, TestResult],
    ) -> None:
        if when:
            self._tell_results(component_name, component_results)

    def _tell_summary_when(
        self,
        when: bool,
        component_name: str,
        component_results: Dict[Test, TestResult],
    ) -> None:
        if when:
            self._tell_summary(component_name, component_results)

    def _print(self, s: str, *args, **kwargs):
        if self.outfile is None:
            print(s, *args, **kwargs)
        else:
            with open(self.outfile, "a") as f:
                print(s, *args, file=f, **kwargs)
            
    def write(self):
        self.tell("\n")

        self._tell_results_when(
            not self._emulator_only, "Assembler", self.results.assembler # type: ignore
        )
        self._tell_results_when(
            not self._assembler_only, "Emulator", self.results.emulator # type: ignore
        )
        self._tell_summary_when(
            not self._emulator_only, "Assembler", self.results.assembler # type: ignore
        )
        self._tell_summary_when(
            not self._assembler_only, "Emulator", self.results.emulator # type: ignore
        )
        self.tell("\n")

