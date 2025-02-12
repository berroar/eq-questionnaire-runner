import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from app.data_models import QuestionnaireStore
from app.data_models.session_data import SessionData
from app.data_models.session_store import SessionStore
from app.questionnaire import QuestionnaireSchema

time_to_freeze = datetime.now(timezone.utc).replace(second=0, microsecond=0)
tx_id = str(uuid.uuid4())
response_id = "1234567890123456"
period_str = "2016-01-01"
period_id = "2016-02-01"
ref_p_start_date = "2016-02-02"
ref_p_end_date = "2016-03-03"
ru_ref = "432423423423"
ru_name = "ru_name"
user_id = "789473423"
schema_name = "1_0000"
feedback_count = 1
display_address = "68 Abingdon Road, Goathill"
form_type = "I"
collection_exercise_sid = "ce_sid"
case_id = "case_id"
survey_id = "021"
data_version = "0.0.1"
feedback_type = "Feedback type"
feedback_text = "Feedback text"
feedback_type_question_category = "Feedback type question category"
started_at = str(datetime.now(tz=timezone.utc).isoformat())
language_code = "cy"
case_type = "I"
channel = "H"
case_ref = "1000000000000001"
region_code = "GB_WLS"


@pytest.fixture
@freeze_time(time_to_freeze)
def session_data():
    return SessionData(
        tx_id="123",
        schema_name="some_schema_name",
        display_address="68 Abingdon Road, Goathill",
        period_str=None,
        language_code="cy",
        launch_language_code="en",
        survey_url=None,
        ru_name=None,
        ru_ref=None,
        submitted_at=datetime.now(timezone.utc).isoformat(),
        response_id="321",
        case_id="789",
    )


@pytest.fixture
def confirmation_email_fulfilment_schema():
    return QuestionnaireSchema(
        {
            "form_type": "H",
            "region_code": "GB-WLS",
            "submission": {"confirmation_email": True},
        }
    )


@pytest.fixture
def language():
    return "en"


@pytest.fixture
def schema():
    return QuestionnaireSchema({"post_submission": {"view_response": True}})


@pytest.fixture
def storage():
    return Mock()


def set_storage_data(
    storage_,
    raw_data="{}",
    version=1,
    submitted_at=None,
):
    storage_.get_user_data = Mock(
        return_value=(raw_data, version, collection_exercise_sid, submitted_at)
    )


@pytest.fixture
def session_data_feedback():
    return SessionData(
        tx_id=tx_id,
        schema_name=schema_name,
        response_id=response_id,
        period_str=period_str,
        language_code=language_code,
        launch_language_code=None,
        survey_url=None,
        ru_name=ru_name,
        ru_ref=ru_ref,
        case_id=case_id,
        feedback_count=feedback_count,
    )


@pytest.fixture
def schema_feedback():
    return QuestionnaireSchema({"survey_id": survey_id, "data_version": data_version})


@pytest.fixture
def metadata():
    return {
        "tx_id": tx_id,
        "user_id": user_id,
        "schema_name": schema_name,
        "collection_exercise_sid": collection_exercise_sid,
        "period_id": period_id,
        "period_str": period_str,
        "ref_p_start_date": ref_p_start_date,
        "ref_p_end_date": ref_p_end_date,
        "ru_ref": ru_ref,
        "response_id": response_id,
        "form_type": form_type,
        "display_address": display_address,
        "case_type": case_type,
        "channel": channel,
        "case_ref": case_ref,
        "region_code": region_code,
    }


@pytest.fixture
def response_metadata():
    return {
        "started_at": started_at,
    }


@pytest.fixture
def submission_payload_expires_at():
    return datetime.now(timezone.utc) + timedelta(seconds=5)


@pytest.fixture
def submission_payload_session_data():
    return SessionData(
        tx_id="tx_id",
        schema_name="schema_name",
        response_id="response_id",
        period_str="period_str",
        language_code="cy",
        launch_language_code="en",
        survey_url=None,
        ru_name="ru_name",
        ru_ref="ru_ref",
        case_id="0123456789000000",
    )


@pytest.fixture
def submission_payload_session_store(
    submission_payload_session_data,
    submission_payload_expires_at,
):  # pylint: disable=redefined-outer-name
    return SessionStore("user_ik", "pepper", "eq_session_id").create(
        "eq_session_id",
        "user_id",
        submission_payload_session_data,
        submission_payload_expires_at,
    )


@pytest.fixture
def mock_questionnaire_store(mocker):
    storage_ = mocker.Mock()
    storage_.get_user_data = mocker.Mock(return_value=("{}", "ce_id", 1, None))
    questionnaire_store = QuestionnaireStore(storage_)
    questionnaire_store.metadata = {"tx_id": "tx_id", "case_id": "case_id"}
    return questionnaire_store
