
import typing as _typing
import typing_extensions as _typing_extensions

T = _typing.TypeVar("T")
U = _typing.TypeVar("U")
V = _typing.TypeVar("V")
Ts = _typing_extensions.TypeVarTuple("Ts")

P = _typing.ParamSpec("P")


R = _typing.TypeVar("R")


T_co = _typing.TypeVar("T_co", covariant=True)
T_cn = _typing.TypeVar("T_cn", contravariant=True)
U_co = _typing.TypeVar("U_co", covariant=True)
U_cn = _typing.TypeVar("U_cn", contravariant=True)
R_co = _typing.TypeVar("R_co", covariant=True)
R_cn = _typing.TypeVar("R_cn", contravariant=True)



