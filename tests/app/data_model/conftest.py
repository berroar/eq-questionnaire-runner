from datetime import datetime, timedelta, timezone

import pytest

from app.data_models.answer_store import Answer
from app.data_models.progress_store import CompletionStatus
from app.data_models.session_store import SessionStore
from app.storage import storage_encryption


@pytest.fixture
def basic_answer_store(answer_store):

    answer_store.add_or_update(
        Answer(answer_id="answer1", value=10, list_item_id="abc123")
    )
    answer_store.add_or_update(
        Answer(answer_id="answer2", value=20, list_item_id="xyz987")
    )
    answer_store.add_or_update(
        Answer(answer_id="another-answer2", value=25, list_item_id="xyz987")
    )

    answer_store.add_or_update(Answer(answer_id="answer3", value=30))
    answer_store.add_or_update(Answer(answer_id="another-answer3", value=35))

    answer_store.add_or_update(Answer(answer_id="answer4", value="<p>abc123</p>"))
    answer_store.add_or_update(
        Answer(answer_id="answer5", value=["<p>abc123</p>", "some value"])
    )
    answer_store.add_or_update(
        Answer(
            answer_id="answer6", value={"item1": "<p>abc123</p>", "item2": "some value"}
        )
    )

    answer_store.add_or_update(Answer(answer_id="to-escape", value="'Twenty Five'"))
    return answer_store


@pytest.fixture
def relationship_answer_store(answer_store):

    answer_store.add_or_update(
        Answer(
            answer_id="relationship-answer",
            value=[
                {
                    "list_item_id": "abc123",
                    "to_list_item_id": "xyz987",
                    "relationship": "Husband or Wife",
                },
                {
                    "list_item_id": "abc123",
                    "to_list_item_id": "123abc",
                    "relationship": "Son or Daughter",
                },
                {
                    "list_item_id": "xyz987",
                    "to_list_item_id": "123abc",
                    "relationship": "Son or Daughter",
                },
            ],
        )
    )

    return answer_store


@pytest.fixture
def store_to_serialize(answer_store):

    answer_store.add_or_update(
        Answer(answer_id="answer1", value=10, list_item_id="abc123")
    )
    answer_store.add_or_update(
        Answer(answer_id="answer2", value=20, list_item_id="xyz987")
    )
    answer_store.add_or_update(Answer(answer_id="answer3", value=30))

    return answer_store


@pytest.fixture
def basic_input():
    return {
        "METADATA": {"test": True},
        "ANSWERS": [{"answer_id": "test", "value": "test"}],
        "LISTS": [],
        "PROGRESS": [
            {
                "section_id": "a-test-section",
                "list_item_id": "abc123",
                "status": CompletionStatus.COMPLETED,
                "block_ids": ["a-test-block"],
            }
        ],
        "RESPONSE_METADATA": {"test-meta": "test"},
    }


@pytest.fixture
def questionnaire_store(mocker):
    store = mocker.MagicMock()

    def get_user_data():
        """Fake get_user_data implementation for storage"""
        return (store.input_data, "ce_sid", 1, None)

    def set_output_data(data, collection_exercise_sid, submitted_at, expires_at):
        store.output_data = data
        store.collection_exercise_sid = collection_exercise_sid
        store.submitted_at = submitted_at
        store.expires_at = expires_at

    # Storage class mocking
    store.storage = mocker.MagicMock()
    store.storage.get_user_data = mocker.MagicMock(side_effect=get_user_data)
    store.storage.save = mocker.MagicMock(side_effect=set_output_data)

    store.input_data = "{}"
    store.output_data = ""
    store.collection_exercise_sid = None
    store.submitted_at = None
    store.output_version = None
    store.expires_at = None

    return store


@pytest.fixture
def app_session_store(app, mocker, session_data):
    app.permanent_session_lifetime = timedelta(seconds=1)
    store = mocker.MagicMock()
    store.session_store = SessionStore("user_ik", "pepper")
    store.expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=3)
    store.session_data = session_data
    return store


@pytest.fixture
def app_session_store_encoded(mocker, session_data):
    store = mocker.MagicMock()
    store.user_id = "user_id"
    store.user_ik = "user_ik"
    store.pepper = "pepper"
    store.session_id = "session_id"
    store.expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=3)
    store.session_data = session_data

    # pylint: disable=protected-access
    store.key = storage_encryption.StorageEncryption._generate_key(
        store.user_id, store.user_ik, store.pepper
    )
    return store
