# pylint: disable=redefined-outer-name
import uuid

import pytest


@pytest.fixture
def fake_metadata_runner():
    """Generate the set of claims required for runner to function"""
    return {
        "tx_id": str(uuid.uuid4()),
        "jti": str(uuid.uuid4()),
        "schema_name": "2_a",
        "ru_ref": "2016-04-04",
        "collection_exercise_sid": "test-sid",
        "response_id": str(uuid.uuid4()),
        "account_service_url": "https://ras.ons.gov.uk",
        "case_id": str(uuid.uuid4()),
    }


@pytest.fixture
def fake_business_metadata_runner(fake_metadata_runner):
    """Generate a set of claims required for runner using business parameters instead of schema_name"""
    del fake_metadata_runner["schema_name"]

    fake_metadata_runner["eq_id"] = "mbs"
    fake_metadata_runner["form_type"] = "0253"

    return fake_metadata_runner


@pytest.fixture
def fake_metadata_full(fake_metadata_runner):
    """Generate a fake set of claims
    These claims should represent all claims known to runner, including common questionnaire
    level claims.
    """
    fake_questionnaire_claims = {
        "user_id": "1",
        "period_id": "3",
        "period_str": "2016-01-01",
        "ref_p_start_date": "2016-02-02",
        "ref_p_end_date": "2016-03-03",
        "ru_name": "Apple",
        "return_by": "2016-07-07",
        "case_ref": "1000000000000001",
        "case_id": str(uuid.uuid4()),
    }

    return dict(fake_metadata_runner, **fake_questionnaire_claims)


@pytest.fixture
def fake_questionnaire_metadata_requirements_full():
    return [
        {"name": "user_id", "type": "string"},
        {"name": "period_id", "type": "string"},
        {"name": "period_str", "type": "string"},
        {"name": "ref_p_start_date", "type": "string"},
        {"name": "ref_p_end_date", "type": "string"},
        {"name": "account_service_url", "type": "url", "optional": True},
    ]
