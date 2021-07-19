from dataclasses import dataclass
from typing import Optional, Union

from app.data_models import AnswerStore, ListStore
from app.data_models.list_store import ListModel
from app.questionnaire import Location, QuestionnaireSchema
from app.questionnaire.relationship_location import RelationshipLocation

answer_value_types = Union[str, int, float, list, dict, None]
value_source_types = Union[str, int, float, list, None]


@dataclass
class ValueSourceResolver:
    answer_store: AnswerStore
    list_store: ListStore
    metadata: dict
    schema: QuestionnaireSchema
    location: Union[Location, RelationshipLocation]
    list_item_id: Optional[str]
    routing_path_block_ids: Optional[list] = None
    use_default_value: bool = False

    def _get_list_item_id_from_value_source(self, value_source: dict) -> Optional[str]:
        list_item_selector = value_source.get("list_item_selector")
        value: Optional[str] = None
        if list_item_selector:
            if list_item_selector["source"] == "location":
                value = getattr(self.location, list_item_selector["id"])
            elif list_item_selector["source"] == "list":
                value = getattr(
                    self.list_store[list_item_selector["id"]],
                    list_item_selector["id_selector"],
                )

        return value

    def _is_answer_on_path(self, answer_id: str) -> bool:
        if self.routing_path_block_ids:
            block = self.schema.get_block_for_answer_id(answer_id)
            return block is not None and block["id"] in self.routing_path_block_ids

        return True

    def _get_answer_value(
        self, answer_id: str, list_item_id: Optional[str]
    ) -> answer_value_types:
        if not self._is_answer_on_path(answer_id):
            return None

        if answer := self.answer_store.get_answer(answer_id, list_item_id):
            return answer.value

        if self.use_default_value and (
            answer := self.schema.get_default_answer(answer_id)
        ):
            return answer.value

    def _resolve_answer_value(self, value_source: dict) -> value_source_types:
        list_item_id = self._get_list_item_id_from_value_source(value_source)
        answer_id = value_source["identifier"]
        if not list_item_id:
            list_item_id = (
                self.list_item_id
                if self.list_item_id
                and self.schema.answer_should_have_list_item_id(answer_id)
                else None
            )

        answer_value = self._get_answer_value(
            answer_id=answer_id, list_item_id=list_item_id
        )

        if isinstance(answer_value, dict):
            return (
                answer_value.get(value_source["selector"])
                if "selector" in value_source
                else None
            )

        return answer_value

    def _resolve_value_source_list(
        self, value_source_list: list[dict]
    ) -> list[Union[str, int, float, None]]:
        values: list[Union[str, int, float, None]] = []
        for value_source in value_source_list:
            value = self._resolve(value_source)
            if isinstance(value, list):
                values.extend(value)
            else:
                values.append(value)
        return values

    def _resolve(self, value_source: dict) -> value_source_types:
        if value_source["source"] == "answers":
            return self._resolve_answer_value(value_source)
        if value_source["source"] == "metadata":
            return self.metadata.get(value_source["identifier"])
        if value_source["source"] == "list":
            id_selector = value_source.get("id_selector")
            list_model: ListModel = self.list_store[value_source["identifier"]]

            if id_selector:
                value: Union[str, list] = getattr(list_model, id_selector)
                return value

            return len(list_model)
        if (
            value_source["source"] == "location"
            and value_source["identifier"] == "list_item_id"
        ):
            return self.list_item_id

    def resolve(self, value_source: Union[list, dict]) -> value_source_types:
        if isinstance(value_source, list):
            return self._resolve_value_source_list(value_source)

        return self._resolve(value_source)
