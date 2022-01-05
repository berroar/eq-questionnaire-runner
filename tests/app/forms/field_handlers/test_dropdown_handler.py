from wtforms import Form, SelectField

from app.forms import error_messages
from app.forms.field_handlers.dropdown_handler import DropdownHandler


def test_build_choices_without_placeholder(
    dropdown_answer_schema, value_source_resolver, rule_evaluator
):
    handler = DropdownHandler(
        dropdown_answer_schema, value_source_resolver, rule_evaluator, error_messages
    )

    expected_choices = [("", "Select an answer")] + [
        (option["label"], option["value"])
        for option in dropdown_answer_schema["options"]
    ]

    assert handler.choices == expected_choices


def test_build_choices_with_placeholder(
    dropdown_answer_schema, value_source_resolver, rule_evaluator
):
    dropdown_answer_schema["placeholder"] = "Select an option"
    handler = DropdownHandler(
        dropdown_answer_schema, value_source_resolver, rule_evaluator, error_messages
    )

    expected_choices = [("", "Select an option")] + [
        (option["label"], option["value"])
        for option in dropdown_answer_schema["options"]
    ]

    assert handler.choices == expected_choices


def test_get_field(dropdown_answer_schema, value_source_resolver, rule_evaluator):
    handler = DropdownHandler(
        dropdown_answer_schema, value_source_resolver, rule_evaluator, error_messages
    )

    expected_choices = [("", "Select an answer")] + [
        (option["label"], option["value"])
        for option in dropdown_answer_schema["options"]
    ]

    class TestForm(Form):
        test_field = handler.get_field()

    form = TestForm()

    assert isinstance(form.test_field, SelectField)
    assert form.test_field.label.text == dropdown_answer_schema["label"]
    assert form.test_field.description == ""
    assert form.test_field.default == ""
    assert form.test_field.choices == expected_choices
