import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from assisted_wayfinding_backend.lambda_functions.manual_user_lookup.index import (
    handler,
)


@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "test-table")


@pytest.fixture
def mock_context():
    return MagicMock()


@pytest.fixture
def mock_dynamodb_table():
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


def test_successful_lookup(mock_environment, mock_context, mock_dynamodb_table):
    event = {
        "queryStringParameters": {
            "name": "John Doe",
            "dateOfBirth": "1990-01-01",
            "flightNumber": "SQ123",
        }
    }

    mock_dynamodb_table.scan.return_value = {
        "Items": [
            {
                "userId": "user_john_doe",
                "name": "John Doe",
                "dateOfBirth": "1990-01-01",
                "next_flight_id": "SQ123",
            }
        ]
    }

    response = handler(event, mock_context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "userData" in body
    assert body["userData"]["name"] == "John Doe"


def test_user_not_found(mock_environment, mock_context, mock_dynamodb_table):
    event = {
        "queryStringParameters": {
            "name": "Jane Doe",
            "dateOfBirth": "1995-05-05",
            "flightNumber": "SQ456",
        }
    }

    mock_dynamodb_table.scan.return_value = {"Items": []}

    response = handler(event, mock_context)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"] == "User not found"


def test_missing_required_fields(mock_environment, mock_context):
    event = {"queryStringParameters": {"name": "John Doe"}}

    response = handler(event, mock_context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"] == "Missing required fields"


def test_dynamodb_client_error(mock_environment, mock_context, mock_dynamodb_table):
    event = {
        "queryStringParameters": {
            "name": "John Doe",
            "dateOfBirth": "1990-01-01",
            "flightNumber": "SQ123",
        }
    }

    mock_dynamodb_table.scan.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "DynamoDB error"}},
        "Scan",
    )

    response = handler(event, mock_context)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert "Internal server error" in body["error"]


def test_unexpected_exception(mock_environment, mock_context):
    event = {
        "queryStringParameters": {
            "name": "John Doe",
            "dateOfBirth": "1990-01-01",
            "flightNumber": "SQ123",
        }
    }

    with patch("boto3.resource", side_effect=Exception("Unexpected error")):
        response = handler(event, mock_context)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert "Internal server error" in body["error"]


def test_empty_query_parameters(mock_environment, mock_context):
    event = {"queryStringParameters": None}

    response = handler(event, mock_context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"] == "Missing required fields"


def test_partial_query_parameters(mock_environment, mock_context):
    event = {"queryStringParameters": {"name": "John Doe", "dateOfBirth": "1990-01-01"}}

    response = handler(event, mock_context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"] == "Missing required fields"


def test_url_encoded_name(mock_environment, mock_context, mock_dynamodb_table):
    event = {
        "queryStringParameters": {
            "name": "John%20Doe",
            "dateOfBirth": "1990-01-01",
            "flightNumber": "SQ123",
        }
    }

    mock_dynamodb_table.scan.return_value = {
        "Items": [
            {
                "userId": "user_john_doe",
                "name": "John Doe",
                "dateOfBirth": "1990-01-01",
                "next_flight_id": "SQ123",
            }
        ]
    }

    response = handler(event, mock_context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "userData" in body
    assert body["userData"]["name"] == "John Doe"
