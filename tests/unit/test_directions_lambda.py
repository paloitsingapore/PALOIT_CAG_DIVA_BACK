import json
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from assisted_wayfinding_backend.lambda_functions.directions.index import handler


# Sample event for testing
@pytest.fixture
def valid_event():
    return {"pathParameters": {"from": "checkin", "to": "gate_b4"}}


@pytest.fixture
def context():
    return {}


# Mocking the S3 client
@pytest.fixture
def s3_client_mock():
    with patch(
        "assisted_wayfinding_backend.lambda_functions.directions.index.s3_client"
    ) as mock:
        yield mock


# Mocking environment variables
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("MAP_IMAGE_BUCKET", "assistedwayfinding-map-images-dev")


def test_successful_direction_retrieval(valid_event, context, s3_client_mock, mock_env):
    # Mock S3 head_object to return True indicating the object exists
    s3_client_mock.head_object.return_value = {}

    response = handler(valid_event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["from"] == "checkin"
    assert body["to"] == "gate_b4"
    assert "map_image" in body
    assert (
        body["map_image"]
        == "https://assistedwayfinding-map-images-dev.s3.amazonaws.com/maps/checkin_to_gate_b4.png"
    )
    assert "direction_steps" in body
    assert len(body["direction_steps"]) == 5  # 4 steps + arrival step


def test_map_image_not_found(valid_event, context, s3_client_mock, mock_env):
    # Mock S3 head_object to raise a 404 error indicating the object does not exist
    s3_client_mock.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )

    response = handler(valid_event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["map_image"] == ""


def test_map_image_bucket_missing(valid_event, context, s3_client_mock, monkeypatch):
    # Remove the MAP_IMAGE_BUCKET environment variable
    monkeypatch.delenv("MAP_IMAGE_BUCKET", raising=False)

    response = handler(valid_event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["map_image"] == ""
    assert "direction_steps" in body


def test_s3_access_denied(valid_event, context, s3_client_mock, mock_env):
    # Mock S3 head_object to raise a 403 error indicating access is denied
    s3_client_mock.head_object.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadObject"
    )

    response = handler(valid_event, context)

    assert response["statusCode"] == 200  # Still returns 200, but map_image is empty
    body = json.loads(response["body"])
    assert body["map_image"] == ""


def test_missing_path_parameters(context, s3_client_mock, mock_env):
    # Event without pathParameters
    event = {"pathParameters": {}}

    response = handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Bad Request"
    assert "Missing required parameter" in body["message"]


def test_additional_locations(valid_event, context, s3_client_mock, mock_env):
    # Update the event to use different locations
    event = {"pathParameters": {"from": "kiosk_1", "to": "gate_b4"}}

    # Mock S3 head_object to return True indicating the object exists
    s3_client_mock.head_object.return_value = {}

    response = handler(event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["from"] == "kiosk_1"
    assert body["to"] == "gate_b4"
    assert "map_image" in body
    assert (
        body["map_image"]
        == "https://assistedwayfinding-map-images-dev.s3.amazonaws.com/maps/kiosk_1_to_gate_b4.png"
    )
    assert "direction_steps" in body
    assert len(body["direction_steps"]) >= 4  # Depending on random steps
