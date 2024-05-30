"""
All routes are relative to`armv8server`
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from typing_extensions import Self
from armv8suite.data.result import TestType

from armv8suite.utils.decorators import no_instances

# Re-export these for convenience
# pylint: disable=unused-import
from armv8server import TEMPLATE_FOLDER, STATIC_FOLDER

@dataclass(slots=True)
class Param:
    """ A url parameter key and its type 
    
    Can be called to create a new Param with the same key with a value
    """
    key: str
    type_: type
    value: Optional[str] = None
    
    def __str__(self) -> str:
        if self.value is None:
            return self.key
        return f"{self.key}={self.value}"
    
    def __call__(self, value: Optional[str] = None) -> Param:
        """ Create a new Param with the same key and type but a different value """
        return Param(self.key, self.type_, value)


@no_instances(recursive=True)
class Params:
    """ All url parameter keys. 
    
    All are callable, returning a Param with the same key and a value.
    """
    class TestSingle:
        test_file = Param("test_file", Path)

    class TestFind:
        fname = Param("fname", Path)


@dataclass
class HTTPRoute:
    """ A route (url-path) and its parameter keys """
    route: str
    extras: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._update_extras()

    def _update_extras(self) -> None:
        for k, v in self.extras.items():
            setattr(self, k, v)

    def just_route(self) -> HTTPRoute:
        return HTTPRoute(self.route)

    def __str__(self) -> str:
        param_list = self.params()
        if not param_list:
            return self.route
        
        params = "&".join(str(p) for p in param_list if p.value is not None)
        return f"{self.route}?{params}"

    def params(self) -> List[Param]:
        return [p for p in self.__dict__.values() if isinstance(p, Param)]

    def copy(self) -> HTTPRoute:
        return HTTPRoute(self.route, self.extras.copy())

    @classmethod
    def join(cls, route1: HTTPRoute | Tuple[str, HTTPRoute], *routes: HTTPRoute | Tuple[str, HTTPRoute]) -> Self:
        default_sep = "/"
        route_ls = []
        extras = []
        for route in (route1, *routes):
            if isinstance(route, tuple):
                sep, route = route
            else:
                sep = default_sep
            route_ls.append(f"{sep}{route.route}")
            extras.append(route.extras.copy())

        res = cls.__new__(cls ,"".join(route_ls), extras = {k: v for d in extras for k, v in d.items()})
        return res
        
    def __div__(self, other: HTTPRoute | Tuple[str, HTTPRoute]) -> Self:
        return self.join(other)
        
        

class SingleTestRoute(HTTPRoute):
    """ A route (url-path) and its parameter keys for a single test """    
    def __init__(self, route: str, test_file_name: Optional[str] = None, extras: Optional[Dict] = None):
        extras = {} if extras is None else extras
        super().__init__(route, extras)
        self.test_file = Params.TestSingle.test_file(test_file_name)

    def __call__(self, test_file_name: Optional[str] = None) -> SingleTestRoute:
        return SingleTestRoute(self.route, test_file_name, self.extras)

@no_instances(recursive=True)
class WebRouteMethods:
    """ Methods to create routes """
    @staticmethod
    def any_all(portion: str):
        return HTTPRoute(f"/{portion}")
    
    @staticmethod
    def any_single(portion: str | HTTPRoute, x: Optional[str] = None):
        if isinstance(portion, str):
            route = portion
        else:
            route = portion.route
        res = SingleTestRoute(f"/{route}/single", x)
        return res


@no_instances(recursive=True)
class WebRoutes(WebRouteMethods):
    """ All routes (url-paths) for the server """
    homepage = HTTPRoute("/")

    assemble_all = WebRouteMethods.any_all(TestType.ASSEMBLER.key_name())
    emulate_all = WebRouteMethods.any_all(TestType.EMULATOR.key_name())

    assemble_single = WebRouteMethods.any_single(assemble_all)
    emulate_single = WebRouteMethods.any_single(emulate_all)


    find_test = HTTPRoute(f"/<{Params.TestFind.fname.key}>/find")
    find_test_assemble = HTTPRoute(f"{assemble_all.route}/find", extras={"test_type": TestType.ASSEMBLER})
    find_test_emulate = HTTPRoute(f"{emulate_all.route}/find", extras={"test_type": TestType.EMULATOR})
