from dataclasses import dataclass, field
from typing import Optional, Union

from app.data_models import AnswerStore, ListStore
from app.questionnaire import Location, QuestionnaireSchema
from app.questionnaire.relationship_location import RelationshipLocation
from app.questionnaire.routing.operators import Operator
from app.questionnaire.value_source_resolver import ValueSourceResolver


@dataclass
class WhenRuleEvaluator:
    rule: dict
    schema: QuestionnaireSchema
    answer_store: AnswerStore
    list_store: ListStore
    metadata: dict
    location: Union[Location, RelationshipLocation]
    routing_path_block_ids: Optional[list] = field(default_factory=list)

    def __post_init__(self):
        self.value_source_resolver = ValueSourceResolver(
            answer_store=self.answer_store,
            list_store=self.list_store,
            metadata=self.metadata,
            schema=self.schema,
            location=self.location,
            list_item_id=self.location.list_item_id,
            routing_path_block_ids=self.routing_path_block_ids,
            use_default_value=True,
        )

    def _evaluate(self, rule):
        if not isinstance(rule, dict):
            return rule

        if "source" in rule:
            return self.value_source_resolver.resolve(rule)

        operator = Operator(next(iter(rule)))
        operands = rule[operator.name]

        if not isinstance(operands, (list, tuple)):
            raise TypeError(f"Got non list or tuple for operands - {type(operands)}")

        operands = (self._evaluate(operand) for operand in operands)
        return operator.evaluate(operands)

    def evaluate(self):
        return self._evaluate(self.rule)
