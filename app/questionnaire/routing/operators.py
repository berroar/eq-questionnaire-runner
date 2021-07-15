from typing import Iterable

from app.questionnaire.routing.operations import (
    comparison_types,
    evaluate_all_in,
    evaluate_and,
    evaluate_any_in,
    evaluate_equal,
    evaluate_greater_than,
    evaluate_greater_than_or_equal,
    evaluate_in,
    evaluate_less_than,
    evaluate_less_than_or_equal,
    evaluate_not,
    evaluate_not_equal,
    evaluate_or,
    resolve_datetime_from_string,
)


class OperatorNames:
    NOT = "not"
    AND = "and"
    OR = "or"
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    IN = "in"
    ALL_IN = "all-in"
    ANY_IN = "any-in"
    DATE = "date"


OPERATIONS = {
    OperatorNames.NOT: evaluate_not,
    OperatorNames.AND: evaluate_and,
    OperatorNames.OR: evaluate_or,
    OperatorNames.EQUAL: evaluate_equal,
    OperatorNames.NOT_EQUAL: evaluate_not_equal,
    OperatorNames.GREATER_THAN: evaluate_greater_than,
    OperatorNames.LESS_THAN: evaluate_less_than,
    OperatorNames.GREATER_THAN_OR_EQUAL: evaluate_greater_than_or_equal,
    OperatorNames.LESS_THAN_OR_EQUAL: evaluate_less_than_or_equal,
    OperatorNames.IN: evaluate_in,
    OperatorNames.ALL_IN: evaluate_all_in,
    OperatorNames.ANY_IN: evaluate_any_in,
    OperatorNames.DATE: resolve_datetime_from_string,
}


class Operator:
    def __init__(self, name: str) -> None:
        self.name = name
        self._operation = OPERATIONS[self.name]
        self._short_circuit = self.name in [OperatorNames.AND, OperatorNames.OR]

    def evaluate(self, operands: Iterable) -> comparison_types:
        value: comparison_types = (
            self._operation(operands)
            if self._short_circuit
            else self._operation(*operands)
        )
        return value
