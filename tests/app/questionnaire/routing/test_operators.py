from datetime import datetime

import pytest

from app.questionnaire.routing.operators import Operator, OperatorNames

now = datetime.utcnow()

test_data_equals_operation_numeric_and_date_matching_values = [
    [(0.5, 0.5), True],
    [(1.0, 1), True],
    [(3, 3), True],
    [(now, now), True],
]

test_data_equals_operation_numeric_and_date = [
    *test_data_equals_operation_numeric_and_date_matching_values,
    [(0.5, 0.7), False],
    [(1.0, 3), False],
    [(3, 7), False],
    [(now, datetime.utcnow()), False],
]

equals_operations = [
    *test_data_equals_operation_numeric_and_date,
    [("Yes", "Yes"), True],
    [("CaseInsensitive", "caseInsensitive"), True],
    [(None, None), True],
    [(True, True), True],
    [("Yes", "No"), False],
    [(None, 1), False],
    [(True, False), False],
]

test_data_greater_than_less_than_operations = [
    [(0.7, 0.5), True],
    [(2, 1.0), True],
    [(7, 3), True],
    [(datetime.utcnow(), now), True],
    [(0.5, 0.7), False],
    [(1.0, 2), False],
    [(3, 7), False],
    [(now, datetime.utcnow()), False],
]


@pytest.mark.parametrize(
    "operands, result",
    equals_operations,
)
def test_operation_equal(operands, result):
    operator = Operator(OperatorNames.EQUAL)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    equals_operations,
)
def test_operation_not_equal(operands, result):
    operator = Operator(OperatorNames.NOT_EQUAL)
    assert operator.evaluate(operands) is not result


@pytest.mark.parametrize(
    "operands, result",
    test_data_greater_than_less_than_operations,
)
def test_operation_greater_than(operands, result):
    operator = Operator(OperatorNames.GREATER_THAN)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        *test_data_greater_than_less_than_operations,
        *test_data_equals_operation_numeric_and_date_matching_values,
    ],
)
def test_operation_greater_than_or_equal(operands, result):
    operator = Operator(OperatorNames.GREATER_THAN_OR_EQUAL)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    test_data_greater_than_less_than_operations,
)
def test_operation_less_than(operands, result):
    operator = Operator(OperatorNames.LESS_THAN)
    assert operator.evaluate(operands) is not result


@pytest.mark.parametrize(
    "operands, result", test_data_greater_than_less_than_operations
)
def test_operation_less_than_or_equal_operands_equal(operands, result):
    operator = Operator(OperatorNames.LESS_THAN_OR_EQUAL)
    assert operator.evaluate(operands) is not result


@pytest.mark.parametrize(
    "operands, result",
    test_data_equals_operation_numeric_and_date_matching_values,
)
def test_operation_less_than_or_equal_operands_not_equal(operands, result):
    operator = Operator(OperatorNames.LESS_THAN_OR_EQUAL)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize("operand, result", [[False, True], [True, False]])
def test_operation_not(operand, result):
    operator = Operator(OperatorNames.NOT)
    assert operator.evaluate([operand]) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        [(True, True), True],
        [(True, True, True, True), True],
        [(True, False), False],
        [(False, True, True, True), False],
    ],
)
def test_operation_and(operands, result):
    operator = Operator(OperatorNames.AND)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        [(True, True), True],
        [(True, True, True, True), True],
        [(True, False), True],
        [(False, False, False, True), True],
    ],
)
def test_operation_or(operands, result):
    operator = Operator(OperatorNames.OR)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        [("Yes", ["Yes", "No"]), True],
        [("CaseInsensitive", ["caseInsensitive", "Other"]), True],
        [(0.5, [0.5, 1]), True],
        [(1, [1, 3]), True],
        [(None, [None, 1]), True],
        [("Yes", ["Nope", "No"]), False],
        [(0.5, [0.3, 1]), False],
        [(1, [1.5, 3]), False],
        [(None, ["Yes", "No"]), False],
    ],
)
def test_operation_in(operands, result):
    operator = Operator(OperatorNames.IN)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        [(["Yes", "No"], ["Yes", "No", "Okay"]), True],
        [(["CaseInsensitive", "other"], ["caseInsensitive", "Other"]), True],
        [([0.5], [0.5, 1]), True],
        [([1, 3, 5], [5, 3, 1, 7]), True],
        [([None, 1], [1, None, 3]), True],
        [(["Yes", "No"], ["Nope", "No"]), False],
        [([0.5, 1], [0.3, 1]), False],
        [([1, 1.5, 3, 5], [1.5, 3, 5, 7]), False],
        [([None, "No"], ["Yes", "No"]), False],
    ],
)
def test_operation_all_in(operands, result):
    operator = Operator(OperatorNames.ALL_IN)
    assert operator.evaluate(operands) is result


@pytest.mark.parametrize(
    "operands, result",
    [
        [(["Yes", "No"], ["Yes", "No", "Okay"]), True],
        [(["CaseInsensitive", "other"], ["No", "Other"]), True],
        [([0.5], [0.5, 1]), True],
        [([0, 3, 10], [5, 3, 1, 7]), True],
        [([None, 10], [1, None, 3]), True],
        [(["Yes", "Okay"], ["Nope", "No"]), False],
        [([0.5, 3], [0.3, 1]), False],
        [([1, 10, 100, 500], [1.5, 3, 5, 7]), False],
        [([None, 0], ["Yes", "No"]), False],
    ],
)
def test_operation_all_in(operands, result):
    operator = Operator(OperatorNames.ANY_IN)
    assert operator.evaluate(operands) is result
