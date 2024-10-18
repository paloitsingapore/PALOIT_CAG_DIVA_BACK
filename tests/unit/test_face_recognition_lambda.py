# tests/unit/test_face_recognition_lambda.py

import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from assisted_wayfinding_backend.lambda_functions.face_recognition.index import (
    handler as recognition_handler,
)


@pytest.fixture
def mock_environment(monkeypatch):
    """Fixture to mock environment variables."""
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "test-table")
    monkeypatch.setenv("REKOGNITION_COLLECTION_ID", "test-collection")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")


@pytest.fixture
def test_images():
    """Fixture to load and provide test images."""
    with open("tests/unit/images/test_fake_person.jpg", "rb") as f:
        fake_person_image = base64.b64encode(f.read()).decode("utf-8")
    with open("tests/unit/images/test_no_face.jpg", "rb") as f:
        no_face_image = base64.b64encode(f.read()).decode("utf-8")
    return {"fake_person_image": fake_person_image, "no_face_image": no_face_image}


@pytest.fixture
def mock_context():
    """Fixture to create a mock AWS Lambda context."""
    context = MagicMock()
    context.aws_request_id = "test-request-id"
    return context


@pytest.fixture
def mock_boto3_clients():
    """Fixture to mock boto3 clients and resources."""
    with patch("boto3.resource") as mock_resource, patch("boto3.client") as mock_client:
        yield mock_resource, mock_client


def test_face_recognition_success(
    mock_environment, mock_boto3_clients, mock_context, test_images
):
    """
    Test successful face recognition where a face is matched and passenger data is retrieved.
    """
    mock_resource, mock_client = mock_boto3_clients
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    mock_rekognition = mock_client.return_value
    mock_s3 = mock_client.return_value

    event = {"body": json.dumps({"image": test_images["fake_person_image"]})}

    mock_rekognition.search_faces_by_image.return_value = {
        "FaceMatches": [
            {
                "Face": {"FaceId": "test-face-id"},
                "Similarity": 99.0,
            }
        ]
    }

    mock_table.scan.return_value = {
        "Items": [
            {
                "userId": "P12345",
                "name": "fake person",
                "faceIds": ["test-face-id"],
            }
        ]
    }

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "Face recognized" in body["message"]
    assert body["passengerData"]["name"] == "fake person"


def test_face_recognition_no_face(
    mock_environment, mock_boto3_clients, mock_context, test_images
):
    """
    Test face recognition when no face is detected in the image.
    """
    mock_resource, mock_client = mock_boto3_clients
    mock_rekognition = mock_client.return_value

    event = {"body": json.dumps({"image": test_images["no_face_image"]})}

    mock_rekognition.search_faces_by_image.return_value = {"FaceMatches": []}

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 404
    assert "No matching face found" in json.loads(response["body"])["message"]


def test_face_recognition_no_passenger_data(
    mock_environment, mock_boto3_clients, mock_context, test_images
):
    """
    Test behavior when a face is matched but no passenger data is found.
    """
    mock_resource, mock_client = mock_boto3_clients
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    mock_rekognition = mock_client.return_value

    event = {"body": json.dumps({"image": test_images["fake_person_image"]})}

    mock_rekognition.search_faces_by_image.return_value = {
        "FaceMatches": [
            {
                "Face": {"FaceId": "test-face-id"},
                "Similarity": 99.0,
            }
        ]
    }

    mock_table.scan.return_value = {"Items": []}

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 404
    assert (
        "No passenger data found for the recognized face"
        in json.loads(response["body"])["message"]
    )


def test_face_recognition_dynamodb_error(
    mock_environment, mock_boto3_clients, mock_context, test_images
):
    """Test behavior when DynamoDB query fails."""
    mock_resource, mock_client = mock_boto3_clients
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    mock_rekognition = mock_client.return_value

    event = {"body": json.dumps({"image": test_images["fake_person_image"]})}

    mock_rekognition.search_faces_by_image.return_value = {
        "FaceMatches": [
            {
                "Face": {"FaceId": "test-face-id"},
                "Similarity": 99.0,
            }
        ]
    }

    mock_table.scan.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "Scan",
    )

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 500
    assert "Table not found" in json.loads(response["body"])["error"]


def test_face_recognition_missing_env_vars():
    """Test behavior when environment variables are missing."""
    with patch.dict("os.environ", {}, clear=True):
        event = {"body": json.dumps({"image": "dummy_image"})}
        response = recognition_handler(event, MagicMock())

    assert response["statusCode"] == 500
    assert (
        "Missing required environment variables"
        in json.loads(response["body"])["error"]
    )


def test_face_recognition_invalid_input(mock_environment, mock_context):
    """Test behavior with invalid input (missing image)."""
    event = {"body": json.dumps({})}  # Missing 'image' key

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 400
    assert "Missing 'image' in request body" in json.loads(response["body"])["error"]


def test_face_recognition_invalid_json(mock_environment, mock_context):
    """Test behavior with invalid JSON in request body."""
    event = {"body": "invalid json"}

    response = recognition_handler(event, mock_context)

    assert response["statusCode"] == 400
    assert "Invalid JSON in request body" in json.loads(response["body"])["error"]
