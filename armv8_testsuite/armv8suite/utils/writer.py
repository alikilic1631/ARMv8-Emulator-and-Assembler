from abc import ABC, abstractmethod
from io import TextIOWrapper
from typing import Generic, Iterable, List, Optional, TypeVar

T = TypeVar('T')

class Writer(ABC, Generic[T]):
    """ Approximation of the Writer monad.
    Abstractly represents a write-only output.
    """
    @abstractmethod
    def tell(self, t: T) -> None:
        pass

    def tells(self, ts: Iterable[T]) -> None:
        [self.tell(t) for t in ts]
        
    def tell_if(self, cond: bool, t: T) -> None:
        if cond: self.tell(t)

class ListWriter(Writer[T]):
    """ ListWriter Wrapper """
    def __init__(self, ls: Optional[List[T]] = None):
        self._list = [] if ls is None else ls
    
    def tell(self, t: T) -> None:
        self._list.append(t)
        
    def to_list(self) -> List[T]:
        return self._list
    
class StringWriter(ListWriter[T]):
    def to_string(self, join_with: str = "") -> str:
        return join_with.join([str(x) for x in self._list])
    
    def __str__(self) -> str:
        return self.to_string()
    
class IOTextWriter(Writer[T]):
    def __init__(self, out: TextIOWrapper) -> None:
        super().__init__()
        self._out = out
    
    def tell(self, t: T) -> None:
        self._out.write(str(t) + '\n')
        
    def tells(self, ts: Iterable[T]) -> None:
        for t in ts:
            self.tell(t)

    def close(self) -> None:
        self._out.close()