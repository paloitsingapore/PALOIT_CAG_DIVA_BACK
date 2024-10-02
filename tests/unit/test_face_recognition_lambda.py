import os
import json
from moto import mock_dynamodb
import boto3
from assisted_wayfinding_backend.lambda_functions.face_recognition import index

@mock_dynamodb
def test_face_recognition_lambda_handler():
    # Set up mock DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table_name = 'TestPassengerTable'
    
    # Create a mock table
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'passengerId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'passengerId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    # Set environment variable
    os.environ['DYNAMODB_TABLE_NAME'] = table_name

    try:
        # Test event
        event = {}
        context = {}

        # Call the handler function
        response = index.handler(event, context)

        # Assert the response
        assert response['statusCode'] == 200
        assert f'Using table: {table_name}' in response['body']
    finally:
        # Clean up
        del os.environ['DYNAMODB_TABLE_NAME']
        table.delete()