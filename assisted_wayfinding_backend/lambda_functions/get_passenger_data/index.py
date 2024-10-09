import json
import os
import logging
from decimal import Decimal

import boto3
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
    logger.info("Get Passenger Data Lambda function invoked")
    logger.info(f"Event: {json.dumps(event)}")

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    collection_id = os.environ.get("REKOGNITION_COLLECTION_ID")

    if not table_name or not collection_id:
        logger.error("Missing required environment variables")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing required environment variables"}),
        }

    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Extract personaId from the event
        persona_id = event.get('personaId')
        
        if not persona_id:
            logger.error("Missing 'personaId' in the event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'personaId' in the event"}),
            }

        # Query DynamoDB
        response = table.get_item(Key={'userId': persona_id})
        logger.info(f"DynamoDB get_item response: {json.dumps(response, default=decimal_default)}")

        if 'Item' in response:
            user_data = response['Item']
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
                        "message": "Passenger data retrieved",
                        "passengerData": user_data,
                    },
                    default=decimal_default
                ),
            }
        else:
            logger.info(f"No passenger data found for personaId: {persona_id}")
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"message": f"No passenger data found for personaId: {persona_id}"}),
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