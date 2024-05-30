from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import stat
import tempfile
from typing import IO, Any, Callable, Generic, Iterator, Optional, ParamSpec, Protocol, Tuple, TypeVar
from typing_extensions import Self

from result import Ok, Result

from .typevars import *



def map_optional(func: Callable[[T], U], arg: Optional[T]) -> Optional[U]:
    return None if arg is None else func(arg)

def map_optionals(func: Callable[..., U], *args, **kwargs) -> Optional[U]:
    if any(arg is None for arg in args) or any(arg is None for arg in kwargs.values()):
        return None
    return func(*args, **kwargs)



def result_tuple(
    *results: Result[Any, U]
) -> Result[Tuple, U]:
    """Combines multiple results into a single result"""
    for result in results:
        if result.is_err():
            return result # type: ignore
    return Ok(tuple(result.unwrap() for result in results))



def wrap_open(path: Optional[Path], mode: str, *args, **kw_args) -> IO[Any]:
    if path is None:
        return tempfile.TemporaryFile(mode=mode, **kw_args)
    return open(path, mode, *args, **kw_args)


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class CallableArgsKWArgs(Protocol, Generic[T_cn, U_cn, R_co]):
    def __call__(self, *args: T_cn, **kwargs: U_cn) -> R_co:
        ...
        
def is_defined(obj: Any) -> bool:
    try: 
        obj
        return True
    except NameError:
        return False
    
class SizedIterable(Protocol[T_co]):
    def __iter__(self) -> Iterator[T_co]:
        ...
        
    def __len__(self) -> int:
        ...



