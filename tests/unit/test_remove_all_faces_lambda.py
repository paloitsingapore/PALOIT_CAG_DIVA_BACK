import json
import unittest
from unittest.mock import MagicMock, patch
import os
from botocore.exceptions import ClientError, ParamValidationError

from assisted_wayfinding_backend.lambda_functions.remove_all_faces.index import handler


class TestRemoveAllFaces(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "DYNAMODB_TABLE_NAME": "test-table",
                "REKOGNITION_COLLECTION_ID": "test-collection",
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_remove_all_faces_success(self, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_rekognition = mock_client.return_value

        mock_rekognition.list_faces.return_value = {
            "Faces": [{"FaceId": "face1"}, {"FaceId": "face2"}]
        }
        mock_rekognition.delete_faces.return_value = {}
        mock_table.scan.return_value = {
            "Items": [{"userId": "user1"}, {"userId": "user2"}]
        }

        response = handler({}, {})

        self.assertEqual(response["statusCode"], 200)
        self.assertIn(
            "All faces and user data removed successfully",
            json.loads(response["body"])["message"],
        )

        mock_rekognition.list_faces.assert_called_once_with(
            CollectionId="test-collection"
        )
        mock_rekognition.delete_faces.assert_called_once_with(
            CollectionId="test-collection", FaceIds=["face1", "face2"]
        )
        mock_table.scan.assert_called_once()
        self.assertEqual(
            mock_table.batch_writer.return_value.__enter__.return_value.delete_item.call_count,
            2,
        )

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_remove_all_faces_no_faces(self, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_rekognition = mock_client.return_value

        mock_rekognition.list_faces.return_value = {"Faces": []}
        mock_table.scan.return_value = {"Items": []}

        response = handler({}, {})

        self.assertEqual(response["statusCode"], 200)
        self.assertIn(
            "All faces and user data removed successfully",
            json.loads(response["body"])["message"],
        )

        mock_rekognition.list_faces.assert_called_once_with(
            CollectionId="test-collection"
        )
        mock_rekognition.delete_faces.assert_not_called()
        mock_table.scan.assert_called_once()
        mock_table.batch_writer.assert_not_called()

    @patch("boto3.client")
    def test_remove_all_faces_error(self, mock_client):
        mock_client.return_value.list_faces.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
            "ListFaces",
        )

        response = handler({}, {})

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("error", json.loads(response["body"]))

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_remove_all_faces_with_faces_but_no_items(self, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_rekognition = mock_client.return_value

        mock_rekognition.list_faces.return_value = {
            "Faces": [{"FaceId": "face1"}, {"FaceId": "face2"}]
        }
        mock_table.scan.return_value = {"Items": []}

        response = handler({}, {})

        self.assertEqual(response["statusCode"], 200)
        self.assertIn(
            "All faces and user data removed successfully",
            json.loads(response["body"])["message"],
        )

        mock_rekognition.list_faces.assert_called_once_with(
            CollectionId="test-collection"
        )
        mock_rekognition.delete_faces.assert_called_once_with(
            CollectionId="test-collection", FaceIds=["face1", "face2"]
        )
        mock_table.scan.assert_called_once()
        mock_table.batch_writer.assert_not_called()

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_remove_all_faces_rekognition_error(self, mock_client, mock_resource):
        mock_rekognition = mock_client.return_value
        mock_rekognition.list_faces.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "Invalid collection id"}},
            "ListFaces"
        )

        response = handler({}, {})
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("error", json.loads(response["body"]))
        self.assertIn("Invalid collection id", json.loads(response["body"])["error"])

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_remove_all_faces_dynamodb_error(self, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_rekognition = mock_client.return_value

        mock_rekognition.list_faces.return_value = {"Faces": []}
