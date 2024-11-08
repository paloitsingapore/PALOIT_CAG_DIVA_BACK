import base64
import json
import os
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper function to handle Decimal serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    logger.info("Face Recognition Lambda function invoked")
    logger.info(f"Event: {json.dumps(event)}")

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    collection_id = os.environ.get("REKOGNITION_COLLECTION_ID")
    bucket_name = os.environ.get("S3_BUCKET_NAME")

    if not table_name or not collection_id or not bucket_name:
        logger.error("Missing required environment variables")
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
        if "image" not in body:
            logger.error("Missing 'image' in request body")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'image' in request body"}),
            }
        image_bytes = base64.b64decode(body["image"])

        # Upload image to S3 temporarily
        s3_key = f"temp_images/{context.aws_request_id}.jpg"
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=image_bytes)
        logger.info(f"Uploaded temporary image to S3: {s3_key}")

        # Search for matching faces in Rekognition
        search_response = rekognition.search_faces_by_image(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": bucket_name, "Name": s3_key}},
            MaxFaces=1,
            FaceMatchThreshold=70,  # Adjust this threshold as needed
        )
        logger.info(f"Rekognition search response: {json.dumps(search_response)}")

        # Delete the temporary image
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info(f"Deleted temporary image from S3: {s3_key}")

        if search_response["FaceMatches"]:
            face_match = search_response["FaceMatches"][0]
            face_id = face_match["Face"]["FaceId"]
            similarity = face_match["Similarity"]
            logger.info(f"Face match found. FaceId: {face_id}, Similarity: {similarity}")

            # Query DynamoDB
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("faceIds").contains(face_id)
            )
            logger.info(f"DynamoDB scan response: {json.dumps(response, default=decimal_default)}")

            if response["Items"]:
                user_data = response["Items"][0]
                logger.info(f"User data found: {json.dumps(user_data, default=decimal_default)}")
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                    },
                    "body": json.dumps(
                        {
                            "message": "Face recognized",
                            "passengerData": user_data,
                        },
                        default=decimal_default
                    ),
                }

            logger.info("No passenger data found for the recognized face")
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"message": "No passenger data found for the recognized face"}),
            }
        else:
            logger.info("No matching face found")
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"message": "No matching face found"}),
            }

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except ClientError as e:
        logger.error(f"AWS client error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"error": str(e)}),
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"error": "An unexpected error occurred"}),
        }

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