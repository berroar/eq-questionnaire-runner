from flask import Blueprint, g, redirect, request, url_for
from flask_babel import lazy_gettext
from flask_login import current_user, login_required
from itsdangerous import BadSignature
from structlog import get_logger
from werkzeug.exceptions import BadRequest

from app.authentication.no_questionnaire_state_exception import (
    NoQuestionnaireStateException,
)
from app.globals import get_metadata, get_questionnaire_store, get_session_store
from app.helpers import url_safe_serializer
from app.helpers.language_helper import handle_language
from app.helpers.schema_helpers import with_schema
from app.helpers.session_helpers import with_questionnaire_store
from app.helpers.template_helpers import render_template
from app.utilities.schema import load_schema_from_session_data
from app.views.handlers.individual_response import (
    IndividualResponseChangeHandler,
    IndividualResponseHandler,
    IndividualResponseHowHandler,
    IndividualResponsePostAddressConfirmHandler,
    IndividualResponsePostalDeadlinePast,
    IndividualResponseTextConfirmHandler,
    IndividualResponseTextHandler,
    IndividualResponseWhoHandler,
)

logger = get_logger()

individual_response_blueprint = Blueprint(
    name="individual_response", import_name=__name__, url_prefix="/individual-response/"
)


@login_required
@individual_response_blueprint.before_request
def before_individual_response_request():
    if request.method == "OPTIONS":
        return None

    metadata = get_metadata(current_user)
    if not metadata:
        raise NoQuestionnaireStateException(401)

    questionnaire_store = get_questionnaire_store(
        current_user.user_id, current_user.user_ik
    )

    if questionnaire_store.submitted_at:
        return redirect(url_for("post_submission.get_thank_you"))

    logger.bind(
        tx_id=metadata["tx_id"],
        schema_name=metadata["schema_name"],
        ce_id=metadata["collection_exercise_sid"],
    )

    logger.info(
        "individual-response request", method=request.method, url_path=request.full_path
    )

    handle_language()

    session_store = get_session_store()
    # pylint: disable=assigning-non-slot
    g.schema = load_schema_from_session_data(session_store.session_data)


@individual_response_blueprint.route("/", methods=["GET"])
@with_questionnaire_store
@with_schema
def request_individual_response(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code
    list_item_id = request.args.get("list_item_id")

    individual_response_handler = IndividualResponseHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    return individual_response_handler.handle_get()


@individual_response_blueprint.route("/<list_item_id>/how", methods=["GET", "POST"])
@with_questionnaire_store
@with_schema
def individual_response_how(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code

    individual_response_handler = IndividualResponseHowHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route("/<list_item_id>/change", methods=["GET", "POST"])
@with_questionnaire_store
@with_schema
def individual_response_change(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseChangeHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route(
    "/<list_item_id>/post/confirm-address", methods=["GET", "POST"]
)
@with_questionnaire_store
@with_schema
def individual_response_post_address_confirm(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code

    try:
        individual_response_handler = IndividualResponsePostAddressConfirmHandler(
            schema=schema,
            questionnaire_store=questionnaire_store,
            language=language_code,
            request_args=request.args,
            form_data=request.form,
            list_item_id=list_item_id,
        )
    except IndividualResponsePostalDeadlinePast:
        return redirect(url_for(".individual_response_how", list_item_id=list_item_id))

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route("/post/confirmation", methods=["GET", "POST"])
@with_questionnaire_store
@with_schema
def individual_response_post_address_confirmation(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=None,
    )

    if request.method == "POST":
        return redirect(url_for("questionnaire.get_questionnaire"))

    return render_template(
        template="individual_response/confirmation-post",
        display_address=questionnaire_store.metadata.get("display_address"),
        page_title=individual_response_handler.page_title(
            lazy_gettext("An individual access code has been sent by post")
        ),
    )


@individual_response_blueprint.route("/who", methods=["GET", "POST"])
@with_questionnaire_store
@with_schema
def individual_response_who(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code

    individual_response_handler = IndividualResponseWhoHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
    )

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route(
    "/<list_item_id>/text/enter-number", methods=["GET", "POST"]
)
@with_questionnaire_store
@with_schema
def individual_response_text_message(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseTextHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route(
    "/<list_item_id>/text/confirm-number", methods=["GET", "POST"]
)
@with_questionnaire_store
@with_schema
def individual_response_text_message_confirm(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseTextConfirmHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "POST" and individual_response_handler.form.validate():
        return individual_response_handler.handle_post()

    return individual_response_handler.handle_get()


@individual_response_blueprint.route("/text/confirmation", methods=["GET", "POST"])
@with_questionnaire_store
@with_schema
def individual_response_text_message_confirmation(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        request_args=request.args,
        form_data=request.form,
        list_item_id=None,
    )

    if request.method == "POST":
        return redirect(url_for("questionnaire.get_questionnaire"))

    try:
        mobile_number = url_safe_serializer().loads(request.args["mobile_number"])
    except BadSignature as exc:
        raise BadRequest from exc

    return render_template(
        template="individual_response/confirmation-text-message",
        mobile_number=mobile_number,
        page_title=individual_response_handler.page_title(
            lazy_gettext("An individual access code has been sent by text")
        ),
    )
