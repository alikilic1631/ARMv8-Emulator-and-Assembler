from __future__ import annotations

# standard library
from dataclasses import dataclass
import traceback
from typing import Dict, List
from json import JSONDecodeError
from pathlib import Path

# 3rd party imports
from flask import render_template

# local imports
from armv8suite.data.diffs import AssemblerDiffs, EmulatorDiffs
from armv8suite.data.result import TestType
from armv8suite.utils.writer import ListWriter


def nice_bin_str(bin_str: bytes) -> List[str]:
    """Convert a binary string to a nice string representation"""
    lines = []
    for i in range(0, len(bin_str), 4):
        curr_word = bin_str[i : i + 4]
        lines.append(f"{i:04x}:    {curr_word.hex()}")

    return lines


def nice_out_str(out_str: str) -> List[str]:
    return out_str.splitlines()


def prepare_err_str(err: Exception) -> List[str]:
    """Prepare an error string for display by turning into list of lines"""
    return traceback.format_exception(type(err), err, err.__traceback__)


# from test.test_runner import TestType
# import test.run_tests as run_tests

@dataclass(slots=True)
class TemplateArgs:
    test_type: str
    test_type_name: str
    title_suffix: str
    exec_name: str
    args: List[str]
    read_mode: str

_test_type_to_template_args: Dict[TestType, TemplateArgs] = {
    TestType.ASSEMBLER: TemplateArgs(
        test_type=TestType.ASSEMBLER.key_name(),
        test_type_name="Assembler",
        title_suffix="Assembler",
        exec_name="assembler",
        args=["-A"],
        read_mode="rb",
    ),
    TestType.EMULATOR: TemplateArgs(
        test_type=TestType.EMULATOR.key_name(),
        test_type_name="Emulator",
        title_suffix= "Emulator",
        exec_name="emulator",
        args=["-E"],
        read_mode="r"
    )
}


def test_type_to_template_args(test_type: TestType) -> TemplateArgs:
    return _test_type_to_template_args[test_type]


###################################################################################################
# Single Test Rendering

def render_single_fnf_error(test_file: Path | str) -> str:
    return render_template(
        "single_file_not_found_error.jinja",
        fname=str(test_file),
        file_not_found_error=True,
    )


def render_exec_nf_error(exec_name: str) -> str:
    return render_template(
        "file_not_found_error.jinja",
        executable_not_found=True,
        executable_name=exec_name,
    )


def render_single_json_decode_error(test_file: Path | str, err: JSONDecodeError, test_type_verb: str) -> str:
    return render_template(
        "individual_exec_error.jinja",
        fname=str(test_file),
        json_decode_error=True,
        json_decode_error_msg=prepare_err_str(err),
        test_type_verb=test_type_verb
    )
    
def render_json_decode_error(err: JSONDecodeError, test_type_verb: str) -> str:
    return render_template(
        "exec_error.jinja",
        json_decode_error=True,
        json_decode_error_msg=prepare_err_str(err),
        test_type_verb=test_type_verb
    )
    
def render_generic_error(err: Exception, test_type_verb: str) -> str:
    return render_template(
        "exec_error.jinja",
        generic_error=True,
        generic_error_msg=prepare_err_str(err),
        test_type_verb=test_type_verb
    )


def render_single_generic_error(test_file: Path | str, err: Exception, test_type_verb: str) -> str:
    return render_template(
        "individual_exec_error.jinja",
        fname=str(test_file),
        generic_error=True,
        generic_error_msg=prepare_err_str(err),
        test_type_verb=test_type_verb
    )


def render_exec_failed_error(test_file: Path | str, log: List[str], test_type_verb: str) -> str:
    return render_template(
        "individual_exec_error.jinja",
        fname=str(test_file),
        exec_failed_error=True,
        log=log,
        test_type_verb=test_type_verb
    )


def render_individual_valid(
    test_file: Path | str,
    test_is_correct: bool,
    act_out: bytes | str,
    exp_out: bytes | str,
    test_type: TestType,
    log: List[str],
    diffs: AssemblerDiffs | EmulatorDiffs | None
) -> str:
    test_type_name = test_type_to_template_args(test_type).test_type_name

    lw: ListWriter[str] = ListWriter()
    if test_type == TestType.ASSEMBLER:
        if diffs is not None:
            assert isinstance(diffs, AssemblerDiffs)
            AssemblerDiffs.to_writer(diffs, lw)
        
        assert isinstance(act_out, bytes)
        assert isinstance(exp_out, bytes)
        
        act_nice = nice_bin_str(act_out)
        exp_nice = nice_bin_str(exp_out)
        output_name = "Binary"
    else:
        if diffs is not None:
            assert isinstance(diffs, EmulatorDiffs)
            EmulatorDiffs.to_writer(diffs, lw)

        assert isinstance(act_out, str)
        assert isinstance(exp_out, str)
        
        act_nice = nice_out_str(act_out)
        exp_nice = nice_out_str(exp_out)
        output_name = "Output"
    diffs_strs = lw.to_list()

    return render_template(
        "individual_success.jinja",
        fname=str(test_file),
        test_is_correct=test_is_correct,
        actual_output=act_nice,
        expected_output=exp_nice,
        test_type=test_type_name,
        output_name=output_name,
        log=log,
        diffs=diffs_strs,
        title=f"{test_type_name} Test Results",
    )

