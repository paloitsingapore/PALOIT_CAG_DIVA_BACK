import base64
import json
import os

import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    print("Face Indexing Lambda function invoked")

    try:
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

        # Extract data from the event
        body = json.loads(event["body"])
        user_id = body["userId"]
        images = body["images"]
        passenger_data = body["passengerData"]

        face_ids = []
        image_urls = []
        for i, image in enumerate(images):
            # Decode and upload image to S3
            image_bytes = base64.b64decode(image)
            s3_key = f"user_photos/{user_id}_face_{i}.jpg"
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=image_bytes)

            # Store the S3 URL
            image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            image_urls.append(image_url)

            # Index the face in Rekognition
            index_response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={"S3Object": {"Bucket": bucket_name, "Name": s3_key}},
                ExternalImageId=user_id,  # Associate face with user_id
                DetectionAttributes=["ALL"],
            )

            if index_response["FaceRecords"]:
                face_ids.append(index_response["FaceRecords"][0]["Face"]["FaceId"])

        # Optionally, handle if no faces are detected
        if not face_ids:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "No faces detected in the provided images."}
                ),
            }

        # Store user data in DynamoDB
        table.put_item(
            Item={
                "userId": user_id,
                "faceIds": face_ids,
                "imageUrls": image_urls,
                "rekognition_collection_id": collection_id,
                **passenger_data,
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "User created and faces indexed successfully",
                    "userId": user_id,
                    "faceIds": face_ids,
                }
            ),
        }

    except ClientError as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "An unexpected error occurred."}),
        }
