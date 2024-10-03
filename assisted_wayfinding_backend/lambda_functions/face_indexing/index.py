import base64
import json
import os

import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    print("Face Indexing Lambda function invoked")

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    collection_id = os.environ.get("REKOGNITION_COLLECTION_ID")
    bucket_name = os.environ.get("S3_BUCKET_NAME")

    if not table_name or not collection_id or not bucket_name:
        missing_vars = []
        if not table_name:
            missing_vars.append("DYNAMODB_TABLE_NAME")
        if not collection_id:
            missing_vars.append("REKOGNITION_COLLECTION_ID")
        if not bucket_name:
            missing_vars.append("S3_BUCKET_NAME")

        error_message = (
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_message}),
        }

    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb")
    rekognition = boto3.client("rekognition")
    s3 = boto3.client("s3")
    table = dynamodb.Table(table_name)

    try:
        # Extract base64-encoded image and passenger data from the event
        body = json.loads(event["body"])
        image_bytes = base64.b64decode(body["image"])
        passenger_data = body["passengerData"]

        # Upload image to S3
        s3_key = f"passenger_photos/{passenger_data['passengerId']}.jpg"
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=image_bytes)

        # Index the face in Rekognition
        index_response = rekognition.index_faces(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": bucket_name, "Name": s3_key}},
            ExternalImageId=passenger_data["passengerId"],
            DetectionAttributes=["ALL"],
        )

        if index_response["FaceRecords"]:
            face_id = index_response["FaceRecords"][0]["Face"]["FaceId"]

            # Store passenger data in DynamoDB
            passenger_data["faceId"] = face_id
            passenger_data["s3Key"] = s3_key
            table.put_item(Item=passenger_data)

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {"message": "Face indexed successfully", "faceId": face_id}
                ),
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No face detected in the image"}),
            }

    except ClientError as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
