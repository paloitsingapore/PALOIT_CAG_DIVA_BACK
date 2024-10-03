import base64
import json
import os
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_dynamodb, mock_rekognition

from assisted_wayfinding_backend.lambda_functions.face_recognition import index


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_table(aws_credentials):
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "TestPassengerTable"
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "faceId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "faceId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Insert test data
        table.put_item(
            Item={
                "faceId": "test_face_id",
                "passengerId": "test_passenger_id",
                "name": "John Doe",
                "passportNumber": "AB1234567",
            }
        )

        yield table_name


@pytest.fixture
def rekognition_collection(aws_credentials):
    with mock_rekognition():
        rekognition = boto3.client("rekognition", region_name="us-east-1")
        collection_id = "TestFaceCollection"
        rekognition.create_collection(CollectionId=collection_id)
        yield collection_id


def test_face_recognition_lambda_handler(dynamodb_table, rekognition_collection):
    # Set environment variables
    os.environ["DYNAMODB_TABLE_NAME"] = dynamodb_table
    os.environ["REKOGNITION_COLLECTION_ID"] = rekognition_collection

    # Mock the Rekognition search_faces_by_image method
    with patch("boto3.client") as mock_boto3_client:
        mock_rekognition = MagicMock()
        mock_rekognition.search_faces_by_image.return_value = {
            "FaceMatches": [
                {
                    "Face": {"FaceId": "test_face_id", "Confidence": 99.9},
                    "Similarity": 99.9,
                }
            ]
        }
        mock_boto3_client.return_value = mock_rekognition

        # Test event
        event = {
            "body": json.dumps(
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            )
        }
        context = {}

        # Call the handler function
        response = index.handler(event, context)

        # Assert the response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["message"] == "Face recognized"
        assert body["passengerData"]["passengerId"] == "test_passenger_id"
        assert body["passengerData"]["name"] == "John Doe"
        assert body["passengerData"]["passportNumber"] == "AB1234567"


def test_face_recognition_no_match(dynamodb_table, rekognition_collection):
    # Set environment variables
    os.environ["DYNAMODB_TABLE_NAME"] = dynamodb_table
    os.environ["REKOGNITION_COLLECTION_ID"] = rekognition_collection

    # Mock the Rekognition search_faces_by_image method
    with patch("boto3.client") as mock_boto3_client:
        mock_rekognition = MagicMock()
        mock_rekognition.search_faces_by_image.return_value = {"FaceMatches": []}
        mock_boto3_client.return_value = mock_rekognition

        # Test event
        event = {
            "body": json.dumps(
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            )
        }
        context = {}

        # Call the handler function
        response = index.handler(event, context)

        # Assert the response
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["message"] == "No matching face found"


def test_face_recognition_error(dynamodb_table, rekognition_collection):
    # Set environment variables
    os.environ["DYNAMODB_TABLE_NAME"] = dynamodb_table
    os.environ["REKOGNITION_COLLECTION_ID"] = rekognition_collection

    # Mock the Rekognition search_faces_by_image method to raise an exception
    with patch("boto3.client") as mock_boto3_client:
        mock_rekognition = MagicMock()
        mock_rekognition.search_faces_by_image.side_effect = Exception(
            "Rekognition error"
        )
        mock_boto3_client.return_value = mock_rekognition

        # Test event
        event = {
            "body": json.dumps(
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            )
        }
        context = {}

        # Call the handler function
        response = index.handler(event, context)

        # Assert the response
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


# Clean up environment variables after tests
def teardown_module(module):
    os.environ.pop("DYNAMODB_TABLE_NAME", None)
    os.environ.pop("REKOGNITION_COLLECTION_ID", None)
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    os.environ.pop("AWS_SECURITY_TOKEN", None)
    os.environ.pop("AWS_SESSION_TOKEN", None)
    os.environ.pop("AWS_DEFAULT_REGION", None)
