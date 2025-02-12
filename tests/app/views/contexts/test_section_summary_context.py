from unittest.mock import MagicMock

import pytest

from app.data_models.answer_store import Answer, AnswerStore
from app.data_models.list_store import ListStore
from app.data_models.progress_store import ProgressStore
from app.questionnaire.location import Location
from app.questionnaire.questionnaire_schema import DEFAULT_LANGUAGE_CODE
from app.questionnaire.routing_path import RoutingPath
from app.utilities.schema import load_schema_from_name
from app.views.contexts import SectionSummaryContext
from tests.app.views.contexts import assert_summary_context


def test_build_summary_rendering_context(
    test_section_summary_schema, answer_store, list_store, progress_store, mocker
):
    section_summary_context = SectionSummaryContext(
        "en",
        test_section_summary_schema,
        answer_store,
        list_store,
        progress_store,
        metadata={},
        response_metadata={},
        current_location=Location(section_id="property-details-section"),
        routing_path=mocker.MagicMock(),
    )

    single_section_context = section_summary_context()

    assert_summary_context(single_section_context)


def test_build_view_context_for_section_summary(
    test_section_summary_schema, answer_store, list_store, progress_store, mocker
):
    summary_context = SectionSummaryContext(
        "en",
        test_section_summary_schema,
        answer_store,
        list_store,
        progress_store,
        metadata={},
        response_metadata={},
        current_location=Location(
            section_id="property-details-section",
            block_id="property-details-summary",
        ),
        routing_path=mocker.MagicMock(),
    )
    context = summary_context()

    assert "summary" in context
    assert_summary_context(context)
    assert len(context["summary"]) == 6
    assert "title" in context["summary"]


@pytest.mark.parametrize(
    "answers, location, title_key, expected_title",
    (
        (
            [Answer(answer_id="house-type-answer", value="Semi-detached")],
            Location(section_id="house-details-section"),
            "title",
            "Household Summary - Semi-detached",
        ),
        (
            [],
            Location(section_id="property-details-section"),
            "page_title",
            "Custom section summary title",
        ),
        (
            [Answer(answer_id="house-type-answer", value="Semi-detached")],
            Location(section_id="house-details-section"),
            "page_title",
            "Household Summary - …",
        ),
        (
            [Answer(answer_id="number-of-people-answer", value=3)],
            Location(section_id="household-count-section"),
            "page_title",
            "… people live here",
        ),
        (
            [],
            Location(section_id="property-details-section"),
            "title",
            "Property Details Section",
        ),
    ),
)
def test_custom_section(
    answers,
    location,
    title_key,
    expected_title,
    test_section_summary_schema,
    answer_store,
    list_store,
    progress_store,
    mocker,
):
    for answer in answers:
        answer_store.add_or_update(answer)

    summary_context = SectionSummaryContext(
        "en",
        test_section_summary_schema,
        answer_store,
        list_store,
        progress_store,
        metadata={},
        response_metadata={},
        current_location=location,
        routing_path=mocker.MagicMock(),
    )
    context = summary_context()
    assert context["summary"][title_key] == expected_title


@pytest.mark.usefixtures("app")
def test_context_for_section_list_summary(people_answer_store):
    schema = load_schema_from_name("test_list_collector_section_summary")

    summary_context = SectionSummaryContext(
        language=DEFAULT_LANGUAGE_CODE,
        schema=schema,
        answer_store=people_answer_store,
        list_store=ListStore(
            [
                {"items": ["PlwgoG", "UHPLbX"], "name": "people"},
                {"items": ["gTrlio"], "name": "visitors"},
            ]
        ),
        progress_store=ProgressStore(),
        metadata={"display_address": "70 Abingdon Road, Goathill"},
        response_metadata={},
        current_location=Location(section_id="section"),
        routing_path=RoutingPath(
            [
                "primary-person-list-collector",
                "list-collector",
                "visitor-list-collector",
            ],
            section_id="section",
        ),
    )
    context = summary_context()
    expected = {
        "summary": {
            "answers_are_editable": True,
            "collapsible": False,
            "custom_summary": [
                {
                    "add_link": "/questionnaire/people/add-person/?return_to=section-summary",
                    "add_link_text": "Add someone to this household",
                    "empty_list_text": "There are no householders",
                    "list": {
                        "editable": True,
                        "list_items": [
                            {
                                "edit_link": "/questionnaire/people/PlwgoG/edit-person/?return_to=section-summary",
                                "item_title": "Toni Morrison",
                                "primary_person": False,
                                "remove_link": "/questionnaire/people/PlwgoG/remove-person/?return_to=section-summary",
                                "list_item_id": "PlwgoG",
                            },
                            {
                                "edit_link": "/questionnaire/people/UHPLbX/edit-person/?return_to=section-summary",
                                "item_title": "Barry Pheloung",
                                "primary_person": False,
                                "remove_link": "/questionnaire/people/UHPLbX/remove-person/?return_to=section-summary",
                                "list_item_id": "UHPLbX",
                            },
                        ],
                    },
                    "list_name": "people",
                    "title": "Household members staying overnight on 13 October 2019 at 70 Abingdon Road, Goathill",
                    "type": "List",
                },
                {
                    "add_link": "/questionnaire/visitors/add-visitor/?return_to=section-summary",
                    "add_link_text": "Add another visitor to this household",
                    "empty_list_text": "There are no visitors",
                    "list": {
                        "editable": True,
                        "list_items": [
                            {
                                "edit_link": "/questionnaire/visitors/gTrlio/edit-visitor-person/?return_to=section-summary",
                                "item_title": "",
                                "primary_person": False,
                                "remove_link": "/questionnaire/visitors/gTrlio/remove-visitor/?return_to=section-summary",
                                "list_item_id": "gTrlio",
                            }
                        ],
                    },
                    "list_name": "visitors",
                    "title": "Visitors staying overnight on 13 October 2019 at 70 Abingdon Road, Goathill",
                    "type": "List",
                },
            ],
            "page_title": "People who live here and overnight visitors",
            "summary_type": "SectionSummary",
            "title": "People who live here and overnight visitors",
        }
    }

    assert context == expected


@pytest.mark.usefixtures("app")
def test_context_for_driving_question_summary_empty_list():
    schema = load_schema_from_name("test_list_collector_driving_question")

    summary_context = SectionSummaryContext(
        DEFAULT_LANGUAGE_CODE,
        schema,
        AnswerStore([{"answer_id": "anyone-usually-live-at-answer", "value": "No"}]),
        ListStore(),
        ProgressStore(),
        metadata={},
        response_metadata={},
        current_location=Location(section_id="section"),
        routing_path=RoutingPath(["anyone-usually-live-at"], section_id="section"),
    )

    context = summary_context()
    expected = {
        "summary": {
            "answers_are_editable": True,
            "collapsible": False,
            "custom_summary": [
                {
                    "add_link": "/questionnaire/anyone-usually-live-at/?return_to=section-summary",
                    "add_link_text": "Add someone to this household",
                    "empty_list_text": "There are no householders",
                    "list": {"editable": False, "list_items": []},
                    "list_name": "people",
                    "title": "Household members",
                    "type": "List",
                }
            ],
            "page_title": "List Collector Driving Question Summary",
            "summary_type": "SectionSummary",
            "title": "List Collector Driving Question Summary",
        }
    }

    assert context == expected


@pytest.mark.usefixtures("app")
def test_context_for_driving_question_summary():
    schema = load_schema_from_name("test_list_collector_driving_question")

    summary_context = SectionSummaryContext(
        DEFAULT_LANGUAGE_CODE,
        schema,
        AnswerStore(
            [
                {"answer_id": "anyone-usually-live-at-answer", "value": "Yes"},
                {"answer_id": "first-name", "value": "Toni", "list_item_id": "PlwgoG"},
                {
                    "answer_id": "last-name",
                    "value": "Morrison",
                    "list_item_id": "PlwgoG",
                },
            ]
        ),
        ListStore([{"items": ["PlwgoG"], "name": "people"}]),
        ProgressStore(),
        metadata={},
        response_metadata={},
        current_location=Location(section_id="section"),
        routing_path=RoutingPath(
            ["anyone-usually-live-at", "anyone-else-live-at"], section_id="section"
        ),
    )

    context = summary_context()

    expected = {
        "summary": {
            "answers_are_editable": True,
            "collapsible": False,
            "custom_summary": [
                {
                    "add_link": "/questionnaire/people/add-person/?return_to=section-summary",
                    "add_link_text": "Add someone to this household",
                    "empty_list_text": "There are no householders",
                    "list": {
                        "editable": True,
                        "list_items": [
                            {
                                "item_title": "Toni Morrison",
                                "primary_person": False,
                                "edit_link": "/questionnaire/people/PlwgoG/edit-person/?return_to=section-summary",
                                "remove_link": "/questionnaire/people/PlwgoG/remove-person/?return_to=section-summary",
                                "list_item_id": "PlwgoG",
                            }
                        ],
                    },
                    "list_name": "people",
                    "title": "Household members",
                    "type": "List",
                }
            ],
            "page_title": "List Collector Driving Question Summary",
            "summary_type": "SectionSummary",
            "title": "List Collector Driving Question Summary",
        }
    }

    assert context == expected


@pytest.mark.usefixtures("app")
def test_titles_for_repeating_section_summary(people_answer_store):
    schema = load_schema_from_name("test_repeating_sections_with_hub_and_spoke")

    section_summary_context = SectionSummaryContext(
        DEFAULT_LANGUAGE_CODE,
        schema,
        people_answer_store,
        ListStore(
            [
                {"items": ["PlwgoG", "UHPLbX"], "name": "people"},
                {"items": ["gTrlio"], "name": "visitors"},
            ]
        ),
        ProgressStore(),
        metadata={},
        response_metadata={},
        current_location=Location(
            section_id="personal-details-section",
            list_name="people",
            list_item_id="PlwgoG",
        ),
        routing_path=MagicMock(),
    )

    context = section_summary_context()

    assert context["summary"]["title"] == "Toni Morrison"

    section_summary_context = SectionSummaryContext(
        DEFAULT_LANGUAGE_CODE,
        schema,
        people_answer_store,
        ListStore(
            [
                {"items": ["PlwgoG", "UHPLbX"], "name": "people"},
                {"items": ["gTrlio"], "name": "visitors"},
            ]
        ),
        ProgressStore(),
        metadata={},
        response_metadata={},
        current_location=Location(
            block_id="personal-summary",
            section_id="personal-details-section",
            list_name="people",
            list_item_id="UHPLbX",
        ),
        routing_path=MagicMock(),
    )

    context = section_summary_context()
    assert context["summary"]["title"] == "Barry Pheloung"


@pytest.mark.usefixtures("app")
def test_primary_only_links_for_section_summary(people_answer_store):
    schema = load_schema_from_name("test_list_collector_section_summary")

    summary_context = SectionSummaryContext(
        language=DEFAULT_LANGUAGE_CODE,
        schema=schema,
        answer_store=people_answer_store,
        list_store=ListStore(
            [{"items": ["PlwgoG"], "name": "people", "primary_person": "PlwgoG"}]
        ),
        progress_store=ProgressStore(),
        metadata={"display_address": "70 Abingdon Road, Goathill"},
        response_metadata={},
        current_location=Location(section_id="section"),
        routing_path=RoutingPath(
            [
                "primary-person-list-collector",
                "list-collector",
                "visitor-list-collector",
            ],
            section_id="section",
        ),
    )
    context = summary_context()

    list_items = context["summary"]["custom_summary"][0]["list"]["list_items"]

    assert "/add-or-edit-primary-person/" in list_items[0]["edit_link"]


@pytest.mark.usefixtures("app")
def test_primary_links_for_section_summary(people_answer_store):
    schema = load_schema_from_name("test_list_collector_section_summary")

    summary_context = SectionSummaryContext(
        language=DEFAULT_LANGUAGE_CODE,
        schema=schema,
        answer_store=people_answer_store,
        list_store=ListStore(
            [
                {
                    "items": ["PlwgoG", "fg0sPd"],
                    "name": "people",
                    "primary_person": "PlwgoG",
                }
            ]
        ),
        progress_store=ProgressStore(),
        metadata={"display_address": "70 Abingdon Road, Goathill"},
        response_metadata={},
        current_location=Location(section_id="section"),
        routing_path=RoutingPath(
            [
                "primary-person-list-collector",
                "list-collector",
                "visitor-list-collector",
            ],
            section_id="section",
        ),
    )
    context = summary_context()

    list_items = context["summary"]["custom_summary"][0]["list"]["list_items"]

    assert "/edit-person/" in list_items[0]["edit_link"]
    assert "/edit-person/" in list_items[1]["edit_link"]
