from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Union

from flask import url_for
from werkzeug.utils import redirect

from app.questionnaire.location import InvalidLocationException
from app.questionnaire.router import Router
from app.views.contexts import SubmitContext
from app.views.handlers.submission import SubmissionHandler

if TYPE_CHECKING:
    from werkzeug import Response  # pragma: no cover
    from app.data_models import QuestionnaireStore  # pragma: no cover
    from app.questionnaire import QuestionnaireSchema  # pragma: no cover


class SubmitHandler:
    def __init__(
        self,
        schema: QuestionnaireSchema,
        questionnaire_store: QuestionnaireStore,
        language: str,
    ):
        self._schema = schema
        self._questionnaire_store = questionnaire_store
        self._language = language
        self._router = Router(
            schema,
            questionnaire_store.answer_store,
            questionnaire_store.list_store,
            questionnaire_store.progress_store,
            questionnaire_store.metadata,
        )
        if not self._is_valid_location():
            raise InvalidLocationException(
                "Submit page not enabled or questionnaire is not complete"
            )

    @cached_property
    def router(self) -> Router:
        return Router(
            schema=self._schema,
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            progress_store=self._questionnaire_store.progress_store,
            metadata=self._questionnaire_store.metadata,
        )

    def get_context(self) -> dict[str, Union[str, dict]]:
        submit_context = SubmitContext(
            language=self._language,
            schema=self._schema,
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            progress_store=self._questionnaire_store.progress_store,
            metadata=self._questionnaire_store.metadata,
        )
        return submit_context()

    def _is_valid_location(self) -> bool:
        return (
            self._schema.is_questionnaire_flow_linear
            and self.router.is_questionnaire_complete
        )

    def get_previous_location_url(self) -> str:
        return self.router.get_last_location_in_questionnaire().url()

    @property
    def template(self) -> str:
        include_summary = self._schema.questionnaire_flow_options["include_summary"]
        return "summary" if include_summary else "confirmation"

    def handle_post(self) -> Response:
        submission_handler = SubmissionHandler(
            self._schema, self._questionnaire_store, self.router.full_routing_path()
        )
        submission_handler.submit_questionnaire()
        return redirect(url_for("post_submission.get_thank_you"))
