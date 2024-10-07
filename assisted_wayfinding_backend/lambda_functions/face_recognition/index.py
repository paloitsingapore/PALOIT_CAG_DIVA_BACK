import base64
import json
import os

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def handler(event, context):
    print("Face Recognition Lambda function invoked")

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    collection_id = os.environ.get("REKOGNITION_COLLECTION_ID")
    bucket_name = os.environ.get("S3_BUCKET_NAME")

    if not table_name or not collection_id or not bucket_name:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing required environment variables"}),
        }

    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb")
    rekognition = boto3.client("rekognition")
    s3 = boto3.client("s3")
    table = dynamodb.Table(table_name)

    try:
        # Extract base64-encoded image from the event
        body = json.loads(event["body"])
        image_bytes = base64.b64decode(body["image"])

        # Upload image to S3 temporarily
        s3_key = f"temp_images/{context.aws_request_id}.jpg"
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=image_bytes)

        # Search for matching faces in Rekognition
        search_response = rekognition.search_faces_by_image(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": bucket_name, "Name": s3_key}},
            MaxFaces=1,
            FaceMatchThreshold=70,  # Adjust this threshold as needed
        )

        # Delete the temporary image
        s3.delete_object(Bucket=bucket_name, Key=s3_key)

        if search_response["FaceMatches"]:
            face_match = search_response["FaceMatches"][0]
            face_id = face_match["Face"]["FaceId"]
            similarity = face_match["Similarity"]

            # Query DynamoDB
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("faceIds").contains(
                    face_id
                )
            )
            if response["Items"]:
                user_data = response["Items"][0]
                return {
                    "statusCode": 200,
                    "body": json.dumps(
                        {
                            "message": "Face recognized",
                            "passengerData": user_data,
                        }
                    ),
                }

            return {
                "statusCode": 404,
                "body": json.dumps(
                    {"message": "No passenger data found for the recognized face"}
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "No matching face found"}),
            }

    except ClientError as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def get_passenger_id_from_face_id(face_id, table):
    try:
        # Query the table using a secondary index on faceId
        response = table.query(
            IndexName="faceId-index",  # You'll need to create this secondary index
            KeyConditionExpression=Key("faceId").eq(face_id),
        )

        if response["Items"]:
            return response["Items"][0]["passengerId"]
        else:
            return None
    except ClientError as e:
        print(f"Error querying DynamoDB: {str(e)}")
        return None
