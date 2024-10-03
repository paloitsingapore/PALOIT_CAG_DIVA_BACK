from aws_cdk import (
    Duration,
    NestedStack,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from constructs import Construct


class LambdaStack(NestedStack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda function for face recognition
        self.face_recognition_function = _lambda.Function(
            self,
            "FaceRecognitionFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assisted_wayfinding_backend/lambda_functions/face_recognition"
            ),
            memory_size=config["lambda_memory_size"],
            timeout=Duration.seconds(config["lambda_timeout"]),
            environment={
                "DYNAMODB_TABLE_NAME": f"{config['project_name']}-PassengerTable-{config['environment']}",
                "REKOGNITION_COLLECTION_ID": config["rekognition_collection_id"],
                "PROJECT_NAME": config["project_name"],
                "ENVIRONMENT": config["environment"],
            },
        )

        self.face_indexing_function = _lambda.Function(
            self,
            "FaceIndexingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assisted_wayfinding_backend/lambda_functions/face_indexing"
            ),
            memory_size=config["lambda_memory_size"],
            timeout=Duration.seconds(config["lambda_timeout"]),
            environment={
                "DYNAMODB_TABLE_NAME": f"{config['project_name']}-PassengerTable-{config['environment']}",
                "REKOGNITION_COLLECTION_ID": config["rekognition_collection_id"],
                "PROJECT_NAME": config["project_name"],
                "ENVIRONMENT": config["environment"],
            },
        )

        # Add necessary permissions for DynamoDB, Rekognition, and other AWS services
        rekognition_policy = iam.PolicyStatement(
            actions=[
                "rekognition:SearchFacesByImage",
                "rekognition:DetectFaces",
                "rekognition:IndexFaces",
            ],
            resources=[
                f"arn:aws:rekognition:{self.region}:{self.account}:collection/{config['rekognition_collection_id']}"
            ],
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
                "dynamodb:Scan",
            ],
            resources=["*"],  # TODO: Restrict this to specific table ARNs in production
        )

        self.face_recognition_function.add_to_role_policy(dynamodb_policy)
        self.face_indexing_function.add_to_role_policy(dynamodb_policy)

        # Add S3 permissions
        s3_policy = iam.PolicyStatement(
            actions=["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
            resources=[f"arn:aws:s3:::{config['s3_bucket_name'].lower()}/*"],
        )

        self.face_recognition_function.add_to_role_policy(s3_policy)
        self.face_indexing_function.add_to_role_policy(s3_policy)
