from aws_cdk import (
    CfnOutput,
    Duration,
    NestedStack,
    aws_iam as iam,
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

        # Add S3 permissions to both functions
        s3_policy = iam.PolicyStatement(
            actions=[
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",  # Add this line
            ],
            resources=[
                f"arn:aws:s3:::{config['s3_bucket_name']}/*",
                f"arn:aws:s3:::{config['s3_bucket_name']}",
            ],
        )
        self.face_indexing_function.add_to_role_policy(s3_policy)
        self.face_recognition_function.add_to_role_policy(s3_policy)

        # Update the Rekognition permissions for the face indexing function
        face_indexing_rekognition_policy = iam.PolicyStatement(
            actions=[
                "rekognition:CreateUser",
                "rekognition:IndexFaces",
                "rekognition:SearchFacesByImage",
                "rekognition:ListFaces",
                "rekognition:AssociateFaces",
            ],
            resources=[
                f"arn:aws:rekognition:{self.region}:{self.account}:collection/{config['rekognition_collection_id']}"
            ],
        )
        self.face_indexing_function.add_to_role_policy(face_indexing_rekognition_policy)

        # Add DynamoDB permissions to both functions
        dynamodb_policy = iam.PolicyStatement(
            actions=[
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
            ],
            resources=[
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{config['dynamodb_table_name']}"
            ],
        )
        self.face_indexing_function.add_to_role_policy(dynamodb_policy)
        self.face_recognition_function.add_to_role_policy(dynamodb_policy)

        # Add new function for removing all faces
        self.remove_all_faces_function = _lambda.Function(
            self,
            "RemoveAllFacesFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assisted_wayfinding_backend/lambda_functions/remove_all_faces"
            ),
            environment={
                "DYNAMODB_TABLE_NAME": config["dynamodb_table_name"],
                "REKOGNITION_COLLECTION_ID": config["rekognition_collection_id"],
            },
        )

        # Update permissions for the remove_all_faces_function
        self.remove_all_faces_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "rekognition:ListFaces",
                    "rekognition:DeleteFaces",
                ],
                resources=[
                    f"arn:aws:rekognition:*:*:collection/{config['rekognition_collection_id']}"
                ],
            )
        )

        self.remove_all_faces_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:Scan",
                    "dynamodb:DeleteItem",
                    "dynamodb:BatchWriteItem",  # Add this line
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{config['dynamodb_table_name']}"
                ],
            )
        )

        # Add the Directions Lambda function
        self.directions_function = _lambda.Function(
            self,
            "DirectionsFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assisted_wayfinding_backend/lambda_functions/directions"
            ),
            environment={
                "MAP_IMAGE_BUCKET": config["map_image_bucket"],
            },
        )
        CfnOutput(self, "MapImageBucketName", value=config["map_image_bucket"])

        # Add S3 read permissions for the Directions function
        self.directions_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                ],
                resources=[
                    f"arn:aws:s3:::{config['map_image_bucket']}",
                    f"arn:aws:s3:::{config['map_image_bucket']}/*",
                ],
            )
        )

        # Add the manual user lookup function
        self.manual_user_lookup_function = _lambda.Function(
            self,
            "ManualUserLookupFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assisted_wayfinding_backend/lambda_functions/manual_user_lookup"
            ),
            environment={
                "DYNAMODB_TABLE_NAME": config["dynamodb_table"].table_name,
            },
        )

        # Grant DynamoDB read permissions to the manual user lookup function
        config["dynamodb_table"].grant_read_data(self.manual_user_lookup_function)
