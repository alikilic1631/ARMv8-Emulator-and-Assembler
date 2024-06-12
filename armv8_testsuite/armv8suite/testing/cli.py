from __future__ import annotations

STUDENT_MODE = True

# standard library
import subprocess
import os
import multiprocessing as mp
from pathlib import Path
from typing import List, Tuple
import argparse

# local
import armv8suite.routes as routes
from armv8suite.testing.config import RunnerConfig
from armv8suite.testing.output import JSONPrinter, PrettyPrinter
from armv8suite.testing.runner import Runner, RunnerResult



if STUDENT_MODE:
    DEFAULT_ACT_OUTDIR = routes.TEST_ACTUAL_DIR
    DEFAULT_EXP_OUTDIR = routes.TEST_EXPECTED_DIR
    DEFAULT_OUT_JSON = routes.OUT_ALL
    DEFAULT_TEST_CASES_DIR = routes.TEST_CASES_DIR
    DEFAULT_GEN_DIR = f"{routes.TEST_CASES_DIR}/generated"
    DEFAULT_ASSEMBLER = routes.ASSEMBLER_PATH
    DEFAULT_EMULATOR = routes.EMULATOR_PATH
else:
    DEFAULT_ACT_OUTDIR = "out"
    DEFAULT_EXP_OUTDIR = "test/expected"
    DEFAULT_OUT_JSON = "out/results.json"
    DEFAULT_TEST_CASES_DIR = "test/test_cases"
    DEFAULT_GEN_DIR = "test/test_cases/generated"
    DEFAULT_ASSEMBLER = "build/assemble"
    DEFAULT_EMULATOR = "build/emulate"


def setup_params() -> argparse.ArgumentParser:
    """ argparse commandline arguments setup. """
    parser = argparse.ArgumentParser(description="Run emulator and assembler tests")

    common = parser.add_argument_group("common options")

    common.add_argument(
        "testfiles", metavar="testfiles", nargs="*", help="input file(s)"
    )
    common.add_argument(
        "-a", 
        "--assembler", 
        help="path to assembler to test"
    )
    common.add_argument(
        "-e", 
        "--emulator", 
        help="path to emulator to test"
    )
    common.add_argument(
        "-H",
        "--help-extra",
        help="show this help message and exit",
        action="store_true",
        default=False,
    )

    common.add_argument(
        "-t",
        "--testdir",
        help="directory containing test files",
        default=DEFAULT_TEST_CASES_DIR,
    )

    extra = parser.add_argument_group("extra options")
    extra.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="run verbose"
    )
    extra.add_argument(
        "-p",
        "--pretty-print",
        action="store_true",
        help="pretty print results",
        default=False,
    )
    extra.add_argument("-l", "--logfile", help="file to log output")
    extra.add_argument(
        "-o", 
        "--outfile", 
        help="file to write results", 
        default=DEFAULT_OUT_JSON
    )

    extra.add_argument(
        "--outdir",
        help="directory to write intermediate test files",
        default=DEFAULT_ACT_OUTDIR,
    )

    extra.add_argument(
        "--actdir", 
        help="directory to write test results ", 
        default=DEFAULT_ACT_OUTDIR
    )
    extra.add_argument(
        "--expdir",
        help="directory containing expected results ",
        default=DEFAULT_EXP_OUTDIR,
    )

    extra.add_argument(
        "-A",
        "--assembler-only",
        action="store_true",
        help="run assembler tests only",
        default=False,
    )

    extra.add_argument(
        "-E",
        "--emulator-only",
        action="store_true",
        help="run emulator tests only",
        default=False,
    )

    extra.add_argument(
        "-f",
        "--failures",
        action="store_true",
        help="output failures only",
        default=False,
    )

    extra.add_argument(
        "--toolchain",
        help="path to arm toolchain bin folder",
    )

    extra.add_argument(
        "--multi-threaded",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    # These are only for non-student use
    if not STUDENT_MODE:
        supervisor = parser.add_argument_group("supervisor options (NOT FOR STUDENTS)")
        supervisor.add_argument(
            "-g", "--generate", action="store_true", help="generate tests"
        )
        supervisor.add_argument(
            "-X",
            "--expected-only",
            action="store_true",
            help="only generate expected results",
        )

        supervisor.add_argument(
            "-Y",
            "--actual-only",
            action="store_true",
            help="only generate actual results",
        )

        supervisor.add_argument(
            "-G", "--generate-only", action="store_true", help="generate tests only"
        )

        supervisor.add_argument(
            "--thorough-memory-check",
            action="store_true",
            help="run unicorn memory checker",
            default=False,
        )

        supervisor.add_argument(
            "--seed", help="seed to initialise random number generator", default=42
        )
        supervisor.add_argument(
            "--noout",
            action="store_true",
            help="Don't save intermediate results and files",
            default=False,
        )
    return parser


def parse_args(args_list: List[str]) -> argparse.Namespace:
    """ Parse list of arguments from commandline. """
    parser = setup_params()
    args: argparse.Namespace = parser.parse_args(args_list)
    return args


def setup_config_with_args(args_list: List[str]) -> RunnerConfig:
    """ Setup a test-runner configuration with commandline arguments. """
    args = parse_args(args_list)
    return setup_config(args)


def setup_config(args: argparse.Namespace) -> RunnerConfig:
    """ Setup a test-runner configuration with commandline arguments parsed by argparse namespace. """
    make_cmd = ["make"]
    if not args.verbose:
        make_cmd += ["--silent"]
    if not STUDENT_MODE and not args.generate_only:
        subprocess.check_call(make_cmd)

    if args.emulator_only and args.assembler_only:
        raise Exception(
            "Can't have both -A (--assembler-only) and -E (--emulator-only)"
        )

    #######################################################################################################
    # Which tests to run
    tests_to_run = []

    test_dir = Path(args.testdir)

    if len(args.testfiles) == 0:
        is_run_all = True
        tests_to_run = [path for path in test_dir.rglob("*.s")]
    else:
        is_run_all = False
        for testfile in args.testfiles:
            testfilepath = Path(testfile)
            if not testfilepath.exists():
                raise FileNotFoundError(f"{testfilepath} does not exist")
            # assert testfilepath.exists(), f"{testfilepath} does not exist"
            if testfilepath.is_dir():
                tests_to_run += [path for path in Path(testfilepath).rglob("*.s")]
            else:
                tests_to_run += [testfilepath]

    #######################################################################################################

    cfg = RunnerConfig(
        actdir=args.actdir,
        expdir=args.expdir,
        testdir=args.testdir,
        testfiles=tests_to_run,
        assembler=args.assembler,
        emulator=args.emulator,
        verbose=args.verbose,
        assembler_only=args.assembler_only,
        emulator_only=args.emulator_only,
        logfile=args.logfile,
        is_multi_threaded=args.multi_threaded,
    )

    if args.toolchain is not None:
        cfg._setup_arm_toolchain(args.toolchain)

    if not STUDENT_MODE:
        (
            cfg.with_expected_only(args.expected_only)
            .with_actual_only(args.actual_only)
            # .with_thorough_memory_check(args.thorough_memory_check)
        )
    else:
        cfg.with_actual_only(True)

    val_res = cfg.validate()
    if val_res.is_err():
        raise Exception(val_res.err())

    return cfg


def run_tests_with_args(args_list: List[str]) -> RunnerResult:
    args = parse_args(args_list)
    cfg = setup_config(args)
    return run_tests_with_cfg(cfg)


def write_run_results(
    args: argparse.Namespace, cfg: RunnerConfig, results: RunnerResult
) -> None:
    if args.pretty_print:
        pp = PrettyPrinter().with_results(results)
        pp._emulator_only = args.emulator_only
        pp._assembler_only = args.assembler_only

        if args.failures:
            pp.with_failures_only()

        pp.write()


    if args.outfile and cfg.is_run_all:
        out_path = Path(args.outfile)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        jp = JSONPrinter(results, out_path)
        jp.write(assemble_only=args.assembler_only, emulate_only=args.emulator_only)


def run_tests_single_process_with_cfg(cfg: RunnerConfig) -> RunnerResult:
    runner = Runner(cfg)
    try:
        results = runner.run()
    except FileNotFoundError as e:
        print(f"File {e.filename} not found")
        raise e
    except Exception as e:
        raise e

    return results


def _run_tests_process(cfg: RunnerConfig) -> RunnerResult:
    runner = Runner(cfg, cfg.id)
    try:
        results = runner.run()
    except FileNotFoundError as e:
        print(f"File {e.filename} not found")
        raise e
    except Exception as e:
        raise e
    return results


def run_tests_multi_process_with_cfg(cfg: RunnerConfig) -> RunnerResult:
    try:
        num_procs = max(
            min(mp.cpu_count() - 1, len(cfg.test_files) // 25),
            1
        )
    except NotImplementedError:
        num_procs = 1

    test_chunks = [cfg.test_files[i::num_procs] for i in range(num_procs)]
    cfgs = [
        cfg.copy().with_test_files(test_chunk).with_id(i)
        for i, test_chunk in enumerate(test_chunks)
    ]

    with mp.Pool(num_procs) as pool:
        results = pool.map(_run_tests_process, cfgs)

    asm_results, ems_results, excs_results = {}, {}, {}
    for res in results:
        asm_results.update(res.assembler)
        ems_results.update(res.emulator)
        excs_results.update(res.exceptions)

    results = RunnerResult(asm_results, ems_results, excs_results)

    return results


def run_tests_with_cfg(cfg: RunnerConfig) -> RunnerResult:
    if not cfg.is_multi_threaded or len(cfg.test_files) < 30:
        cfg.is_multi_threaded = False
        return run_tests_single_process_with_cfg(cfg)
    else:
        return run_tests_multi_process_with_cfg(cfg)



def run_and_write_tests_with_args_get_cfg(args: List[str]) -> Tuple[RunnerResult, RunnerConfig]:
    args_ = parse_args(args)
    cfg = setup_config(args_)
    results = run_tests_with_cfg(cfg)
    write_run_results(args_, cfg, results)
    return results, cfg

def run_and_write_tests_with_args(args: List[str]) -> RunnerResult:
    return run_and_write_tests_with_args_get_cfg(args)[0]