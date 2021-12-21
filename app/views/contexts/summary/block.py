from flask import url_for

from app.questionnaire.rules.rule_evaluator import RuleEvaluator
from app.questionnaire.when_rules import evaluate_when_rules
from app.views.contexts.summary.question import Question


class Block:
    def __init__(
        self,
        block_schema,
        *,
        answer_store,
        list_store,
        metadata,
        response_metadata,
        schema,
        location,
        return_to,
    ):
        self.id = block_schema["id"]
        self.location = location
        self.title = block_schema.get("title")
        self.number = block_schema.get("number")
        self.link = self._build_link(block_schema["id"], return_to)

        self.question = self.get_question(
            block_schema=block_schema,
            answer_store=answer_store,
            list_store=list_store,
            metadata=metadata,
            response_metadata=response_metadata,
            schema=schema,
            location=location,
        )

    def _build_link(self, block_id, return_to):
        return url_for(
            "questionnaire.block",
            list_name=self.location.list_name,
            block_id=block_id,
            list_item_id=self.location.list_item_id,
            return_to=return_to,
        )

    @staticmethod
    def get_question(
        *,
        block_schema,
        answer_store,
        list_store,
        metadata,
        response_metadata,
        schema,
        location,
    ):
        """ Taking question variants into account, return the question which was displayed to the user """
        list_item_id = location.list_item_id
        rule_evaluator = RuleEvaluator(
            schema=schema,
            answer_store=answer_store,
            list_store=list_store,
            metadata=metadata,
            response_metadata=response_metadata,
            location=location,
        )

        for variant in block_schema.get("question_variants", []):
            display_variant = evaluate_when_rules(
                variant.get("when"),
                schema,
                metadata,
                answer_store,
                list_store,
                location,
            )
            if display_variant:
                return Question(
                    variant["question"],
                    answer_store=answer_store,
                    schema=schema,
                    list_item_id=list_item_id,
                    rule_evaluator=rule_evaluator,
                ).serialize()

        return Question(
            block_schema["question"],
            answer_store=answer_store,
            schema=schema,
            list_item_id=list_item_id,
            rule_evaluator=rule_evaluator,
        ).serialize()

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "number": self.number,
            "link": self.link,
            "question": self.question,
        }
