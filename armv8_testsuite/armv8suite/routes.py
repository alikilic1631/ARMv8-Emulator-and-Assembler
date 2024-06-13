import json
from pathlib import Path
from typing import Any, Dict, Optional
import shutil
import subprocess
import os

CONFIG = Path("./config.json")

TEST_CASES_DIR = './test/test_cases/'
TEST_CASES_DIR_PATH = Path(TEST_CASES_DIR)

TEST_EXPECTED_DIR = './test/expected_results/'
TEST_ACTUAL_DIR = './test/actual_results/'
OUT_JSON_DIR = './test/actual_results'
OUT_ASSEMBLE_ALL = f'{OUT_JSON_DIR}/assembler_all.json'
OUT_EMULATE_ALL = f'{OUT_JSON_DIR}/emulator_all.json'
OUT_ALL = f'{OUT_JSON_DIR}/results.json'
ASSEMBLER_PATH = './solution/assemble'
EMULATOR_PATH = './solution/emulate'


OS_EXEC_FMT_ERRNO = 8


def ensure_path(path: Path, name: str = "file"):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found at {path}")
    
def ensure_executable(path: Path, name: str = "file"):
    ensure_path(path, name)
    error = PermissionError(f"{name} is not executable at {path}.\n  Try running `chmod +x {path}` to make it executable.")

    # Check if the file exists
    if not os.access(path, os.X_OK):
        raise error
    
    # Check if the file is executable
    try:
        subprocess.Popen([f"./{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        if e.errno == OS_EXEC_FMT_ERRNO:
            raise error
    except Exception as e:
        return


def parse_config(js: Path, ignore_assembler: bool, ignore_emulator: bool) -> Dict[str, str]:
    res = {}
    if not js.exists():
        return res
    
    with open(js, "r") as f:
        try:
            d: Dict[str, Any] = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"JSON config is invalid: {js}")

    if "paths" in d:
        paths = d["paths"]
        if not ignore_assembler and "assembler" in paths:
            res["assembler"] = paths["assembler"]
            ensure_executable(Path(res["assembler"]), "assembler")
        if not ignore_emulator and "emulator" in paths:
            res["emulator"] = paths["emulator"]
            ensure_executable(Path(res["emulator"]), "emulator")
            
    return res



STANDARD_ARGS = [
    "--expdir", TEST_EXPECTED_DIR, 
    "--actdir", TEST_ACTUAL_DIR, 
    "--testdir", TEST_CASES_DIR,
    "--outdir", TEST_ACTUAL_DIR,
    "-a", ASSEMBLER_PATH,
    "-e", EMULATOR_PATH,
    ]
