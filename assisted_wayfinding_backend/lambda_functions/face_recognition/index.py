import os
import boto3

def handler(event, context):
    print('Face Recognition Lambda function invoked')
    
    # Get the DynamoDB table name from environment variables
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    
    if not table_name:
        return {
            'statusCode': 500,
            'body': 'DynamoDB table name not provided'
        }
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    print(f"DynamoDB table name: {table_name}")
    
    return {
        'statusCode': 200,
        'body': f'Face Recognition function executed successfully! Using table: {table_name}'
    }