from __future__ import annotations

# standard library
import subprocess as sp
from pathlib import Path
from typing import Dict, List, Optional

# third party
from result import Ok, Err, Result
from armv8suite import routes
from armv8suite.routes import CONFIG, parse_config

from armv8suite.utils import make_executable

###################################################################################################
""" Runner Config """


# @dataclass(slots=True)
class RunnerConfig:
    """
    Attributes:
        _logfile: Path to logfile
        _outdir: Path to test output directory
        _assembler: Path to assembler to run
        _emulator: Path to emulator to run
        _toolchain_prefix: Prefix for toolchain binaries
        _verbose: Whether to print verbose output
        _assembler_only: Whether to only run the assembler
        _emulator_only: Whether to only run the emulator

    """

    logfile: Optional[Path] = None
    toolchain_prefix: Optional[str] = None

    actdir: Path
    expdir: Path
    testdir: Path
    test_files: List[Path]
    is_multi_threaded: bool = False

    assembler: Path
    emulator: Path

    verbose: bool = False
    assembler_only: bool = False
    emulator_only: bool = False
    expected_only: bool = False
    actual_only: bool = False
    is_run_all: bool = True

    do_listings: bool = False
    process_wait_time = 1

    def __init__(
        self,
        actdir: Optional[Path | str],
        expdir: Optional[Path | str],
        testdir: Optional[Path | str],
        testfiles: Optional[List[Path]],
        assembler: Optional[Path | str],
        emulator: Optional[Path | str],
        logfile: Optional[Path | str],
        verbose: bool = False,
        assembler_only: bool = False,
        emulator_only: bool = False,
        expected_only: bool = False,
        actual_only: bool = False,
        do_listings: bool = False,
        process_wait_time: int = 1,
        is_run_all: bool = True,
        is_multi_threaded: bool = False,
        id: Optional[int] = None,
    ) -> None:
        self.with_test_files(testfiles)
        self.verbose = verbose
        self.assembler_only = assembler_only
        self._setup_arm_toolchain(None)
        self.emulator_only = emulator_only
        self.expected_only = expected_only
        self.actual_only = actual_only
        self.do_listings = do_listings
        self.process_wait_time = process_wait_time

        self.logfile = self._prep_path_like(logfile, prep_parent=True)
        self.actdir = self._prep_path_like(actdir, prep_dir=True)
        self.expdir = self._prep_path_like(expdir)
        self.testdir = self._prep_path_like(testdir)
        
        d = parse_config(CONFIG, ignore_assembler=self.emulator_only, ignore_emulator=self.assembler_only)
            
            
        self.assembler = self.prep_exec(d, assembler, "assembler", is_used=not self.emulator_only)
        self.emulator = self.prep_exec(d, emulator, "emulator", is_used=not self.assembler_only)
        
        self.is_run_all = is_run_all
        self.is_multi_threaded = is_multi_threaded
        if is_multi_threaded:
            self.id = id
            # if not hasattr(self, "_print_lock"):
            # self._print_lock: LockT = Lock()

    @staticmethod
    def prep_exec(config: Dict[str, str], exec_: Optional[Path | str], key: str, is_used: bool):
        if exec_ is None:
            if key in config:
                exec_ = config[key]
            else:
                exec_ = routes.ASSEMBLER_PATH
        exec_ = RunnerConfig._prep_path_like(exec_)
        if is_used:
            make_executable(exec_)
        return exec_

    def _setup_arm_toolchain(self, path_to_toolchain: Optional[str]) -> None:
        """Adds arm toolchain if installed"""
        raise_err = False
        try:
            if path_to_toolchain is None:
                toolchain = "aarch64-none-elf"
            else:
                toolchain = f"{path_to_toolchain}/aarch64-none-elf"
            sp.call([f"{toolchain}-objdump", "--version"], stdout=sp.DEVNULL)

            self.toolchain_prefix = toolchain
        except FileNotFoundError:
            raise_err = True
        if raise_err and path_to_toolchain is not None:
            raise FileNotFoundError(
                f"aarch64-none-elf toolchain binaries not found at: {path_to_toolchain}"
            )

    def with_test_files(self, test_files: Optional[List[Path]]) -> RunnerConfig:
        if test_files is None:
            test_files = []

        self.test_files = test_files
        assert all(
            file.match("*.s") for file in test_files
        ), f"test files must be .s files but found {' '.join(str(file) for file in test_files)}"
        return self

    def with_id(self, id: int) -> RunnerConfig:
        self.id = id
        return self

    def with_verbose(self, verbose: bool = True) -> RunnerConfig:
        self.verbose = verbose
        return self

    def with_assembler_only(self, assembler_only: bool = True) -> RunnerConfig:
        self.assembler_only = assembler_only
        return self

    def with_emulator_only(self, emulator_only: bool = True) -> RunnerConfig:
        self.emulator_only = emulator_only
        return self

    def with_expected_only(self, expected_only: bool = True) -> RunnerConfig:
        self.expected_only = expected_only
        return self

    def with_actual_only(self, actual_only: bool = True) -> RunnerConfig:
        self.actual_only = actual_only
        return self

    @staticmethod
    def _prep_path_like(
        path_like: Optional[Path | str],
        prep_dir: bool = False,
        prep_parent: bool = False,
    ) -> Path:
        if isinstance(path_like, str):
            path_like = Path(path_like)
        if isinstance(path_like, Path) and not path_like.exists():
            if prep_dir:
                path_like.mkdir(parents=True, exist_ok=True)
            elif prep_parent:
                path_like.parent.mkdir(parents=True, exist_ok=True)
        return path_like  # type: ignore

    def with_expdir(self, expdir: Optional[Path | str]) -> RunnerConfig:
        self.expdir = self._prep_path_like(expdir, prep_dir=True)
        return self

    def with_actdir(self, actdir: Optional[Path | str]) -> RunnerConfig:
        self.actdir = self._prep_path_like(actdir, prep_dir=True)
        return self

    def with_testdir(self, testdir: Optional[Path | str]) -> RunnerConfig:
        self.testdir = self._prep_path_like(testdir, prep_dir=True)
        return self

    def with_reference_toolchain_prefix(self, prefix: str) -> RunnerConfig:
        self.toolchain_prefix = prefix
        self.do_listings = True
        return self

    def with_assembler_under_test(self, path: Optional[Path | str]) -> RunnerConfig:
        self.assembler = self._prep_path_like(path)
        make_executable(self.assembler)
        return self

    def with_emulator_under_test(self, path: Optional[Path | str]) -> RunnerConfig:
        self.emulator = self._prep_path_like(path)
        make_executable(self.emulator)
        return self

    def with_logfile(self, logfile: Optional[Path | str]) -> RunnerConfig:
        self.logfile = self._prep_path_like(logfile, prep_parent=True)
        return self

    def _assert_is_configured(self):
        assert self.emulator is not None, "emulator has not been initialised"
        assert self.assembler is not None, "assembler has not been initialised"
        assert (
            self.expdir is not None
        ), "expected result directory has not been initialised"
        assert (
            self.actdir is not None
        ), "actual output directory has not been initialised"

    def validate(self) -> Result[None, str]:
        self._assert_is_configured()
        if not self.expected_only:
            if not self.emulator_only and not self.assembler.exists():
                return Err(f"assembler {self.assembler} cannot be found")
            if not self.assembler_only and not self.emulator.exists():
                return Err(f"emulator {self.emulator} cannot be found")
        return Ok(None)

    def copy(self, include_test_files: bool = False) -> RunnerConfig:
        return RunnerConfig(
            actdir=self.actdir,
            expdir=self.expdir,
            testdir=self.testdir,
            testfiles=self.test_files if include_test_files else None,
            assembler=self.assembler,
            emulator=self.emulator,
            logfile=self.logfile,
            verbose=self.verbose,
            assembler_only=self.assembler_only,
            emulator_only=self.emulator_only,
            expected_only=self.expected_only,
            actual_only=self.actual_only,
            do_listings=self.do_listings,
            process_wait_time=self.process_wait_time,
            is_run_all=self.is_run_all,
            is_multi_threaded=self.is_multi_threaded,
        )
