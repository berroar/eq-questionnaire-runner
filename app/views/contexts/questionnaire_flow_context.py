from app.data_models.questionnaire_store import QuestionnaireStore
from app.questionnaire.questionnaire_schema import QuestionnaireSchema
from app.views.contexts import (
    HubQuestionnaireFlowContext,
    LinearQuestionnaireFlowContext,
)


class QuestionnaireFlowContext:
    def __init__(
        self,
        schema: QuestionnaireSchema,
        questionnaire_store: QuestionnaireStore,
        language: str,
        is_survey_complete: bool,
        enabled_section_ids: list,
    ):
        self._schema = schema
        self._questionnaire_store = questionnaire_store
        self._language = language
        self._is_survey_complete = is_survey_complete
        self._enabled_section_ids = enabled_section_ids
        self._template = None

    def __call__(self):
        if self._schema.is_questionnaire_flow_hub:
            self._template = "hub"
            return self.hub_flow_context()

        if self._schema.is_questionnaire_flow_linear:
            include_summary = self._schema.questionnaire_flow_options["include_summary"]
            self._template = "summary" if include_summary else "confirmation"
            return self.linear_flow_context()

        raise NotImplementedError("Only Hub and Linear flows are supported")

    def hub_flow_context(self):
        hub_context = HubQuestionnaireFlowContext(
            language=self._language,
            schema=self._schema,
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            progress_store=self._questionnaire_store.progress_store,
            metadata=self._questionnaire_store.metadata,
        )
        return hub_context(
            survey_complete=self._is_survey_complete,
            enabled_section_ids=self._enabled_section_ids,
        )

    def linear_flow_context(self):
        linear_questionnaire_flow_context = LinearQuestionnaireFlowContext(
            self._language,
            self._schema,
            self._questionnaire_store.answer_store,
            self._questionnaire_store.list_store,
            self._questionnaire_store.progress_store,
            self._questionnaire_store.metadata,
        )
        collapsible = self._schema.questionnaire_flow_options.get("collapsible", False)
        include_summary = self._schema.questionnaire_flow_options["include_summary"]
        return linear_questionnaire_flow_context(
            include_summary=include_summary, collapsible=collapsible
        )

    @property
    def template(self):
        return self._template
