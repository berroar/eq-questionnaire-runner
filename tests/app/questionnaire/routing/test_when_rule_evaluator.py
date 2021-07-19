from datetime import datetime

import pytest
from freezegun import freeze_time

from app.data_models import AnswerStore, ListStore
from app.questionnaire import Location, QuestionnaireSchema
from app.questionnaire.routing.operator import Operator
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

current_location_source = {"source": "location", "identifier": "list_item_id"}

now = datetime.utcnow()
formatted_now = now.strftime("%Y-%m-%d")


def get_list_items(num: int):
    return [f"item-{i}" for i in range(1, num + 1)]


def get_test_data_for_source(source: dict):
    """
    operator, first_argument, second_argument, resolved_value, result
    """
    return [
        (Operator.EQUAL, source, "Maybe", "Maybe", True),
        (Operator.EQUAL, "Maybe", source, "Maybe", True),
        (Operator.NOT_EQUAL, source, "Maybe", "Yes", True),
        (Operator.NOT_EQUAL, "Maybe", source, "Yes", True),
        (Operator.GREATER_THAN, 2, source, 1, True),
        (Operator.GREATER_THAN, source, 1, 2, True),
        (Operator.GREATER_THAN_OR_EQUAL, 1, source, 1, True),
        (Operator.GREATER_THAN_OR_EQUAL, source, 1, 1, True),
        (Operator.LESS_THAN, 1, source, 2, True),
        (Operator.LESS_THAN, source, 2, 1, True),
        (Operator.LESS_THAN_OR_EQUAL, 1, source, 1, True),
        (Operator.LESS_THAN_OR_EQUAL, source, 1, 1, True),
        (Operator.IN, source, ["Maybe"], "Maybe", True),
        (Operator.IN, "Maybe", source, ["Maybe"], True),
        (Operator.ANY_IN, source, ["Maybe"], ["Yes", "Maybe"], True),
        (Operator.ANY_IN, ["Maybe"], source, ["Yes", "Maybe"], True),
        (Operator.ALL_IN, source, ["Maybe"], ["Maybe"], True),
        (Operator.ALL_IN, ["Maybe"], source, ["Maybe"], True),
        # Test inverse
        (Operator.EQUAL, source, "Maybe", "Yes", False),
        (Operator.EQUAL, "Maybe", source, "Yes", False),
        (Operator.NOT_EQUAL, source, "Maybe", "Maybe", False),
        (Operator.NOT_EQUAL, "Maybe", source, "Maybe", False),
        (Operator.GREATER_THAN, 1, source, 2, False),
        (Operator.GREATER_THAN, source, 2, 1, False),
        (Operator.GREATER_THAN_OR_EQUAL, 1, source, 2, False),
        (Operator.GREATER_THAN_OR_EQUAL, source, 1, 0, False),
        (Operator.LESS_THAN, 2, source, 1, False),
        (Operator.LESS_THAN, source, 1, 2, False),
        (Operator.LESS_THAN_OR_EQUAL, 1, source, 0, False),
        (Operator.LESS_THAN_OR_EQUAL, source, 1, 2, False),
        (Operator.IN, source, ["Maybe"], "Yes", False),
        (Operator.IN, "Maybe", source, ["Yes"], False),
        (Operator.ANY_IN, source, ["Maybe"], ["Yes", "No"], False),
        (Operator.ANY_IN, ["Maybe"], source, ["Yes", "No"], False),
        (Operator.ALL_IN, source, ["Maybe"], ["Yes", "No"], False),
        (Operator.ALL_IN, ["Maybe"], source, ["Yes"], False),
    ]


def get_test_data_with_string_values_for_source(source: dict):
    return [
        (Operator.EQUAL, source, "item-1", True),
        (Operator.EQUAL, "item-1", source, True),
        (Operator.NOT_EQUAL, source, "item-2", True),
        (Operator.NOT_EQUAL, "item-2", source, True),
        (Operator.IN, source, ["item-1"], True),
        # Test inverse
        (Operator.EQUAL, source, "item-2", False),
        (Operator.EQUAL, "item-2", source, False),
        (Operator.NOT_EQUAL, source, "item-1", False),
        (Operator.NOT_EQUAL, "item-1", source, False),
        (Operator.IN, source, ["item-2"], False),
    ]


def get_test_data_for_date_value_for_source(source):
    return [
        (
            {
                Operator.EQUAL: [
                    {Operator.DATE: [source]},
                    {Operator.DATE: [formatted_now]},
                ]
            },
            True,
        ),
        (
            {
                Operator.NOT_EQUAL: [
                    {Operator.DATE: [source, {"days": -1}]},
                    {Operator.DATE: [formatted_now]},
                ]
            },
            True,
        ),
        (
            {
                Operator.LESS_THAN: [
                    {Operator.DATE: [source, {"days": -1}]},
                    {Operator.DATE: ["now"]},
                ]
            },
            True,
        ),
        (
            {
                Operator.LESS_THAN_OR_EQUAL: [
                    {Operator.DATE: [source, {"days": -1}]},
                    {Operator.DATE: ["now", {"days": -1}]},
                ]
            },
            True,
        ),
        (
            {
                Operator.GREATER_THAN: [
                    {Operator.DATE: [source]},
                    {Operator.DATE: ["now", {"months": -1}]},
                ]
            },
            True,
        ),
        (
            {
                Operator.GREATER_THAN_OR_EQUAL: [
                    {Operator.DATE: [source, {"months": -1}]},
                    {Operator.DATE: ["now", {"months": -1}]},
                ]
            },
            True,
        ),
        # Test inverse
        (
            {
                Operator.EQUAL: [
                    {Operator.DATE: [source, {"days": -1}]},
                    {Operator.DATE: [formatted_now]},
                ]
            },
            False,
        ),
        (
            {
                Operator.NOT_EQUAL: [
                    {Operator.DATE: [source]},
                    {Operator.DATE: [formatted_now]},
                ]
            },
            False,
        ),
        (
            {
                Operator.LESS_THAN: [
                    {Operator.DATE: [source, {"days": 1}]},
                    {Operator.DATE: ["now"]},
                ]
            },
            False,
        ),
        (
            {
                Operator.GREATER_THAN: [
                    {Operator.DATE: [source, {"months": -1}]},
                    {Operator.DATE: ["now"]},
                ]
            },
            False,
        ),
    ]


def get_when_rule_evaluator(
    rule,
    schema=QuestionnaireSchema({}),
    metadata=None,
    answer_store=AnswerStore(),
    list_store=ListStore(),
    location=Location(section_id="test-section", block_id="test-block"),
    routing_path_block_ids=None,
):
    return WhenRuleEvaluator(
        rule=rule,
        schema=schema,
        metadata=metadata or {},
        answer_store=answer_store,
        list_store=list_store,
        location=location,
        routing_path_block_ids=routing_path_block_ids,
    )


test_data_mixed_value_sources = (
    {Operator.EQUAL: [{"source": "answers", "identifier": "answer-1"}, "Yes, I do"]},
    {Operator.NOT_EQUAL: [{"source": "list", "identifier": "some-list"}, 0]},
    {
        Operator.GREATER_THAN_OR_EQUAL: [
            {
                "source": "answers",
                "identifier": "answer-2",
                "list_item_selector": {
                    "source": "location",
                    "id": "list_item_id",
                },
            },
            9,
        ]
    },
    {
        Operator.IN: [
            {"source": "metadata", "identifier": "region_code"},
            ["GB-ENG", "GB-WLS"],
        ]
    },
    {Operator.EQUAL: [list_source_id_selector_first, current_location_source]},
    {Operator.ANY_IN: [list_source_id_selector_same_name_items, ["item-1"]]},
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
        (Operator.EQUAL, list_source, 1, 1, True),
        (Operator.EQUAL, 1, list_source, 1, True),
        (Operator.NOT_EQUAL, list_source, 1, 2, True),
        (Operator.NOT_EQUAL, 1, list_source, 2, True),
        (Operator.GREATER_THAN, 2, list_source, 1, True),
        (Operator.GREATER_THAN, list_source, 1, 2, True),
        (Operator.GREATER_THAN_OR_EQUAL, 1, list_source, 1, True),
        (Operator.GREATER_THAN_OR_EQUAL, list_source, 1, 1, True),
        (Operator.LESS_THAN, 1, list_source, 2, True),
        (Operator.LESS_THAN, list_source, 2, 1, True),
        (Operator.LESS_THAN_OR_EQUAL, 1, list_source, 1, True),
        (Operator.LESS_THAN_OR_EQUAL, list_source, 1, 1, True),
        # Test inverse
        (Operator.EQUAL, list_source, 1, 2, False),
        (Operator.EQUAL, 1, list_source, 2, False),
        (Operator.NOT_EQUAL, list_source, 1, 1, False),
        (Operator.NOT_EQUAL, 1, list_source, 1, False),
        (Operator.GREATER_THAN, 1, list_source, 2, False),
        (Operator.GREATER_THAN, list_source, 2, 1, False),
        (Operator.GREATER_THAN_OR_EQUAL, 1, list_source, 2, False),
        (Operator.GREATER_THAN_OR_EQUAL, list_source, 1, 0, False),
        (Operator.LESS_THAN, 2, list_source, 1, False),
        (Operator.LESS_THAN, list_source, 1, 2, False),
        (Operator.LESS_THAN_OR_EQUAL, 1, list_source, 0, False),
        (Operator.LESS_THAN_OR_EQUAL, list_source, 1, 2, False),
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
        (Operator.IN, "item-2", list_source_id_selector_same_name_items, True),
        (
            Operator.ANY_IN,
            list_source_id_selector_same_name_items,
            ["item-3", "item-5"],
            True,
        ),
        (Operator.ANY_IN, ["item-1"], list_source_id_selector_same_name_items, True),
        (
            Operator.ALL_IN,
            list_source_id_selector_same_name_items,
            ["item-1", "item-2", "item-3"],
            True,
        ),
        (
            Operator.ALL_IN,
            ["item-1", "item-2", "item-3"],
            list_source_id_selector_same_name_items,
            True,
        ),
        # Test inverse
        (Operator.IN, "item-5", list_source_id_selector_same_name_items, False),
        (
            Operator.ANY_IN,
            list_source_id_selector_same_name_items,
            ["item-4", "item-5"],
            False,
        ),
        (Operator.ANY_IN, ["item-5"], list_source_id_selector_same_name_items, False),
        (
            Operator.ALL_IN,
            list_source_id_selector_same_name_items,
            ["item-1", "item-2", "item-5"],
            False,
        ),
        (
            Operator.ALL_IN,
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
    get_test_data_with_string_values_for_source(current_location_source),
)
def test_current_location_source(operator, first_argument, second_argument, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: [first_argument, second_argument]},
        location=Location(
            section_id="some-section", block_id="some-block", list_item_id="item-1"
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, operands, result",
    [
        (
            Operator.AND,
            [
                *test_data_mixed_value_sources,
                {
                    Operator.ANY_IN: [
                        list_source_id_selector_same_name_items,
                        ["item-1"],
                    ]
                },
            ],
            True,
        ),
        # Test inverse
        (
            Operator.AND,
            [
                *test_data_mixed_value_sources,
                {
                    Operator.ANY_IN: [
                        list_source_id_selector_same_name_items,
                        ["item-5"],
                    ]
                },
            ],
            False,
        ),
        (
            Operator.OR,
            [
                *test_data_mixed_value_sources,
                {
                    Operator.ALL_IN: [
                        list_source_id_selector_same_name_items,
                        ["item-1"],
                    ]
                },
            ],
            True,
        ),
        # Test inverse
        (
            Operator.OR,
            [
                {
                    Operator.EQUAL: [
                        {"source": "answers", "identifier": "answer-1"},
                        "No",
                    ]
                },
                {
                    Operator.NOT_EQUAL: [
                        {"source": "list", "identifier": "some-list"},
                        5,
                    ]
                },
                {
                    Operator.GREATER_THAN_OR_EQUAL: [
                        {
                            "source": "answers",
                            "identifier": "answer-2",
                            "list_item_selector": {
                                "source": "location",
                                "id": "list_item_id",
                            },
                        },
                        15,
                    ]
                },
                {
                    Operator.IN: [
                        {"source": "metadata", "identifier": "region_code"},
                        ["GB-NIR"],
                    ]
                },
                {
                    Operator.NOT_EQUAL: [
                        list_source_id_selector_first,
                        current_location_source,
                    ]
                },
                {
                    Operator.ANY_IN: [
                        list_source_id_selector_same_name_items,
                        ["item-5"],
                    ]
                },
            ],
            False,
        ),
    ],
)
def test_logic_and_or(operator, operands, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: operands},
        answer_store=AnswerStore(
            [
                {
                    "answer_id": "answer-1",
                    "list_item_id": "item-1",
                    "value": "Yes, I do",
                },
                {
                    "answer_id": "answer-2",
                    "list_item_id": "item-1",
                    "value": 10,
                },
            ]
        ),
        metadata={"region_code": "GB-ENG", "language_code": "en"},
        list_store=ListStore(
            [
                {
                    "name": "some-list",
                    "items": get_list_items(5),
                    "same_name_items": get_list_items(3),
                }
            ],
        ),
        location=Location(
            section_id="some-section", block_id="some-block", list_item_id="item-1"
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, answer_value, result",
    get_test_data_for_source(answer_source),
)
def test_logic_not(operator, first_argument, second_argument, answer_value, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={Operator.NOT: [{operator: [first_argument, second_argument]}]},
        answer_store=AnswerStore([{"answer_id": "some-answer", "value": answer_value}]),
    )

    assert when_rule_evaluator.evaluate() is not result


@pytest.mark.parametrize(
    "operator, first_argument, second_argument, answer_value, result",
    get_test_data_for_source(answer_source),
)
def test_date_source(operator, first_argument, second_argument, answer_value, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={Operator.NOT: [{operator: [first_argument, second_argument]}]},
        answer_store=AnswerStore([{"answer_id": "some-answer", "value": answer_value}]),
    )

    assert when_rule_evaluator.evaluate() is not result


@pytest.mark.parametrize(
    "operator, operands, result",
    [
        (
            Operator.AND,
            [
                {
                    Operator.EQUAL: [
                        {"source": "answers", "identifier": "answer-1"},
                        "Yes, I do",
                    ]
                },
                {
                    Operator.GREATER_THAN_OR_EQUAL: [
                        {
                            "source": "answers",
                            "identifier": "answer-2",
                            "list_item_selector": {
                                "source": "location",
                                "id": "list_item_id",
                            },
                        },
                        9,
                    ]
                },
                {
                    Operator.OR: [
                        {Operator.EQUAL: [list_source, 0]},
                        {
                            Operator.AND: [
                                {
                                    Operator.NOT: [
                                        {
                                            Operator.IN: [
                                                {
                                                    "source": "metadata",
                                                    "identifier": "region_code",
                                                },
                                                ["GB-ENG", "GB-WLS"],
                                            ]
                                        }
                                    ]
                                },
                                {
                                    Operator.IN: [
                                        list_source_id_selector_first,
                                        list_source_id_selector_same_name_items,
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ],
            True,
        ),
        (
            Operator.OR,
            [
                {
                    Operator.NOT_EQUAL: [
                        {"source": "answers", "identifier": "answer-1"},
                        "Yes, I do",
                    ]
                },
                {
                    Operator.OR: [
                        {Operator.EQUAL: [list_source, 0]},
                        {
                            Operator.AND: [
                                {
                                    Operator.NOT: [
                                        {
                                            Operator.IN: [
                                                {
                                                    "source": "metadata",
                                                    "identifier": "region_code",
                                                },
                                                ["GB-ENG", "GB-WLS"],
                                            ]
                                        }
                                    ]
                                },
                                {
                                    Operator.IN: [
                                        list_source_id_selector_first,
                                        list_source_id_selector_same_name_items,
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ],
            True,
        ),
    ],
)
def test_nested_rules(operator, operands, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule={operator: operands},
        answer_store=AnswerStore(
            [
                {
                    "answer_id": "answer-1",
                    "list_item_id": "item-1",
                    "value": "Yes, I do",
                },
                {
                    "answer_id": "answer-2",
                    "list_item_id": "item-1",
                    "value": 10,
                },
            ]
        ),
        metadata={"region_code": "GB-NIR", "language_code": "en"},
        list_store=ListStore(
            [
                {
                    "name": "some-list",
                    "items": get_list_items(5),
                    "same_name_items": get_list_items(3),
                }
            ],
        ),
        location=Location(
            section_id="some-section", block_id="some-block", list_item_id="item-1"
        ),
    )

    assert when_rule_evaluator.evaluate() is result


@pytest.mark.parametrize(
    "rule, result",
    [
        *get_test_data_for_date_value_for_source(answer_source),
        *get_test_data_for_date_value_for_source(metadata_source),
    ],
)
@freeze_time(now)
def test_date_value(rule, result):
    when_rule_evaluator = get_when_rule_evaluator(
        rule=rule,
        answer_store=AnswerStore(
            [
                {
                    "answer_id": "some-answer",
                    "value": formatted_now,
                }
            ]
        ),
        metadata={"some-metadata": formatted_now},
    )

    assert when_rule_evaluator.evaluate() is result
