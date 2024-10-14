import json
import logging
import os
import random
import traceback

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        from_location = event["pathParameters"]["from"]
        to_location = event["pathParameters"]["to"]

        logger.info(f"Retrieving directions from {from_location} to {to_location}")

        if from_location == "checkin" and to_location == "gate_b4":
            direction_steps = [
                {"step": f"Leave {from_location} and turn right", "duration": "1 min"},
                {"step": "Continue up escalator", "duration": "1 min"},
                {"step": "Turn right", "duration": "8 min"},
                {"step": "Turn left", "duration": "3 min"},
                {"step": "Arrive at gate B4", "duration": "0 min"},
            ]
        else:
            possible_steps = [
                "Turn right",
                "Turn left",
                "Go straight",
                "Take the escalator",
                "Take the elevator",
                "Follow the signs",
                "Pass through security",
                "Walk along the corridor",
                "Cross the bridge",
                "Go down the stairs",
            ]

            num_steps = random.randint(3, 7)
            direction_steps = []

            for _ in range(num_steps):
                step = random.choice(possible_steps)
                duration = f"{random.randint(1, 10)} min"
                direction_steps.append({"step": step, "duration": duration})

            direction_steps.append(
                {"step": f"Arrive at {to_location}", "duration": "1 min"}
            )

        map_image = ""
        try:
            bucket_name = os.environ.get("MAP_IMAGE_BUCKET")
            logger.info(f"MAP_IMAGE_BUCKET: {bucket_name}")

            if bucket_name:
                s3_key = f"maps/{from_location}_to_{to_location}.png"
                try:
                    s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                    map_image = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                    logger.info(f"Map image URL: {map_image}")
                except ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        logger.warning(f"Map image not found: {s3_key}")
                    else:
                        logger.error(f"Error checking for map image: {str(e)}")
            else:
                logger.warning("MAP_IMAGE_BUCKET environment variable not set")
        except Exception as e:
            logger.error(f"Error processing map image: {str(e)}")

        response = {
            "from": from_location,
            "to": to_location,
            "map_image": map_image,
            "direction_steps": direction_steps,
        }

        logger.info(f"Returning response: {json.dumps(response)}")
        return {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    except KeyError as e:
        logger.error(f"Missing required parameter: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "Bad Request",
                    "message": f"Missing required parameter: {str(e)}",
                    "details": {"event": event, "missing_key": str(e)},
                }
            ),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "Internal Server Error",
                    "message": str(e),
                    "details": {
                        "event": event,
                        "exception_type": type(e).__name__,
                        "stacktrace": traceback.format_exc(),
                    },
                }
            ),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
