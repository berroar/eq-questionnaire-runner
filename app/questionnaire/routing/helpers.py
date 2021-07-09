from functools import wraps
from typing import Any, Callable


def _casefold(value):
    try:
        return (
            [_casefold(v) for v in value]
            if isinstance(value, (list, tuple))
            else value.casefold()
        )
    except AttributeError:
        return value


def casefold(func: Callable):
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        casefolded_args = [_casefold(arg) for arg in args]
        casefolded_kwargs = {k: _casefold(v) for k, v in kwargs.items()}
        return func(*casefolded_args, **casefolded_kwargs)

    return wrapper
