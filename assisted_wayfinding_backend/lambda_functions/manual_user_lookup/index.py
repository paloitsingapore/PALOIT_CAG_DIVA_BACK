import json
import os
from urllib.parse import unquote_plus

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError


def handler(event, context):
    print("Manual User Lookup Lambda function invoked")
    print(f"Event: {json.dumps(event)}")  # Log the entire event for debugging

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")

    # Initialize DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Check if the input is from query parameters, JSON body, or empty (test invocation)
        if event.get("queryStringParameters"):
            # Extract data from the event query parameters
            query_params = event.get("queryStringParameters", {})
            name = unquote_plus(query_params.get("name", ""))
            date_of_birth = query_params.get("dateOfBirth", "")
            flight_number = query_params.get("flightNumber", "")
        elif event.get("body"):
            # Extract data from JSON body
            body = json.loads(event["body"])
            name = body.get("name", "")
            date_of_birth = body.get("dateOfBirth", "")
            flight_number = body.get("flightNumber", "")
        else:
            # Handle empty input (like in API Gateway Test Console)
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Missing input data",
                        "message": "Please provide name, dateOfBirth, and flightNumber as query parameters or in the request body.",
                    }
                ),
            }

        if not name or not date_of_birth or not flight_number:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Missing required fields",
                        "message": "Please provide name, dateOfBirth, and flightNumber.",
                    }
                ),
            }

        # Query DynamoDB table
        response = table.scan(
            FilterExpression=Attr("name").eq(name)
            & Attr("dateOfBirth").eq(date_of_birth)
            & Attr("next_flight_id").eq(flight_number)
        )

        if response["Items"]:
            user_data = response["Items"][0]
            return {
                "statusCode": 200,
                "body": json.dumps({"userData": user_data}),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User not found"}),
            }

    except ClientError as e:
        print(f"Error querying DynamoDB: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
