import json
import os

import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    print("Remove All Faces Lambda function invoked")

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    collection_id = os.environ.get("REKOGNITION_COLLECTION_ID")

    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb")
    rekognition = boto3.client("rekognition")
    table = dynamodb.Table(table_name)

    try:
        # Remove all faces from Rekognition collection
        response = rekognition.list_faces(CollectionId=collection_id)
        face_ids = [face["FaceId"] for face in response["Faces"]]

        if face_ids:
            rekognition.delete_faces(CollectionId=collection_id, FaceIds=face_ids)

        # Remove all items from DynamoDB table
        scan = table.scan()
        items = scan["Items"]

        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={"userId": item["userId"]})

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "All faces and user data removed successfully"}
            ),
        }

    except ClientError as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
