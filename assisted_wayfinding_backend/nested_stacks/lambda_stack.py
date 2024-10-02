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
                # We'll set the DYNAMODB_TABLE_NAME in the main stack
                "PROJECT_NAME": config['project_name'],
                "ENVIRONMENT": config['environment'],
            }
        )

        # Add necessary permissions for DynamoDB and other AWS services
        self.face_recognition_function.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=["*"] # TODO: Restrict this to specific table ARNs in production
        ))