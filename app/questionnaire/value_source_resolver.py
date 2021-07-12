from dataclasses import dataclass
from typing import Optional, Union

from app.data_models import AnswerStore, ListStore
from app.data_models.list_store import ListModel
from app.questionnaire import Location
from app.questionnaire.relationship_location import RelationshipLocation

value_source_types = Union[str, int, float, list, None]


@dataclass
class ValueSourceResolver:
    answer_store: AnswerStore
    list_store: ListStore
    metadata: dict
    location: Union[Location, RelationshipLocation]
    list_item_id: str

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

        return value or self.list_item_id

    def _resolve_answer_value(self, value_source: dict) -> value_source_types:
        list_item_id = self._get_list_item_id_from_value_source(value_source)
        answer = self.answer_store.get_escaped_answer_value(
            value_source["identifier"], list_item_id
        )
        value: value_source_types = (
            answer.get(value_source["selector"])
            if "selector" in value_source
            else answer
        )
        return value

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
