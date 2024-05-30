import functools
from typing import Callable, Generic

from armv8suite.utils.typevars import P, T


def no_instances(cls=None, /,*, recursive: bool = False) -> Callable:
    """ Decorator to prevent instantiation of a class.
    
    Prevents a class from being instantiated by modifying its `__init__` method.
    `__init__` raises an exception if invoked.
    This is useful for classes that are only used as namespaces.
    
    Args:
    - `cls`: The class to decorate.
    - `recursive`: When true, also decorate classes defined within `cls`.

    Returns:
        The class with the modified `__init__` method.
    """
    def _wrap(cls: type):
        
        def raise_exception(self, *args, **kwargs):
            raise NotImplementedError("Cannot instantiate this class")
        
        cls.__init__ = raise_exception
        if recursive:
            for _, attr in cls.__dict__.items():
                if isinstance(attr, type):
                    no_instances(attr, recursive=recursive)
        return cls
    
    if cls is None:
        # called with parens
        return _wrap
    
    # called without parens
    return _wrap(cls)


class extend_error(Generic[P, T]):
    """ Decorator to extend the error message of an exception. """

    class Decorator:
        """ Decorator to extend the error message of an exception. """
        def __init__(self, func: Callable[P, T]) -> None:
            functools.update_wrapper(self, func)
            self.func = func

        def __call__(self, msg: str, err_tp = Exception, delim: str = "\n") -> Callable[P, T]:
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                try:
                    return self.func(*args, **kwargs)
                except err_tp as inner_err:
                    inner_err.args = (f"{inner_err.args[0]}{delim}{msg}", *inner_err.args[1:])
                    raise inner_err from inner_err

            return wrapper

    def __init__(self, msg: str, err_tp: type = Exception, delim: str = "\n") -> None:
        """ Decorator to extend the error message of an exception.

        Args:
            - `msg` (`str`): The message to append to the error.
            - `err_tp` (`type`, optional): The type of exception to catch. Defaults to Exception.
            - `delim` (`str`, optional): _description_. Defaults to "\n".
        """
        self.msg = msg
        self.err_tp = err_tp
        self.delim = delim

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        return self.Decorator(func)(self.msg, self.err_tp, self.delim)
