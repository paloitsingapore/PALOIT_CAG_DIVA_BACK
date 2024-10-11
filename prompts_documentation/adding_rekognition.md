### API Endpoints Documentation

#### 1. Index Face

**Endpoint:** `/index`

**Method:** POST

**Description:** This endpoint is used to index a new face in the Rekognition collection and store associated passenger data.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string",
  "passengerData": {
    "name": "string",
    "passengerId": "string",
    "changi_app_user_id": "string",
    "next_flight_id": "string",
    "has_lounge_access": boolean,
    "accessibility_needs": boolean
  }
}
```

**Response:**
- Success (200 OK):
  ```json
  {
    "faceId": "string",
    "message": "Face indexed successfully"
  }
  ```
- Error (500 Internal Server Error):
  ```json
  {
    "error": "Error message"
  }
  ```

**Implementation Details:**
The indexing process involves the following steps:
1. Decode the base64 image.
2. Upload the image to an S3 bucket.
3. Index the face using Amazon Rekognition.
4. Store passenger data in DynamoDB.

For the detailed implementation, refer to:

```9:90:assisted_wayfinding_backend/lambda_functions/face_indexing/index.py
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

            # Store the mapping in DynamoDB
            table.put_item(
                Item={
                    "faceId": face_id,
                    "image_url": f"https://{bucket_name}.s3.amazonaws.com/{s3_key}",
                    "rekognition_collection_id": collection_id,
                    "passengerId": passenger_data["passengerId"],
                    "name": passenger_data["name"],
                    "changi_app_user_id": passenger_data["changi_app_user_id"],
                    "next_flight_id": passenger_data["next_flight_id"],
                    "has_lounge_access": passenger_data["has_lounge_access"],
                    "accessibility_needs": passenger_data["accessibility_needs"],
                }
            )

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
```


#### 2. Recognize Face

**Endpoint:** `/recognize`

**Method:** POST

**Description:** This endpoint is used to recognize a face from a given image and retrieve associated passenger data.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response:**
- Success (200 OK):
  ```json
  {
    "name": "string",
    "passengerId": "string",
    "changi_app_user_id": "string",
    "next_flight_id": "string",
    "has_lounge_access": boolean,
    "accessibility_needs": boolean
  }
  ```
- Not Found (404 Not Found):
  ```json
  {
    "message": "No matching face found"
  }
  ```
- Error (500 Internal Server Error):
  ```json
  {
    "error": "Error message"
  }
  ```

**Implementation Details:**
The recognition process involves the following steps:
1. Decode the base64 image.
2. Search for matching faces using Amazon Rekognition.
3. Retrieve associated passenger data from DynamoDB.

For the detailed implementation, refer to:

```10:85:assisted_wayfinding_backend/lambda_functions/face_recognition/index.py
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
            face_id = search_response["FaceMatches"][0]["Face"]["FaceId"]

            # Get passengerId using the new function
            passenger_id = get_passenger_id_from_face_id(face_id, table)

            if passenger_id:
                response = table.get_item(Key={"passengerId": passenger_id})

                if "Item" in response:
                    passenger_data = response["Item"]
                    return {
                        "statusCode": 200,
                        "body": json.dumps(
                            {
                                "message": "Face recognized",
                                "passengerData": passenger_data,
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
```


These endpoints are designed to work with the AWS services including S3, Rekognition, and DynamoDB. Ensure that the necessary permissions and configurations are set up as described in the deployment instructions.







As a Software Architect with 10 years of experience, I will outline the steps needed to integrate facial recognition into your application using AWS services and the AWS Cloud Development Kit (CDK).

Overview

To add facial recognition to your app, we’ll utilize the following AWS services:

	•	AWS Rekognition: For facial detection and recognition.
	•	AWS Lambda: For serverless backend processing.
	•	Amazon API Gateway: To expose RESTful APIs to your frontend.
	•	AWS IAM: To manage permissions securely.

We’ll also update your AWS CDK stack (cdk.json) to include these resources.

Steps

1. Set Up AWS Rekognition

	•	Create a Rekognition Collection: This is a container for storing facial feature vectors.
	•	Use AWS SDK or AWS CLI to create a collection.
	•	Example CLI command:

    ``` 
    aws rekognition create-collection --collection-id "YourCollectionId"
    ```

2. Update AWS CDK Stack

	•	Modify cdk.json: Ensure your CDK app is configured to include the new resources.
	•	Add Rekognition Permissions:
	•	Update your IAM roles to allow Rekognition actions like DetectFaces, IndexFaces, and SearchFacesByImage.
	•	Define Lambda Functions:
	•	Create Lambda functions for indexing and searching faces.
	•	Set Up API Gateway:
	•	Create REST endpoints to interact with your Lambda functions.

3. Develop Lambda Functions

	•	Face Indexing Function:
	•	Triggered when a new user registers or uploads a photo.
	•	Uses IndexFaces API to store facial data in the collection.
	•	Face Search Function:
	•	Accepts an input image and searches for matching faces using SearchFacesByImage.
	•	Implement Error Handling:
	•	Ensure robust error handling and logging for debugging.

4. Integrate Frontend with Backend

	•	Capture User Image:
	•	Update the app UI to capture images (e.g., via camera or file upload).
	•	Call API Endpoints:
	•	Use HTTPS requests to send images to your backend APIs.
	•	Handle Responses:
	•	Display appropriate messages based on recognition results.

5. Security and Privacy

	•	User Consent:
	•	Obtain explicit consent for facial data usage.
	•	Update your privacy policy accordingly.
	•	Data Encryption:
	•	Use AWS KMS to encrypt data at rest and in transit.
	•	Compliance:
	•	Ensure compliance with GDPR, CCPA, and other regulations.

6. Testing

	•	Unit Tests:
	•	Write tests for Lambda functions using frameworks like PyTest or unittest.
	•	Integration Tests:
	•	Test the end-to-end flow between the frontend and backend.
	•	Performance Testing:
	•	Monitor latency and optimize as needed.

7. Deploy and Monitor

	•	Deploy with CDK:
	•	Use cdk deploy to push changes to AWS.
	•	Set Up Monitoring:
	•	Use CloudWatch to monitor Lambda functions and API Gateway.
	•	Logging:
	•	Implement structured logging for easier troubleshooting.

Additional Considerations

Scalability

	•	Lambda Concurrency Limits:
	•	Configure reserved concurrency if needed.
	•	API Gateway Throttling:
	•	Set up throttling to prevent abuse.

Cost Management

	•	Monitor Usage:
	•	Use AWS Cost Explorer to keep track of expenses.
	•	Optimize Resources:
	•	Right-size your Lambdas and consider provisioned concurrency if beneficial.

Fallback Mechanisms

	•	Alternative Authentication:
	•	Provide options like password login or OTP in case facial recognition fails.

Summary

By following these steps, you’ll be able to integrate facial recognition into your app effectively. This will enhance user experience by providing quick and secure authentication.

Note: Always prioritize user privacy and comply with all relevant regulations when handling biometric data.

Feel free to reach out if you need further clarification on any of these steps.







Certainly! I'll guide you through the process of implementing these steps in your CDK application. We'll update your existing code to incorporate AWS Rekognition and set up the necessary resources.


``` config.py
def get_config(env: str) -> Dict[str, Any]:
    base_config = {
        'project_name': 'AssistedWayfinding',
        'lambda_runtime': 'python3.9',
        'lambda_handler': 'index.handler',
        'environment': env,
        'rekognition_collection_id': 'AssistedWayfindingFaces',
    }

    env_specific_config = {
        'dev': {
            'lambda_memory_size': 128,
            'lambda_timeout': 30,
            'face_recognition': {
                'min_confidence': 70,
            }
        },
        'prod': {
            'lambda_memory_size': 256,
            'lambda_timeout': 60,
            'face_recognition': {
                'min_confidence': 90,
            }
        }
    }

    return {**base_config, **env_specific_config.get(env, env_specific_config['dev'])}

    ```

2. Now, let's update the LambdaStack to include Rekognition permissions and create a new Lambda function for indexing faces:

```
from aws_cdk import (
    NestedStack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
)
from constructs import Construct

class LambdaStack(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda function for face recognition
        self.face_recognition_function = _lambda.Function(
            self, "FaceRecognitionFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("assisted_wayfinding_backend/lambda_functions/face_recognition"),
            memory_size=config['lambda_memory_size'],
            timeout=Duration.seconds(config['lambda_timeout']),
            environment={
                "DYNAMODB_TABLE_NAME": f"{config['project_name']}-PassengerTable-{config['environment']}",
                "REKOGNITION_COLLECTION_ID": config['rekognition_collection_id'],
                "PROJECT_NAME": config['project_name'],
                "ENVIRONMENT": config['environment'],
            }
        )

        # Create a Lambda function for indexing faces
        self.face_indexing_function = _lambda.Function(
            self, "FaceIndexingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("assisted_wayfinding_backend/lambda_functions/face_indexing"),
            memory_size=config['lambda_memory_size'],
            timeout=Duration.seconds(config['lambda_timeout']),
            environment={
                "DYNAMODB_TABLE_NAME": f"{config['project_name']}-PassengerTable-{config['environment']}",
                "REKOGNITION_COLLECTION_ID": config['rekognition_collection_id'],
                "PROJECT_NAME": config['project_name'],
                "ENVIRONMENT": config['environment'],
            }
        )

        # Add necessary permissions for DynamoDB, Rekognition, and other AWS services
        rekognition_policy = iam.PolicyStatement(
            actions=[
                "rekognition:SearchFacesByImage",
                "rekognition:DetectFaces",
                "rekognition:IndexFaces",
            ],
            resources=["*"]  # TODO: Restrict this to specific Rekognition collection ARN in production
        )

        self.face_recognition_function.add_to_role_policy(rekognition_policy)
        self.face_indexing_function.add_to_role_policy(rekognition_policy)

        dynamodb_policy = iam.PolicyStatement(
            actions=[
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=["*"]  # TODO: Restrict this to specific table ARNs in production
        )

        self.face_recognition_function.add_to_role_policy(dynamodb_policy)
        self.face_indexing_function.add_to_role_policy(dynamodb_policy)

        ```


Create a new file for the face indexing Lambda function:


```
import os
import boto3
import json
from botocore.exceptions import ClientError

def handler(event, context):
    print('Face Indexing Lambda function invoked')
    
    # Get environment variables
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    collection_id = os.environ.get('REKOGNITION_COLLECTION_ID')
    
    if not table_name or not collection_id:
        return {
            'statusCode': 500,
            'body': 'Missing required environment variables'
        }
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb')
    rekognition = boto3.client('rekognition')
    table = dynamodb.Table(table_name)
    
    try:
        # Extract base64-encoded image and passenger data from the event
        body = json.loads(event['body'])
        image_bytes = body['image'].encode('utf-8')
        passenger_data = body['passengerData']
        
        # Index the face in Rekognition
        index_response = rekognition.index_faces(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            ExternalImageId=passenger_data['passengerId'],
            DetectionAttributes=['ALL']
        )
        
        if index_response['FaceRecords']:
            face_id = index_response['FaceRecords'][0]['Face']['FaceId']
            
            # Store passenger data in DynamoDB
            passenger_data['faceId'] = face_id
            table.put_item(Item=passenger_data)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Face indexed successfully',
                    'faceId': face_id
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No face detected in the image'
                })
            }
    
    except ClientError as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

```

4. Update the main stack to include API Gateway:

```
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
)
from constructs import Construct
from .nested_stacks.lambda_stack import LambdaStack
from .nested_stacks.dynamodb_stack import DynamoDBStack

class AssistedWayfindingBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print(f"Initializing stack for project: {config['project_name']}")

        # Create the DynamoDB nested stack
        dynamodb_stack = DynamoDBStack(self, f"{config['project_name']}DynamoDBStack", config=config)

        # Create the Lambda nested stack
        lambda_stack = LambdaStack(self, f"{config['project_name']}LambdaStack", config=config)

        # Pass the DynamoDB table name to the Lambda functions
        lambda_stack.face_recognition_function.add_environment(
            "DYNAMODB_TABLE_NAME", dynamodb_stack.table_name
        )
        lambda_stack.face_indexing_function.add_environment(
            "DYNAMODB_TABLE_NAME", dynamodb_stack.table_name
        )

        # Grant the Lambda functions read/write permissions to the DynamoDB table
        dynamodb_stack.passenger_table.grant_read_write_data(lambda_stack.face_recognition_function)
        dynamodb_stack.passenger_table.grant_read_write_data(lambda_stack.face_indexing_function)

        # Create API Gateway
        api = apigw.RestApi(self, f"{config['project_name']}Api",
            rest_api_name=f"{config['project_name']} API",
            description="API for Assisted Wayfinding"
        )

        face_recognition_integration = apigw.LambdaIntegration(lambda_stack.face_recognition_function)
        face_indexing_integration = apigw.LambdaIntegration(lambda_stack.face_indexing_function)

        api.root.add_resource("recognize").add_method("POST", face_recognition_integration)
        api.root.add_resource("index").add_method("POST", face_indexing_integration)
    ```



These changes will:
1. Set up a Rekognition collection ID in the configuration.
Create two Lambda functions: one for face recognition and one for indexing faces.
3. Grant the necessary permissions to these Lambda functions for accessing Rekognition and DynamoDB.
4. Set up an API Gateway with endpoints for face recognition and face indexing.
Remember to update your requirements.txt file to include the boto3 library if it's not already there.
To create the Rekognition collection, you can add a custom resource to your CDK stack or use the AWS CLI as suggested in the original instructions. If you want to create it via CDK, you'll need to implement a custom resource that calls the Rekognition create_collection API.
These changes should integrate facial recognition into your Assisted Wayfinding backend using AWS Rekognition, Lambda, and API Gateway.



Great question! To upload faces to your system, you'll need to create an endpoint and a process for face enrollment. This typically involves capturing an image of a person's face and associating it with their passenger information. Here's how you can implement this:

1. First, let's create a new Lambda function for face enrollment:

````python:assisted_wayfinding_backend/lambda_functions/face_enrollment/index.py
import os
import boto3
import json
import base64
from botocore.exceptions import ClientError

def handler(event, context):
    print('Face Enrollment Lambda function invoked')
    
    # Get environment variables
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    collection_id = os.environ.get('REKOGNITION_COLLECTION_ID')
    
    if not table_name or not collection_id:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Missing required environment variables'})
        }
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb')
    rekognition = boto3.client('rekognition')
    table = dynamodb.Table(table_name)
    
    try:
        # Extract base64-encoded image and passenger data from the event
        body = json.loads(event['body'])
        image_bytes = base64.b64decode(body['image'])
        passenger_data = body['passengerData']
        
        # Index the face in Rekognition
        index_response = rekognition.index_faces(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            ExternalImageId=passenger_data['passengerId'],
            DetectionAttributes=['ALL']
        )
        
        if index_response['FaceRecords']:
            face_id = index_response['FaceRecords'][0]['Face']['FaceId']
            
            # Store passenger data in DynamoDB
            passenger_data['faceId'] = face_id
            table.put_item(Item=passenger_data)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Face enrolled successfully',
                    'faceId': face_id
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No face detected in the image'
                })
            }
    
    except ClientError as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
````

2. Update the `LambdaStack` to include this new function:

````python:assisted_wayfinding_backend/nested_stacks/lambda_stack.py
# ... (previous code remains the same)

        # Create a Lambda function for face enrollment
        self.face_enrollment_function = _lambda.Function(
            self, "FaceEnrollmentFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("assisted_wayfinding_backend/lambda_functions/face_enrollment"),
            memory_size=config['lambda_memory_size'],
            timeout=Duration.seconds(config['lambda_timeout']),
            environment={
                "DYNAMODB_TABLE_NAME": f"{config['project_name']}-PassengerTable-{config['environment']}",
                "REKOGNITION_COLLECTION_ID": config['rekognition_collection_id'],
                "PROJECT_NAME": config['project_name'],
                "ENVIRONMENT": config['environment'],
            }
        )

        # Add necessary permissions for the new function
        self.face_enrollment_function.add_to_role_policy(rekognition_policy)
        self.face_enrollment_function.add_to_role_policy(dynamodb_policy)

# ... (rest of the code remains the same)
````

3. Update the main stack to include an API Gateway endpoint for face enrollment:

````python:assisted_wayfinding_backend/assisted_wayfinding_backend_stack.py
# ... (previous code remains the same)

        face_enrollment_integration = apigw.LambdaIntegration(lambda_stack.face_enrollment_function)

        api.root.add_resource("enroll").add_method("POST", face_enrollment_integration)

# ... (rest of the code remains the same)
````

Now you have an endpoint for face enrollment. Here's how you can use it:

1. From your client application (e.g., a mobile app or a kiosk interface), you'll need to capture an image of the passenger's face.

2. You'll also need to collect other relevant passenger information (e.g., name, passport number, flight details).

3. Send a POST request to the `/enroll` endpoint with the following JSON structure:

```json
{
  "image": "base64_encoded_image_data",
  "passengerData": {
    "passengerId": "unique_passenger_id",
    "name": "John Doe",
    "passportNumber": "AB1234567",
    "flightNumber": "FL123",
    // ... other relevant passenger information
  }
}
```

4. The Lambda function will then:
   - Index the face in the Rekognition collection
   - Store the passenger information along with the generated face ID in DynamoDB

5. If successful, it will return a response with the face ID, which you can use for future reference.

To use this in your application:

1. Implement a user interface for capturing passenger photos and information.
2. When a new passenger needs to be enrolled, capture their photo and information.
3. Send this data to your `/enroll` endpoint.
4. Store the returned face ID if needed for your application logic.

Remember to handle errors and edge cases, such as when a face can't be detected in the image or when there are network issues.

This setup allows you to enroll faces into your system, which can then be used for recognition later when passengers interact with kiosks or other interfaces in the airport.






I apologize for the oversight. You're right to point out that Rekognition wasn't explicitly deployed in our CDK stack. This is because Amazon Rekognition is a fully managed service that doesn't require explicit deployment like Lambda functions or DynamoDB tables. However, we do need to set up a few things to use Rekognition effectively in our application. Here's what we should do:

1. Create a Rekognition Collection:
   Rekognition collections are containers for persisting detected faces. We need to create one programmatically. Let's add this to our CDK stack.

2. Update the `AssistedWayfindingBackendStack` to create a Rekognition collection:

````python:assisted_wayfinding_backend/assisted_wayfinding_backend_stack.py
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_iam as iam,
    custom_resources as cr,
)
from constructs import Construct
from .nested_stacks.lambda_stack import LambdaStack
from .nested_stacks.dynamodb_stack import DynamoDBStack

class AssistedWayfindingBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ... (existing code)

        # Create Rekognition Collection
        rekognition_collection = cr.AwsCustomResource(
            self, "RekognitionCollection",
            on_create=cr.AwsSdkCall(
                service="Rekognition",
                action="createCollection",
                parameters={
                    "CollectionId": config['rekognition_collection_id']
                },
                physical_resource_id=cr.PhysicalResourceId.of(config['rekognition_collection_id'])
            ),
            on_delete=cr.AwsSdkCall(
                service="Rekognition",
                action="deleteCollection",
                parameters={
                    "CollectionId": config['rekognition_collection_id']
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["rekognition:CreateCollection", "rekognition:DeleteCollection"],
                    resources=["*"]
                )
            ])
        )

        # Grant Rekognition permissions to Lambda functions
        rekognition_policy = iam.PolicyStatement(
            actions=[
                "rekognition:SearchFacesByImage",
                "rekognition:DetectFaces",
                "rekognition:IndexFaces",
            ],
            resources=[f"arn:aws:rekognition:{self.region}:{self.account}:collection/{config['rekognition_collection_id']}"]
        )
        lambda_stack.face_recognition_function.add_to_role_policy(rekognition_policy)
        lambda_stack.face_indexing_function.add_to_role_policy(rekognition_policy)

        # ... (rest of the existing code)
````

3. Update the `config.py` file to include the Rekognition collection ID:

````python:assisted_wayfinding_backend/config.py
def get_config(env: str) -> Dict[str, Any]:
    base_config = {
        'project_name': 'AssistedWayfinding',
        'lambda_runtime': 'python3.9',
        'lambda_handler': 'index.handler',
        'environment': env,
        'rekognition_collection_id': 'AssistedWayfindingFaces',
    }
    # ... (rest of the existing code)
````

4. Make sure the Lambda functions have the correct permissions to access Rekognition. This is already done in the updated `AssistedWayfindingBackendStack` above.

5. Update your Lambda function code to use the correct Rekognition collection ID:

````python:assisted_wayfinding_backend/lambda_functions/face_indexing/index.py
import os
import boto3
import json
import base64
from botocore.exceptions import ClientError

def handler(event, context):
    # ... (existing code)
    
    collection_id = os.environ.get('REKOGNITION_COLLECTION_ID')
    
    # ... (rest of the existing code)
````

Do the same for the face recognition Lambda function.

6. After making these changes, redeploy your stack:

````
cdk deploy
````

This will create a Rekognition collection and grant the necessary permissions to your Lambda functions to interact with it.

Remember, Rekognition is a pay-per-use service, so you'll be billed based on the number of images processed, not for the collection itself.

These changes will properly set up Rekognition for use in your application. After redeploying, you should be able to use Rekognition features in your Lambda functions.




Based on the information provided in the `adding_rekognition.md` file, I'll document the API endpoints that have been implemented for the Assisted Wayfinding application. The API is built using Amazon API Gateway and AWS Lambda functions.

1. Face Enrollment API

Endpoint: POST /enroll
Description: This endpoint is used to enroll a new face into the system.

Request Body:
```json
{
  "image": "base64_encoded_image_data",
  "passengerData": {
    "passengerId": "unique_passenger_id",
    "name": "John Doe",
    "passportNumber": "AB1234567",
    "flightNumber": "FL123",
    // ... other relevant passenger information
  }
}
```

Response:
- Success (200 OK):
```json
{
  "message": "Face enrolled successfully",
  "faceId": "generated_face_id"
}
```
- Error (400 Bad Request):
```json
{
  "message": "No face detected in the image"
}
```
- Error (500 Internal Server Error):
```json
{
  "error": "Error message"
}
```

2. Face Recognition API

Endpoint: POST /recognize
Description: This endpoint is used to recognize a face and retrieve associated passenger information.

Request Body:
```json
{
  "image": "base64_encoded_image_data"
}
```

Response:
- Success (200 OK):
```json
{
  "message": "Face recognized",
  "passengerData": {
    "passengerId": "unique_passenger_id",
    "name": "John Doe",
    "passportNumber": "AB1234567",
    "flightNumber": "FL123",
    // ... other relevant passenger information
  }
}
```
- Error (400 Bad Request):
```json
{
  "message": "No face detected in the image"
}
```
- Error (404 Not Found):
```json
{
  "message": "No matching face found"
}
```
- Error (500 Internal Server Error):
```json
{
  "error": "Error message"
}
```

Both endpoints are implemented using AWS Lambda functions and are integrated with Amazon Rekognition for face detection and recognition. The face enrollment endpoint also stores passenger data in Amazon DynamoDB.

Note: The actual implementation of the face recognition function is not provided in the given markdown file, but it would follow a similar structure to the face enrollment function.

These APIs should be used in conjunction with proper authentication and authorization mechanisms, and all data transmissions should be encrypted using HTTPS. Additionally, ensure compliance with relevant data protection regulations when handling biometric data.


