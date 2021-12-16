import pytest

from app.data_models.answer_store import AnswerStore
from app.data_models.list_store import ListStore
from app.questionnaire import QuestionnaireSchema
from app.questionnaire.rules.rule_evaluator import RuleEvaluator
from app.questionnaire.value_source_resolver import ValueSourceResolver


def get_mock_schema():
    return QuestionnaireSchema(
        {
            "questionnaire_flow": {
                "type": "Linear",
                "options": {"summary": {"collapsible": False}},
            }
        }
    )


def get_mock_answer_store():
    return AnswerStore()


def get_mock_list_store():
    return ListStore()


def get_mock_metadata():
    return {}


def get_mock_response_metadata():
    return {}


def get_mock_location():
    return None


def get_mock_list_item_id():
    return None


def escape_answer_values():
    return False


@pytest.fixture
def rule_evaluator():
    resolver = RuleEvaluator(
        answer_store=get_mock_answer_store(),
        list_store=get_mock_list_store(),
        metadata=get_mock_metadata(),
        response_metadata=get_mock_response_metadata(),
        schema=get_mock_schema(),
        location=get_mock_location(),
    )

    return resolver


@pytest.fixture
def value_source_resolver():
    resolver = ValueSourceResolver(
        answer_store=get_mock_answer_store(),
        list_store=get_mock_list_store(),
        metadata=get_mock_metadata(),
        response_metadata=get_mock_response_metadata(),
        schema=get_mock_schema(),
        location=get_mock_location(),
        list_item_id=get_mock_list_item_id(),
        escape_answer_values=escape_answer_values(),
    )

    return resolver


@pytest.fixture
def dropdown_answer_schema():
    return {
        "type": "Dropdown",
        "id": "dropdown-with-label-answer",
        "mandatory": False,
        "label": "Please choose an option",
        "description": "This is an optional dropdown",
        "options": [
            {"label": "Liverpool", "value": "Liverpool"},
            {"label": "Chelsea", "value": "Chelsea"},
            {"label": "Rugby is better!", "value": "Rugby is better!"},
        ],
    }
