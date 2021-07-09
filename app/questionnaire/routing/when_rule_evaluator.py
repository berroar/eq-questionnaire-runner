from dataclasses import dataclass

from app.questionnaire.routing.operators import Operator


@dataclass
class WhenRuleEvaluator:
    rule: dict
    schema = None
    metadata = None
    answer_store = None
    list_store = None
    current_location = None
    routing_path_block_ids = None

    def _evaluate(self, rule):
        if not isinstance(rule, dict):
            return rule

        operator = Operator(next(iter(rule)))
        operands = rule[operator.name]

        if not isinstance(operands, list) and not isinstance(operands, tuple):
            raise Exception("Got non list or tuple")

        operands = (self._evaluate(operand) for operand in operands)
        return operator.evaluate(operands)

    def evaluate(self):
        return self._evaluate(self.rule)
