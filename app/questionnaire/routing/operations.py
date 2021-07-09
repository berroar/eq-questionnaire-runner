from datetime import datetime
from typing import Iterable, Sequence, Union

from app.questionnaire.routing.helpers import casefold

comparison_greater_than_types = Union[int, float, datetime]
comparison_less_than_types = comparison_greater_than_types
comparison_equal_types = Union[bool, str, int, float, None, datetime]


@casefold
def evaluate_equal(lhs: comparison_equal_types, rhs: comparison_equal_types) -> bool:
    return lhs == rhs


@casefold
def evaluate_not_equal(
    lhs: comparison_equal_types, rhs: comparison_equal_types
) -> bool:
    return lhs != rhs


def evaluate_greater_than(
    lhs: comparison_greater_than_types, rhs: comparison_greater_than_types
) -> bool:
    return lhs > rhs  # type: ignore


def evaluate_greater_than_or_equal(
    lhs: comparison_greater_than_types, rhs: comparison_greater_than_types
) -> bool:
    return lhs >= rhs  # type: ignore


def evaluate_less_than(
    lhs: comparison_less_than_types, rhs: comparison_less_than_types
) -> bool:
    return lhs < rhs  # type: ignore


def evaluate_less_than_or_equal(
    lhs: comparison_less_than_types, rhs: comparison_less_than_types
) -> bool:
    return lhs <= rhs  # type: ignore


def evaluate_not(value: bool) -> bool:
    return not value


def evaluate_and(values: Iterable[bool]) -> bool:
    return all(iter(values))


def evaluate_or(values: Iterable[bool]) -> bool:
    return any(iter(values))


@casefold
def evaluate_in(lhs: Union[str, int, float, None], rhs: Sequence) -> bool:
    return lhs in rhs


@casefold
def evaluate_all_in(lhs: Sequence, rhs: Sequence) -> bool:
    return all(x in rhs for x in lhs)


@casefold
def evaluate_any_in(lhs: Sequence, rhs: Sequence) -> bool:
    return any(x in rhs for x in lhs)


def resolve_date_from_string(date_string: str, offset: dict[str, int]):
    pass
