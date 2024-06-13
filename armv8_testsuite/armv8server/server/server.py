from __future__ import annotations

from typing import Any, Dict, List, Tuple, TypedDict

import json
from json import JSONDecodeError
import os
from pathlib import Path

# 3rd party imports
import flask
from flask import render_template, Flask
from result import Err, Ok, Result
from armv8suite.data.result import ResultType, Test, TestResult

# local imports
from armv8suite.routes import *
from armv8suite.testing.cli import run_and_write_tests_with_args, run_and_write_tests_with_args_get_cfg
from armv8suite.utils import make_executable


from armv8server.app import app

from armv8server.server.render import *
from armv8server.setup.setup import setup_app
import armv8server.setup.routes as routes
import armv8server.data as s_data
import armv8server.data.result as s_result


###################################################################################################
# Template Pages

# homepage
def index():
    return render_template("index.jinja")


# page to find specific test to assemble
def find_test(test_type: TestType):
    root = Path(TEST_CASES_DIR)
    names = [f.relative_to(root) for f in root.rglob("*.s")]

    return render_template(
        "find_test.jinja", names=names, fname=test_type.key_name(), title="List of Tests"
    )


class ResultsCount(TypedDict):
    vals: List[ResultType]
    num_cor: int
    num_inc: int
    num_fail: int
    files: List[str]


def count_results(res: Dict[str, ResultType]) -> ResultsCount:
    """Count the number of correct, incorrect, and failed tests in a dictionary of results"""
    vals = list(res.values())
    res_ = ResultsCount(
        vals=vals,
        num_cor=vals.count(ResultType.CORRECT),
        num_inc=vals.count(ResultType.INCORRECT),
        num_fail=vals.count(ResultType.FAILED),
        files=list(res.keys()),
    )
    return res_


###################################################################################################
# Loading Results JSONs


def load_from_json(json_path: Path) -> Result[Dict[str, Any], JSONDecodeError]:
    """Load the results from a json file"""
    try:
        with open(json_path, "r") as f:
            res = json.load(f)
        return Ok(res)
    except JSONDecodeError as e:
        return Err(e)


class ExecNotFoundError(FileNotFoundError):
    pass


def parse_result_json(
    out_json: Path,
    args: List[str],
    test_type: TestType,
    when_to_run: bool = False,
    keys_to_check: List[str] = [],
) -> Result[Dict[str, Any], Exception]:
    """Tries to load the results json, reruns the tests if json not present or invalid"""
    run_anyway = False

    def _try_parse_json() -> Result[Dict[str, Any], Exception]:
        if not out_json.exists():
            app.logger.info(f"Results json {out_json} does not exist, rerunning")
            return Err(FileNotFoundError(f"Results json `{out_json}` does not exist"))
        load_res = load_from_json(out_json)
        if isinstance(load_res, Err):
            return Err(load_res.err())
        elif keys_to_check:
            res = load_res.ok()
            missing_keys = [k for k in keys_to_check if k not in res]
            if any(missing_keys):
                app.logger.info(
                    f"Results json {out_json} does not contain required fields: `{list(missing_keys)}`, rerunning"
                )
                return Err(
                    KeyError(
                        f"Results json `{out_json}` is missing field(s): {list(missing_keys)}"
                    )
                )
            elif len(res[keys_to_check[0]]) <= 1:
                app.logger.info(
                    f"Results json {out_json} does not contain any tests, rerunning"
                )
                return Err(
                    ValueError(
                        f"Results json `{out_json}` contains no relevant tests: {res[keys_to_check[0]]}"
                    )
                )
        return Ok(load_res.ok())

    load_res = _try_parse_json()

    if load_res.is_err():
        if isinstance(load_res.err(), JSONDecodeError):
            app.logger.warning(f"Could not load results from {out_json}, removing json")
            out_json.unlink()
    run_anyway = load_res.is_err()

    # execs = parse_config(CONFIG)

    # if not executable.exists():
    #     return Err(ExecNotFoundError(f"Executable {executable} does not exist"))
    # elif not executable.is_file():
    #     return Err(ExecNotFoundError(f"Executable {executable} is not a file"))

    # executable_last_modified = os.path.getmtime(executable)
    # json_last_modified = os.path.getmtime(out_json) if out_json.exists() else 0

    if (
        run_anyway
        or not out_json.exists()
        or when_to_run
        # or executable_last_modified >= json_last_modified
        or load_res is None
        or load_res.is_err()
    ):
        app.logger.info(f"(Re)running test(s) with args: {args}")
        try:
            res, cfg = run_and_write_tests_with_args_get_cfg(args)
        except Exception as e:
            return Err(e)
        load_res = load_from_json(out_json)

    second_check = _try_parse_json()
    if second_check.is_err():
        return second_check

    if load_res is None:
        return Err(Exception("No results json loaded"))

    return load_res


###################################################################################################
# Run All Tests


def run_all_common(args: List[str], test_type: TestType) -> str:
    """Run all tests of a given type, and return the results in a template"""
    get_args = test_type_to_template_args(test_type)
    force_run = False
    if flask.request.method == "POST":
        if flask.request.form.get("run_all_button") == "Run All Tests":
            app.logger.info("Set all tests to run")
            force_run = True

    out_json = Path(OUT_ALL)
    sub_type = test_type.key_name()
    results_name = sub_type

    res = parse_result_json(
        out_json,
        args,
        test_type=test_type,
        when_to_run=force_run,
        keys_to_check=[sub_type, f"{sub_type}_summary"],
    )

    if isinstance(res, Err):
        res = res.err()
        if isinstance(res, ExecNotFoundError):
            return render_exec_nf_error(exec_name=get_args.exec_name)
        elif isinstance(res, JSONDecodeError):
            return render_json_decode_error(res, test_type_verb=get_args.exec_name)
        else:
            return render_generic_error(res, test_type_verb=get_args.exec_name)

    assert isinstance(res, Ok)

    res_old = res.ok()
    res_: Dict[str, str] = res_old[sub_type]
    res_summary = res_old[f"{sub_type}_summary"]

    if len(res_) < 2:
        return render_generic_error(
            Exception("No tests found"), test_type_verb=get_args.exec_name
        )
    files, results = res_.keys(), res_.values()

    files = [Path(f).relative_to(Path(TEST_CASES_DIR)) for f in files]
    results = [s_result.column_template(ResultType(r)) for r in results]

    return render_template(
        "all_tests.jinja",
        results=results,
        files=files,
        num_cor=res_summary["correct"],
        num_inc=res_summary["incorrect"],
        num_fail=res_summary["failed"],
        total_tests=res_summary["total"],
        link_portion=test_type.key_name(),
        title=results_name,
    )


# page to assemble all tests
def assemble_all_tests() -> str:
    return run_all_common(
        ["-A"],
        TestType.ASSEMBLER,
    )


# page to emulate all tests
def emulate_all_tests() -> str:
    return run_all_common(
        ["-E"],
        TestType.EMULATOR,
    )


###################################################################################################
# Single Tests


def test_type_get_out_files(test_type: TestType, test: Test) -> Tuple[Path, Path]:
    if test_type == TestType.ASSEMBLER:
        return (test._act_bin, test._exp_bin)
    elif test_type == TestType.EMULATOR:
        return (test._act_out, test._exp_out)
    else:
        raise ValueError(f"Invalid test type: {test_type}")


def run_single_common(test_file_name: str, test_type: TestType):
    get_args = test_type_to_template_args(test_type)
    sub_type = get_args.test_type
    title_suffix = get_args.title_suffix
    args = get_args.args
    read_mode = get_args.read_mode

    test_file: Path = TEST_CASES_DIR_PATH / Path(test_file_name).with_suffix(".s")
    test = Test(
        test_file, Path(TEST_CASES_DIR), Path(TEST_ACTUAL_DIR), Path(TEST_EXPECTED_DIR)
    )
    act_file, exp_file = test_type_get_out_files(test_type, test)

    if not exp_file.exists():
        return render_single_fnf_error(test_file_name)

    out_json: Path = test._act_json

    res = parse_result_json(
        out_json,
        args + [str(test_file)],
        when_to_run=any(not f.exists() for f in [act_file, test._act_json]),
        keys_to_check=[sub_type],
        test_type=test_type,
    )

    if isinstance(res, Err):
        res = res.err()
        if isinstance(res, ExecNotFoundError):
            return render_exec_nf_error(exec_name=get_args.exec_name)
        elif isinstance(res, JSONDecodeError):
            return render_single_json_decode_error(
                test_file_name, res, test_type_verb=get_args.exec_name
            )
        else:
            return render_single_generic_error(
                test_file_name, res, test_type_verb=get_args.exec_name
            )

    assert isinstance(res, Ok)

    res = res.ok()
    res_tr: TestResult
    try:
        res_tr = TestResult.from_dict_tp(res, test, test_type)
    except Exception as e:
        return render_single_generic_error(
            test_file_name, e, test_type_verb=get_args.exec_name
        )
        
    assert isinstance(res_tr, TestResult)

    result_type: ResultType = res_tr.result

    if result_type is ResultType.FAILED:
        res_log = res_tr._log
        return render_exec_failed_error(
            test_file_name, res_log, test_type_verb=get_args.exec_name
        )

    with open(act_file, read_mode) as f:
        act_out = f.read()
    with open(exp_file, read_mode) as f:
        exp_out = f.read()
        
    diffs = res_tr.diff
    if diffs is not None:
        assert isinstance(diffs, (AssemblerDiffs, EmulatorDiffs))

    return render_individual_valid(
        test_file=test_file_name,
        test_is_correct=result_type.is_ok(),
        act_out=act_out,
        exp_out=exp_out,
        test_type=test_type,
        log=res_tr._log,
        diffs=diffs,
    )


# page to assemble a single tests
def assemble_individual(fname: str):
    app.logger.info(f"Retrieve individual assembler test: {fname}")
    tmpl = run_single_common(fname, TestType.ASSEMBLER)
    return tmpl


# page to emulate a specific test
def emulate_individual(fname: str):
    app.logger.info(f"Emulating individual test: {fname}")
    tmpl = run_single_common(fname, TestType.EMULATOR)
    return tmpl
