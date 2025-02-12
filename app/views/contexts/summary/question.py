from flask import url_for
from markupsafe import escape

from app.data_models.answer import escape_answer_value
from app.forms.field_handlers.select_handlers import DynamicAnswerOptions
from app.views.contexts.summary.answer import Answer


class Question:
    def __init__(
        self,
        question_schema,
        *,
        answer_store,
        schema,
        rule_evaluator,
        value_source_resolver,
        location,
        block_id,
        return_to,
    ):
        self.list_item_id = location.list_item_id if location else None
        self.id = question_schema["id"]
        self.type = question_schema["type"]
        self.schema = schema
        self.answer_schemas = iter(question_schema["answers"])
        self.summary = question_schema.get("summary")
        self.title = (
            question_schema.get("title") or question_schema["answers"][0]["label"]
        )
        self.number = question_schema.get("number", None)

        self.rule_evaluator = rule_evaluator
        self.value_source_resolver = value_source_resolver

        self.answers = self._build_answers(
            answer_store=answer_store,
            question_schema=question_schema,
            block_id=block_id,
            list_name=location.list_name if location else None,
            return_to=return_to,
        )

    def get_answer(self, answer_store, answer_id):
        answer = answer_store.get_answer(
            answer_id, self.list_item_id
        ) or self.schema.get_default_answer(answer_id)

        return escape_answer_value(answer.value) if answer else None

    def _build_answers(
        self, *, answer_store, question_schema, block_id, list_name, return_to
    ):

        if self.summary:
            answer_id = f"{self.id}-concatenated-answer"
            link = url_for(
                "questionnaire.block",
                list_name=list_name,
                block_id=block_id,
                list_item_id=self.list_item_id,
                return_to=return_to,
                return_to_answer_id=answer_id,
                _anchor=answer_id,
            )

            return [
                {
                    "id": answer_id,
                    "value": self._concatenate_answers(
                        answer_store, self.summary["concatenation_type"]
                    ),
                    "link": link,
                }
            ]

        summary_answers = []
        for answer_schema in self.answer_schemas:
            answer_value = self.get_answer(answer_store, answer_schema["id"])
            answer = self._build_answer(
                answer_store, question_schema, answer_schema, answer_value
            )

            summary_answer = Answer(
                answer_schema=answer_schema,
                answer_value=answer,
                block_id=block_id,
                list_name=list_name,
                list_item_id=self.list_item_id,
                return_to=return_to,
            ).serialize()
            summary_answers.append(summary_answer)

        if question_schema["type"] == "MutuallyExclusive":
            exclusive_option = summary_answers[-1]["value"]
            if exclusive_option:
                return summary_answers[-1:]
            return summary_answers[:-1]
        return summary_answers

    def _concatenate_answers(self, answer_store, concatenation_type):

        answer_separators = {"Newline": "<br>", "Space": " "}
        answer_separator = answer_separators.get(concatenation_type, " ")

        answer_values = [
            self.get_answer(answer_store, answer_schema["id"])
            for answer_schema in self.answer_schemas
        ]

        values_to_concatenate = []
        for answer_value in answer_values:
            if not answer_value:
                continue

            values_to_concatenate.extend(
                answer_value if isinstance(answer_value, list) else [answer_value]
            )

        return answer_separator.join(str(value) for value in values_to_concatenate)

    def _build_answer(
        self, answer_store, question_schema, answer_schema, answer_value=None
    ):
        if answer_value is None:
            return None

        if question_schema["type"] == "DateRange":
            return self._build_date_range_answer(answer_store, answer_value)

        if answer_schema["type"] == "Dropdown":
            return self._build_dropdown_answer(answer_value, answer_schema)

        answer_builder = {
            "Checkbox": self._build_checkbox_answers,
            "Radio": self._build_radio_answer,
        }

        if answer_schema["type"] in answer_builder:
            return answer_builder[answer_schema["type"]](
                answer_value, answer_schema, answer_store
            )

        return answer_value

    def _build_date_range_answer(self, answer_store, answer):
        next_answer = next(self.answer_schemas)
        to_date = self.get_answer(answer_store, next_answer["id"])
        return {"from": answer, "to": to_date}

    def _get_dynamic_answer_options(
        self,
        answer_schema,
    ):
        if not (dynamic_options_schema := answer_schema.get("dynamic_options")):
            return ()

        dynamic_options = DynamicAnswerOptions(
            dynamic_options_schema=dynamic_options_schema,
            rule_evaluator=self.rule_evaluator,
            value_source_resolver=self.value_source_resolver,
        )

        return dynamic_options.evaluate()

    def get_answer_options(self, answer_schema):
        return tuple(answer_schema.get("options", ())) + tuple(
            self._get_dynamic_answer_options(answer_schema)
        )

    def _build_checkbox_answers(self, answer, answer_schema, answer_store):
        multiple_answers = []
        for option in self.get_answer_options(answer_schema):
            if escape(option["value"]) in answer:
                detail_answer_value = self._get_detail_answer_value(
                    option, answer_store
                )

                multiple_answers.append(
                    {
                        "label": option["label"],
                        "detail_answer_value": detail_answer_value,
                    }
                )

        return multiple_answers or None

    def _build_radio_answer(self, answer, answer_schema, answer_store):
        for option in self.get_answer_options(answer_schema):
            if answer == escape(option["value"]):
                detail_answer_value = self._get_detail_answer_value(
                    option, answer_store
                )
                return {
                    "label": option["label"],
                    "detail_answer_value": detail_answer_value,
                }

    def _get_detail_answer_value(self, option, answer_store):
        if "detail_answer" in option:
            return self.get_answer(answer_store, option["detail_answer"]["id"])

    def _build_dropdown_answer(self, answer, answer_schema):
        for option in self.get_answer_options(answer_schema):
            if answer == option["value"]:
                return option["label"]

    def serialize(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "number": self.number,
            "answers": self.answers,
        }
