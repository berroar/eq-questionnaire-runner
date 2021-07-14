import pytest

from app.data_models import AnswerStore, ListStore
from app.questionnaire import Location, QuestionnaireSchema
from app.questionnaire.routing.when_rule_evaluator import WhenRuleEvaluator

answer_source = {"source": "answers", "identifier": "some-answer"}
answer_source_list_item_selector_location = {
    **answer_source,
    "list_item_selector": {"source": "location", "id": "list_item_id"},
}
answer_source_list_item_selector_list = {
    **answer_source,
    "list_item_selector": {"source": "list", "id": "some-list", "id_selector": "first"},
}

metadata_source = {"source": "metadata", "identifier": "some-metadata"}

list_source = {"source": "list", "identifier": "some-list"}
list_source_id_selector_first = {**list_source, "id_selector": "first"}
list_source_id_selector_same_name_items = {
    **list_source,
    "id_selector": "same_name_items",
}

location_source = {"source": "location", "identifier": "list_item_id"}


def get_list_items(num: int):
    return [f"item-{i}" for i in range(1, num + 1)]


def get_test_data_for_source(source: dict):
    return [
        ("==", source, "Maybe", "Maybe", True),
        ("==", "Maybe", source, "Maybe", True),
        ("!=", source, "Maybe", "Yes", True),
        ("!=", "Maybe", source, "Yes", True),
        (">", 2, source, 1, True),
        (">", source, 1, 2, True),
        (">=", 1, source, 1, True),
        (">=", source, 1, 1, True),
        ("<", 1, source, 2, True),
        ("<", source, 2, 1, True),
        ("<=", 1, source, 1, True),
        ("<=", source, 1, 1, True),
        ("in", source, ["Maybe"], "Maybe", True),
        ("in", "Maybe", source, ["Maybe"], True),
        ("any-in", source, ["Maybe"], ["Yes", "Maybe"], True),
        ("any-in", ["Maybe"], source, ["Yes", "Maybe"], True),
        ("all-in", source, ["Maybe"], ["Maybe"], True),
        ("all-in", ["Maybe"], source, ["Maybe"], True),
        # Test inverse
        ("==", source, "Maybe", "Yes", False),
        ("==", "Maybe", source, "Yes", False),
        ("!=", source, "Maybe", "Maybe", False),
        ("!=", "Maybe", source, "Maybe", False),
        (">", 1, source, 2, False),
        (">", source, 2, 1, False),
        (">=", 1, source, 2, False),
        (">=", source, 1, 0, False),
        ("<", 2, source, 1, False),
        ("<", source, 1, 2, False),
        ("<=", 1, source, 0, False),
        ("<=", source, 1, 2, False),
        ("in", source, ["Maybe"], "Yes", False),
        ("in", "Maybe", source, ["Yes"], False),
        ("any-in", source, ["Maybe"], ["Yes", "No"], False),
        ("any-in", ["Maybe"], source, ["Yes", "No"], False),
        ("all-in", source, ["Maybe"], ["Yes", "No"], False),
        ("all-in", ["Maybe"], source, ["Yes"], False),
    ]


def get_test_data_with_string_values_for_source(source: dict):
    return [
        ("==", source, "item-1", True),
        ("==", "item-1", source, True),
        ("!=", source, "item-2", True),
        ("!=", "item-2", source, True),
        ("in", source, ["item-1"], True),
        # Test inverse
        ("==", source, "item-2", False),
        ("==", "item-2", source, False),
        ("!=", source, "item-1", False),
        ("!=", "item-1", source, False),
        ("in", source, ["item-2"], False),
    ]


def get_when_rule_evaluator(
    rule,
    schema=QuestionnaireSchema({}),
    metadata=None,
    answer_store=AnswerStore(),
    list_store=ListStore(),
    location=Location(section_id="test-section", block_id="test-block"),
):
    return WhenRuleEvaluator(
        rule=rule,
        schema=schema,
        metadata=metadata or {},
        answer_store=answer_store,
        list_store=list_store,
        location=location,
    )


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, answer_value, result",
    get_test_data_for_source(answer_source),
)
def test_answer_source(operator, first_argument, second_argument, answer_value, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        answer_store=AnswerStore([{"answer_id": "some-answer", "value": answer_value}]),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, answer_value, result",
    get_test_data_for_source(answer_source_list_item_selector_location),
)
def test_answer_source_with_list_item_selector_location(
    operator, first_argument, second_argument, answer_value, result
):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        answer_store=AnswerStore(
            [
                {
                    "answer_id": "some-answer",
                    "list_item_id": "item-1",
                    "value": answer_value,
                }
            ]
        ),
        location=Location(
            section_id="some-section", block_id="some-block", list_item_id="item-1"
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, answer_value, result",
    get_test_data_for_source(answer_source_list_item_selector_list),
)
def test_answer_source_with_list_item_selector_list(
    operator, first_argument, second_argument, answer_value, result
):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        answer_store=AnswerStore(
            [
                {
                    "answer_id": "some-answer",
                    "list_item_id": "item-1",
                    "value": answer_value,
                }
            ]
        ),
        list_store=ListStore([{"name": "some-list", "items": get_list_items(3)}]),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, metadata_value, result",
    get_test_data_for_source(metadata_source),
)
def test_metadata_source(
    operator, first_argument, second_argument, metadata_value, result
):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        metadata={"some-metadata": metadata_value},
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, list_count, result",
    [
        ("==", list_source, 1, 1, True),
        ("==", 1, list_source, 1, True),
        ("!=", list_source, 1, 2, True),
        ("!=", 1, list_source, 2, True),
        (">", 2, list_source, 1, True),
        (">", list_source, 1, 2, True),
        (">=", 1, list_source, 1, True),
        (">=", list_source, 1, 1, True),
        ("<", 1, list_source, 2, True),
        ("<", list_source, 2, 1, True),
        ("<=", 1, list_source, 1, True),
        ("<=", list_source, 1, 1, True),
        # Test inverse
        ("==", list_source, 1, 2, False),
        ("==", 1, list_source, 2, False),
        ("!=", list_source, 1, 1, False),
        ("!=", 1, list_source, 1, False),
        (">", 1, list_source, 2, False),
        (">", list_source, 2, 1, False),
        (">=", 1, list_source, 2, False),
        (">=", list_source, 1, 0, False),
        ("<", 2, list_source, 1, False),
        ("<", list_source, 1, 2, False),
        ("<=", 1, list_source, 0, False),
        ("<=", list_source, 1, 2, False),
    ],
)
def test_list_source(operator, first_argument, second_argument, list_count, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        list_store=ListStore(
            [{"name": "some-list", "items": get_list_items(list_count)}]
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, result",
    get_test_data_with_string_values_for_source(list_source_id_selector_first),
)
def test_list_source_with_id_selector_first(
    operator, first_argument, second_argument, result
):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        list_store=ListStore([{"name": "some-list", "items": get_list_items(1)}]),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, result",
    [
        ("in", "item-2", list_source_id_selector_same_name_items, True),
        ("any-in", list_source_id_selector_same_name_items, ["item-3", "item-5"], True),
        ("any-in", ["item-1"], list_source_id_selector_same_name_items, True),
        (
            "all-in",
            list_source_id_selector_same_name_items,
            ["item-1", "item-2", "item-3"],
            True,
        ),
        (
            "all-in",
            ["item-1", "item-2", "item-3"],
            list_source_id_selector_same_name_items,
            True,
        ),
        # Test inverse
        ("in", "item-5", list_source_id_selector_same_name_items, False),
        (
            "any-in",
            list_source_id_selector_same_name_items,
            ["item-4", "item-5"],
            False,
        ),
        ("any-in", ["item-5"], list_source_id_selector_same_name_items, False),
        (
            "all-in",
            list_source_id_selector_same_name_items,
            ["item-1", "item-2", "item-5"],
            False,
        ),
        (
            "all-in",
            ["item-1", "item-2", "item-5"],
            list_source_id_selector_same_name_items,
            False,
        ),
    ],
)
def test_list_source_with_id_selector_same_name_items(
    operator, first_argument, second_argument, result
):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        list_store=ListStore(
            [
                {
                    "name": "some-list",
                    "items": get_list_items(5),
                    "same_name_items": get_list_items(3),
                }
            ]
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, result",
    get_test_data_with_string_values_for_source(location_source),
)
def test_location_source(operator, first_argument, second_argument, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        location=Location(
            section_id="some-section", block_id="some-block", list_item_id="item-1"
        ),
    )

    assert when_rule_evaluator.evaluate() is result
