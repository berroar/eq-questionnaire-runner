from datetime import datetime, timezone
from functools import cached_property
from typing import List, Mapping, Optional
from uuid import uuid4

from flask import current_app, redirect
from flask.helpers import url_for
from flask_babel import lazy_gettext
from itsdangerous import BadSignature
from werkzeug.exceptions import BadRequest, NotFound

from app.data_models import CompletionStatus, FulfilmentRequest
from app.forms.questionnaire_form import generate_form
from app.forms.validators import sanitise_mobile_number
from app.helpers import url_safe_serializer
from app.helpers.template_helpers import render_template
from app.publisher.exceptions import PublicationFailed
from app.questionnaire.placeholder_renderer import PlaceholderRenderer
from app.questionnaire.router import Router
from app.views.contexts.question import build_question_context

GB_ENG_REGION_CODE = "GB-ENG"
GB_WLS_REGION_CODE = "GB-WLS"
GB_NIR_REGION_CODE = "GB-NIR"


class IndividualResponseLimitReached(Exception):
    pass


class IndividualResponseFulfilmentRequestPublicationFailed(Exception):
    pass


class IndividualResponsePostalDeadlinePast(Exception):
    pass


class IndividualResponseHandler:
    @staticmethod
    def _person_name_transforms(list_name) -> List[Mapping]:
        return [
            {
                "transform": "contains",
                "arguments": {
                    "list_to_check": {
                        "source": "list",
                        "selector": "same_name_items",
                        "identifier": list_name,
                    },
                    "value": {"source": "location", "identifier": "list_item_id"},
                },
            },
            {
                "transform": "format_name",
                "arguments": {
                    "include_middle_names": {"source": "previous_transform"},
                    "first_name": {"source": "answers", "identifier": "first-name"},
                    "middle_names": {"source": "answers", "identifier": "middle-names"},
                    "last_name": {"source": "answers", "identifier": "last-name"},
                },
            },
        ]

    @staticmethod
    def _person_name_placeholder(list_name) -> List[Mapping]:
        return [
            {
                "placeholder": "person_name",
                "transforms": IndividualResponseHandler._person_name_transforms(
                    list_name
                ),
            }
        ]

    @staticmethod
    def _person_name_placeholder_possessive(list_name) -> List[Mapping]:
        name_transforms = IndividualResponseHandler._person_name_transforms(list_name)
        return [
            {
                "placeholder": "person_name_possessive",
                "transforms": name_transforms
                + [
                    {
                        "arguments": {
                            "string_to_format": {"source": "previous_transform"}
                        },
                        "transform": "format_possessive",
                    }
                ],
            }
        ]

    @cached_property
    def has_postal_deadline_passed(self):
        individual_response_postal_deadline = current_app.config[
            "EQ_INDIVIDUAL_RESPONSE_POSTAL_DEADLINE"
        ]
        return individual_response_postal_deadline < datetime.now(timezone.utc)

    def __init__(
        self,
        schema,
        questionnaire_store,
        language,
        request_args,
        form_data,
        list_item_id=None,
    ):
        self._schema = schema
        self._questionnaire_store = questionnaire_store
        self._language = language
        self._request_args = request_args or {}
        self._form_data = form_data
        self._answers = None
        self._list_item_id = list_item_id
        self._list_name = self._schema.get_individual_response_list()

        self._metadata = self._questionnaire_store.metadata

        self._response_metadata = self._questionnaire_store.response_metadata

        if not self._is_location_valid():
            raise NotFound

    @cached_property
    def _list_model(self):
        return self._questionnaire_store.list_store[self._list_name]

    @cached_property
    def _list_item_position(self):
        return self._questionnaire_store.list_store.list_item_position(
            self._list_name, self._list_item_id
        )

    def page_title(self, page_title):
        if self._list_item_id:
            page_title += ": " + lazy_gettext(
                "Person {list_item_position}".format(  # pylint: disable=consider-using-f-string
                    list_item_position=self._list_item_position
                )
            )
        return page_title

    def _is_location_valid(self):
        if not self._list_model:
            return False

        if self._list_item_id:
            if self._list_item_id not in self._list_model:
                return False

            if self._list_item_id == self._list_model.primary_person:
                return False

        return True

    @cached_property
    def rendered_block(self) -> Mapping:
        return self._render_block()

    @cached_property
    def placeholder_renderer(self):
        return PlaceholderRenderer(
            language=self._language,
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            metadata=self._questionnaire_store.metadata,
            response_metadata=self._questionnaire_store.response_metadata,
            schema=self._schema,
            location=None,
        )

    @cached_property
    def router(self):
        return Router(
            schema=self._schema,
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            progress_store=self._questionnaire_store.progress_store,
            metadata=self._questionnaire_store.metadata,
            response_metadata=self._questionnaire_store.response_metadata,
        )

    @cached_property
    def individual_section_id(self):
        return self._schema.get_individual_response_individual_section_id()

    @cached_property
    def form(self):
        return generate_form(
            schema=self._schema,
            question_schema=self.rendered_block["question"],
            answer_store=self._questionnaire_store.answer_store,
            list_store=self._questionnaire_store.list_store,
            metadata=self._questionnaire_store.metadata,
            response_metadata=self._questionnaire_store.response_metadata,
            data=self._answers,
            form_data=self._form_data,
        )

    def get_context(self):
        return build_question_context(self.rendered_block, self.form)

    def _publish_fulfilment_request(self, mobile_number=None):
        self._check_individual_response_count()
        topic_id = current_app.config["EQ_FULFILMENT_TOPIC_ID"]
        fulfilment_request = IndividualResponseFulfilmentRequest(
            self._metadata, mobile_number
        )
        try:
            return current_app.eq["publisher"].publish(
                topic_id,
                message=fulfilment_request.message,
                fulfilment_request_transaction_id=fulfilment_request.transaction_id,
            )
        except PublicationFailed as exc:
            raise IndividualResponseFulfilmentRequestPublicationFailed from exc

    def _check_individual_response_count(self):
        if (
            self._questionnaire_store.response_metadata.get(
                "individual_response_count", 0
            )
            >= current_app.config["EQ_INDIVIDUAL_RESPONSE_LIMIT"]
        ):
            raise IndividualResponseLimitReached(
                "Individual response limit has been reached"
            )

    def _update_individual_response_count(self):
        response_metadata = self._questionnaire_store.response_metadata

        if response_metadata.get("individual_response_count"):
            response_metadata["individual_response_count"] += 1
        else:
            response_metadata["individual_response_count"] = 1

    def _update_questionnaire_store_on_publish(self):
        self._update_section_status(CompletionStatus.INDIVIDUAL_RESPONSE_REQUESTED)
        self._update_individual_response_count()
        self._questionnaire_store.save()

    def handle_get(self):
        return render_template(
            template="individual_response/interstitial",
            language=self._language,
            previous_location_url=self._get_previous_location_url(),
            next_location_url=self._get_next_location_url(),
            page_title=self.page_title(
                lazy_gettext("Cannot answer questions for others in your household")
            ),
        )

    def _get_next_location_url(self):
        list_model = self._questionnaire_store.list_store[self._list_name]

        if self._list_item_id:
            return url_for(
                ".individual_response_how",
                list_item_id=self._list_item_id,
                journey=self._request_args.get("journey"),
            )

        if len(list_model.non_primary_people) == 1:
            return url_for(
                ".individual_response_how",
                list_item_id=list_model.non_primary_people[0],
                journey="hub",
            )

        return url_for(".individual_response_who", journey="hub")

    def _get_previous_location_url(self):
        if self._request_args.get("journey") == "remove-person":
            return url_for(
                "questionnaire.block",
                list_name=self._list_name,
                list_item_id=self._list_item_id,
                block_id=self._schema.get_remove_block_id_for_list(self._list_name),
            )

        if self._list_item_id:
            individual_section_first_block_id = (
                self._schema.get_first_block_id_for_section(self.individual_section_id)
            )
            return url_for(
                "questionnaire.block",
                list_name=self._list_name,
                list_item_id=self._list_item_id,
                block_id=individual_section_first_block_id,
            )

        return url_for("questionnaire.get_questionnaire")

    def _render_block(self):
        return self.placeholder_renderer.render(
            self.block_definition, self._list_item_id
        )

    def _update_section_status(self, status):
        self._questionnaire_store.progress_store.update_section_status(
            status, self.individual_section_id, self._list_item_id
        )

    @property
    def block_definition(self):  # pragma: no cover
        raise NotImplementedError


class IndividualResponseHowHandler(IndividualResponseHandler):
    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "id": "individual-response",
            "question": {
                "type": "Question",
                "id": "individual-response-how",
                "title": {
                    "text": lazy_gettext(
                        "How would you like <em>{person_name}</em> to receive a separate census?"
                    ),
                    "placeholders": IndividualResponseHandler._person_name_placeholder(
                        self._list_name
                    ),
                },
                "description": self._build_question_description(),
                "answers": [
                    {
                        "type": "Radio",
                        "id": "individual-response-how-answer",
                        "mandatory": False,
                        "default": "Text message",
                        "options": self._build_handler_answer_options(),
                    }
                ],
            },
        }

    def _build_handler_answer_options(self):
        handler_options = [
            {
                "label": lazy_gettext("Text message"),
                "value": "Text message",
                "description": lazy_gettext(
                    "We will need their mobile number for this"
                ),
            }
        ]
        if not self.has_postal_deadline_passed:
            handler_options.append(
                {
                    "label": lazy_gettext("Post"),
                    "value": "Post",
                    "description": lazy_gettext(
                        "We can only send this to an unnamed resident at the registered household address"
                    ),
                }
            )
        return handler_options

    def _build_question_description(self):
        description = (
            lazy_gettext("It is no longer possible to receive an access code by post.")
            if self.has_postal_deadline_passed
            else lazy_gettext("Select how to send access code.")
        )
        return [
            lazy_gettext(
                "For someone to complete a separate census, we need to send them an individual access code."
            ),
            lazy_gettext(description),
        ]

    @cached_property
    def selected_option(self):
        answer_id = self.rendered_block["question"]["answers"][0]["id"]
        return self.form.get_data(answer_id)

    def handle_get(self):
        if self._request_args.get("journey") == "hub":
            if len(self._list_model.non_primary_people) == 1:
                previous_location_url = url_for(
                    "individual_response.request_individual_response",
                    journey=self._request_args.get("journey"),
                )
            else:
                previous_location_url = url_for(
                    "individual_response.individual_response_who",
                    journey=self._request_args.get("journey"),
                )
        elif self._request_args.get("journey") == "change":
            previous_location_url = url_for(
                "individual_response.individual_response_change",
                list_item_id=self._list_item_id,
            )
        elif self._request_args.get("journey") == "remove-person":
            previous_location_url = url_for(
                "individual_response.request_individual_response",
                list_item_id=self._list_item_id,
                journey="remove-person",
            )
        else:
            previous_location_url = url_for(
                "individual_response.request_individual_response",
                list_item_id=self._list_item_id,
            )

        return render_template(
            "individual_response/question",
            language=self._language,
            content=self.get_context(),
            previous_location_url=previous_location_url,
            show_contact_us_guidance=True,
            page_title=self.page_title(lazy_gettext("Send individual access code")),
        )

    def handle_post(self):
        if self.selected_option == "Post":
            return redirect(
                url_for(
                    ".individual_response_post_address_confirm",
                    list_item_id=self._list_item_id,
                    journey=self._request_args.get("journey"),
                )
            )
        return redirect(
            url_for(
                ".individual_response_text_message",
                list_item_id=self._list_item_id,
                journey=self._request_args.get("journey"),
            )
        )


class IndividualResponseChangeHandler(IndividualResponseHandler):
    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "id": "individual-response-change",
            "question": {
                "type": "Question",
                "id": "individual-response-change-question",
                "title": {
                    "text": lazy_gettext(
                        "How would you like to answer <em>{person_name_possessive}</em> questions?"
                    ),
                    "placeholders": IndividualResponseHandler._person_name_placeholder_possessive(
                        self._list_name
                    ),
                },
                "answers": [
                    {
                        "type": "Radio",
                        "id": "individual-response-change-answer",
                        "mandatory": False,
                        "default": "I would like to request a separate census for them to complete",
                        "options": [
                            {
                                "label": lazy_gettext(
                                    "I would like to request a separate census for them to complete"
                                ),
                                "value": "I would like to request a separate census for them to complete",
                            },
                            {
                                "label": lazy_gettext(
                                    "I will ask them to answer their own questions"
                                ),
                                "value": "I will ask them to answer their own questions",
                                "description": lazy_gettext(
                                    "They will need the household access code from the letter we sent you"
                                ),
                            },
                            {
                                "label": {
                                    "text": lazy_gettext(
                                        "I will answer for {person_name}"
                                    ),
                                    "placeholders": IndividualResponseHandler._person_name_placeholder(
                                        self._list_name
                                    ),
                                },
                                "value": "I will answer for {person_name}",
                            },
                        ],
                    }
                ],
            },
        }

    @cached_property
    def request_separate_census_option(self):
        return self.rendered_block["question"]["answers"][0]["options"][0]["value"]

    @cached_property
    def cancel_go_to_hub_option(self):
        return self.rendered_block["question"]["answers"][0]["options"][1]["value"]

    @cached_property
    def cancel_go_to_section_option(self):
        return self.rendered_block["question"]["answers"][0]["options"][2]["value"]

    @cached_property
    def selected_option(self):
        answer_id = self.rendered_block["question"]["answers"][0]["id"]
        return self.form.get_data(answer_id)

    def handle_get(self):
        self._answers = {
            "individual-response-change-answer": self.request_separate_census_option
        }
        return render_template(
            "individual_response/question",
            language=self._language,
            content=self.get_context(),
            previous_location_url=url_for("questionnaire.get_questionnaire"),
            show_contact_us_guidance=True,
            page_title=self.page_title(lazy_gettext("How to answer questions")),
        )

    def handle_post(self):
        if self.selected_option == self.request_separate_census_option:
            return redirect(
                url_for(
                    "individual_response.individual_response_how",
                    list_item_id=self._list_item_id,
                    journey="change",
                )
            )

        if self.selected_option == self.cancel_go_to_hub_option:
            self._update_section_completeness()
            return redirect(url_for("questionnaire.get_questionnaire"))

        if self.selected_option == self.cancel_go_to_section_option:
            self._update_section_completeness()
            individual_section_first_block_id = (
                self._schema.get_first_block_id_for_section(self.individual_section_id)
            )
            return redirect(
                url_for(
                    "questionnaire.block",
                    list_name=self._list_name,
                    list_item_id=self._list_item_id,
                    block_id=individual_section_first_block_id,
                    journey=self._request_args.get("journey"),
                )
            )

    def _update_section_completeness(self):
        if not self._questionnaire_store.progress_store.get_completed_block_ids(
            self.individual_section_id, self._list_item_id
        ):
            status = CompletionStatus.NOT_STARTED
        else:
            routing_path = self.router.routing_path(
                self.individual_section_id, self._list_item_id
            )
            status = (
                CompletionStatus.COMPLETED
                if self.router.is_path_complete(routing_path)
                else CompletionStatus.IN_PROGRESS
            )
        self._update_section_status(status)
        if self._questionnaire_store.progress_store.is_dirty:
            self._questionnaire_store.save()


class IndividualResponsePostAddressConfirmHandler(IndividualResponseHandler):
    def __init__(self, **kwargs):
        if self.has_postal_deadline_passed:
            raise IndividualResponsePostalDeadlinePast
        super().__init__(**kwargs)

    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "question": {
                "type": "Question",
                "id": "individual-response-post-confirm",
                "title": {
                    "text": lazy_gettext(
                        "Do you want to send an individual access code for {person_name} by post?"
                    ),
                    "placeholders": IndividualResponseHandler._person_name_placeholder(
                        self._list_name
                    ),
                },
                "description": [
                    lazy_gettext(
                        "A letter with an individual access code will be sent to your registered household address"
                    )
                ],
                "guidance": {
                    "contents": [
                        {
                            "description": lazy_gettext(
                                "The letter will be addressed to <strong>Individual Resident</strong> instead of the name provided"
                            )
                        }
                    ]
                },
                "answers": [
                    {
                        "type": "Radio",
                        "id": "individual-response-post-confirm-answer",
                        "mandatory": True,
                        "options": [
                            {
                                "label": lazy_gettext(
                                    "Yes, send the access code by post"
                                ),
                                "value": "Yes, send the access code by post",
                            },
                            {
                                "label": lazy_gettext("No, send it another way"),
                                "value": "No, send it another way",
                            },
                        ],
                    }
                ],
            },
        }

    @cached_property
    def answer_id(self):
        return self.rendered_block["question"]["answers"][0]["id"]

    @cached_property
    def confirm_option(self):
        return self.rendered_block["question"]["answers"][0]["options"][0]["value"]

    @cached_property
    def selected_option(self):
        return self.form.get_data(self.answer_id)

    def handle_get(self):
        previous_location_url = url_for(
            "individual_response.individual_response_how",
            list_item_id=self._list_item_id,
            journey=self._request_args.get("journey"),
        )

        return render_template(
            "individual_response/question",
            language=self._language,
            content=self.get_context(),
            previous_location_url=previous_location_url,
            page_title=self.page_title(lazy_gettext("Confirm address")),
        )

    def handle_post(self):
        if self.selected_option == self.confirm_option:
            self._publish_fulfilment_request()
            self._update_questionnaire_store_on_publish()

            return redirect(
                url_for(
                    "individual_response.individual_response_post_address_confirmation",
                    journey=self._request_args.get("journey"),
                )
            )

        return redirect(
            url_for(
                "individual_response.individual_response_how",
                list_item_id=self._list_item_id,
                journey=self._request_args.get("journey"),
            )
        )


class IndividualResponseWhoHandler(IndividualResponseHandler):
    def __init__(self, schema, questionnaire_store, language, request_args, form_data):
        self._list_name = schema.get_individual_response_list()
        list_model = questionnaire_store.list_store[self._list_name]
        self.non_primary_people_names = {}

        if list_model.same_name_items:
            name_answer_ids = ["first-name", "middle-names", "last-name"]
        else:
            name_answer_ids = ["first-name", "last-name"]

        for list_item_id in list_model.non_primary_people:
            name_answers = questionnaire_store.answer_store.get_answers_by_answer_id(
                name_answer_ids, list_item_id=list_item_id
            )
            name = " ".join(name_answer.value for name_answer in name_answers)
            self.non_primary_people_names[list_item_id] = name

        super().__init__(
            schema,
            questionnaire_store,
            language,
            request_args,
            form_data,
            request_args.get("list_item_id"),
        )

    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "page_title": lazy_gettext("Separate Census"),
            "question": {
                "type": "Question",
                "id": "individual-response-who",
                "title": lazy_gettext(
                    "Who do you need to request a separate census for?"
                ),
                "answers": [
                    {
                        "type": "Radio",
                        "id": "individual-response-who-answer",
                        "mandatory": True,
                        "options": [
                            {"label": name, "value": list_item_id}
                            for list_item_id, name in self.non_primary_people_names.items()
                        ],
                    }
                ],
            },
        }

    @cached_property
    def selected_option(self):
        answer_id = self.rendered_block["question"]["answers"][0]["id"]
        return self.form.get_data(answer_id)

    def handle_get(self):
        if len(self.non_primary_people_names) > 1:
            previous_location_url = url_for(
                "individual_response.request_individual_response",
                journey=self._request_args.get("journey"),
            )

            return render_template(
                "individual_response/question",
                language=self._language,
                content=self.get_context(),
                previous_location_url=previous_location_url,
                page_title=self.page_title(lazy_gettext("Separate Census")),
            )

        raise NotFound

    def handle_post(self):
        return redirect(
            url_for(
                ".individual_response_how",
                journey=self._request_args.get("journey"),
                list_item_id=self.selected_option,
            )
        )


class IndividualResponseTextHandler(IndividualResponseHandler):
    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "question": {
                "type": "Question",
                "id": "individual-response-enter-number",
                "title": {
                    "text": lazy_gettext(
                        "What is <em>{person_name_possessive}</em> mobile number?"
                    ),
                    "placeholders": IndividualResponseHandler._person_name_placeholder_possessive(
                        self._list_name
                    ),
                },
                "answers": [
                    {
                        "type": "MobileNumber",
                        "id": "individual-response-enter-number-answer",
                        "mandatory": True,
                        "label": lazy_gettext("UK mobile number"),
                        "description": lazy_gettext(
                            "This will not be stored and only used once to send the access code"
                        ),
                    }
                ],
            },
        }

    @cached_property
    def answer_id(self):
        return self.rendered_block["question"]["answers"][0]["id"]

    @cached_property
    def mobile_number(self):
        return self.form.get_data(self.answer_id)

    def handle_get(self):
        if "mobile_number" in self._request_args:
            mobile_number = url_safe_serializer().loads(
                self._request_args["mobile_number"]
            )
            self._answers = {"individual-response-enter-number-answer": mobile_number}
        previous_location_url = url_for(
            "individual_response.individual_response_how",
            list_item_id=self._list_item_id,
            journey=self._request_args.get("journey"),
        )

        return render_template(
            "individual_response/question",
            language=self._language,
            content=self.get_context(),
            previous_location_url=previous_location_url,
            page_title=self.page_title(lazy_gettext("Mobile number")),
        )

    def handle_post(self):
        mobile_number = url_safe_serializer().dumps(self.mobile_number)

        return redirect(
            url_for(
                "individual_response.individual_response_text_message_confirm",
                list_item_id=self._list_item_id,
                journey=self._request_args.get("journey"),
                mobile_number=mobile_number,
            )
        )


class IndividualResponseTextConfirmHandler(IndividualResponseHandler):
    def __init__(
        self,
        schema,
        questionnaire_store,
        language,
        request_args,
        form_data,
        list_item_id,
    ):
        try:
            self.mobile_number = url_safe_serializer().loads(
                request_args["mobile_number"]
            )
        except BadSignature as exc:
            raise BadRequest from exc

        super().__init__(
            schema,
            questionnaire_store,
            language,
            request_args,
            form_data,
            list_item_id,
        )

    @cached_property
    def block_definition(self) -> Mapping:
        return {
            "type": "IndividualResponse",
            "question": {
                "type": "Question",
                "id": "individual-response-text-confirm",
                "title": lazy_gettext("Is this mobile number correct?"),
                "description": [self.mobile_number],
                "answers": [
                    {
                        "type": "Radio",
                        "id": "individual-response-text-confirm-answer",
                        "mandatory": True,
                        "options": [
                            {
                                "label": lazy_gettext("Yes, send the text"),
                                "value": "Yes, send the text",
                            },
                            {
                                "label": lazy_gettext("No, I need to change it"),
                                "value": "No, I need to change it",
                            },
                        ],
                    }
                ],
            },
        }

    @cached_property
    def answer_id(self):
        return self.rendered_block["question"]["answers"][0]["id"]

    @cached_property
    def confirm_option(self):
        return self.rendered_block["question"]["answers"][0]["options"][0]["value"]

    @cached_property
    def selected_option(self):
        return self.form.get_data(self.answer_id)

    def handle_get(self):
        previous_location_url = url_for(
            "individual_response.individual_response_text_message",
            list_item_id=self._list_item_id,
            journey=self._request_args.get("journey"),
            mobile_number=self._request_args.get("mobile_number"),
        )

        return render_template(
            "individual_response/question",
            language=self._language,
            content=self.get_context(),
            previous_location_url=previous_location_url,
            page_title=self.page_title(lazy_gettext("Confirm mobile number")),
        )

    def handle_post(self):
        if self.selected_option == self.confirm_option:
            self._publish_fulfilment_request(self.mobile_number)
            self._update_questionnaire_store_on_publish()

            return redirect(
                url_for(
                    "individual_response.individual_response_text_message_confirmation",
                    journey=self._request_args.get("journey"),
                    mobile_number=self._request_args.get("mobile_number"),
                )
            )

        return redirect(
            url_for(
                "individual_response.individual_response_text_message",
                list_item_id=self._list_item_id,
                journey=self._request_args.get("journey"),
                mobile_number=self._request_args.get("mobile_number"),
            )
        )


class IndividualResponseFulfilmentRequest(FulfilmentRequest):
    def __init__(self, metadata: Mapping, mobile_number: Optional[str] = None):
        self._metadata = metadata
        self._mobile_number = mobile_number
        self._fulfilment_type = "sms" if self._mobile_number else "postal"

    def _get_individual_case_id_mapping(self) -> Mapping:
        return (
            {}
            if self._metadata.get("case_type") in ["SPG", "CE"]
            else {"individualCaseId": str(uuid4())}
        )

    def _get_contact_mapping(self) -> Mapping:
        return (
            {"telNo": sanitise_mobile_number(self._mobile_number)}
            if self._mobile_number
            else {}
        )

    def _get_fulfilment_code(self) -> str:
        fulfilment_codes = {
            "sms": {
                GB_ENG_REGION_CODE: "UACITA1",
                GB_WLS_REGION_CODE: "UACITA2B",
                GB_NIR_REGION_CODE: "UACITA4",
            },
            "postal": {
                GB_ENG_REGION_CODE: "P_UAC_UACIPA1",
                GB_WLS_REGION_CODE: "P_UAC_UACIPA2B",
                GB_NIR_REGION_CODE: "P_UAC_UACIPA4",
            },
        }
        region_code = self._metadata["region_code"]
        return fulfilment_codes[self._fulfilment_type][region_code]

    def _payload(self) -> Mapping:
        return {
            "fulfilmentRequest": {
                **self._get_individual_case_id_mapping(),
                "fulfilmentCode": self._get_fulfilment_code(),
                "caseId": self._metadata["case_id"],
                "contact": self._get_contact_mapping(),
            }
        }
