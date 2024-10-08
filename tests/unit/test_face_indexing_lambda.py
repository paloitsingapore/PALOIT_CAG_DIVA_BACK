import base64
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from assisted_wayfinding_backend.lambda_functions.face_indexing.index import handler


@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "test-table")
    monkeypatch.setenv("REKOGNITION_COLLECTION_ID", "test-collection")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")


@pytest.fixture
def mock_context():
    return MagicMock()


@pytest.fixture
def test_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    with open(
        os.path.join(project_root, "tests/unit/images", "test_fake_person.jpg"), "rb"
    ) as f:
        fake_person_image = base64.b64encode(f.read()).decode("utf-8")

    with open(
        os.path.join(project_root, "tests/unit/images", "test_no_face.jpg"), "rb"
    ) as f:
        no_face_image = base64.b64encode(f.read()).decode("utf-8")

    return {"fake_person_image": fake_person_image, "no_face_image": no_face_image}


@pytest.fixture
def sample_event(test_images):
    return {
        "body": json.dumps(
            {
                "userId": "test-user-id",
                "images": [test_images["fake_person_image"]],
                "passengerData": {"name": "fake person", "passengerId": "P12345"},
            }
        )
    }


@pytest.fixture
def mock_aws_clients():
    with patch("boto3.resource") as mock_resource, patch("boto3.client") as mock_client:
        yield mock_resource, mock_client


def test_face_indexing_success(
    mock_environment, mock_context, sample_event, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    mock_s3 = mock_client.return_value
    mock_rekognition = mock_client.return_value

    mock_rekognition.index_faces.return_value = {
        "FaceRecords": [{"Face": {"FaceId": "test-face-id"}}]
    }

    response = handler(sample_event, mock_context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "User created and faces indexed successfully" in body["message"]
    assert body["userId"] == "test-user-id"
    assert body["faceIds"] == ["test-face-id"]

    mock_s3.put_object.assert_called_once()
    mock_rekognition.index_faces.assert_called_once()
    mock_table.put_item.assert_called_once()


def test_face_indexing_no_faces_detected(
    mock_environment, mock_context, test_images, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients
    mock_rekognition = mock_client.return_value

    event = {
        "body": json.dumps(
            {
                "userId": "test-user-id",
                "images": [test_images["no_face_image"]],
                "passengerData": {"name": "No Face", "passengerId": "P67890"},
            }
        )
    }

    mock_rekognition.index_faces.return_value = {"FaceRecords": []}

    response = handler(event, mock_context)

    assert response["statusCode"] == 400
    assert (
        "No faces detected in the provided images"
        in json.loads(response["body"])["error"]
    )


def test_face_indexing_missing_env_vars(mock_context, sample_event):
    with patch.dict("os.environ", clear=True):
        response = handler(sample_event, mock_context)

    assert response["statusCode"] == 500
    assert (
        "Missing required environment variables"
        in json.loads(response["body"])["error"]
    )


def test_face_indexing_s3_error(
    mock_environment, mock_context, sample_event, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients
    mock_s3 = mock_client.return_value

    mock_s3.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
    )

    response = handler(sample_event, mock_context)

    assert response["statusCode"] == 500
    assert "AccessDenied" in json.loads(response["body"])["error"]


def test_face_indexing_rekognition_error(
    mock_environment, mock_context, sample_event, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients
    mock_rekognition = mock_client.return_value

    mock_rekognition.index_faces.side_effect = ClientError(
        {
            "Error": {
                "Code": "InvalidParameterException",
                "Message": "Invalid image format",
            }
        },
        "IndexFaces",
    )

    response = handler(sample_event, mock_context)

    assert response["statusCode"] == 500
    assert "Invalid image format" in json.loads(response["body"])["error"]


def test_face_indexing_dynamodb_error(
    mock_environment, mock_context, sample_event, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    mock_rekognition = mock_client.return_value

    mock_rekognition.index_faces.return_value = {
        "FaceRecords": [{"Face": {"FaceId": "test-face-id"}}]
    }
    mock_table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "PutItem",
    )

    response = handler(sample_event, mock_context)

    assert response["statusCode"] == 500
    assert "Table not found" in json.loads(response["body"])["error"]


def test_face_indexing_invalid_input(mock_environment, mock_context):
    event = {"body": json.dumps({})}  # Missing required fields

    response = handler(event, mock_context)

    assert response["statusCode"] == 500
    assert "An unexpected error occurred" in json.loads(response["body"])["error"]


def test_face_indexing_unexpected_error(
    mock_environment, mock_context, sample_event, mock_aws_clients
):
    mock_resource, mock_client = mock_aws_clients

    # Mock boto3.resource to raise an unexpected exception
    mock_resource.side_effect = Exception("Unexpected error")

    response = handler(sample_event, mock_context)

    assert response["statusCode"] == 500
    assert "An unexpected error occurred" in json.loads(response["body"])["error"]
