from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
)
from constructs import Construct

from .nested_stacks.dynamodb_stack import DynamoDBStack
from .nested_stacks.lambda_stack import LambdaStack
from .nested_stacks.storage_stack import StorageStack


class AssistedWayfindingBackendStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the DynamoDB nested stack
        dynamodb_stack = DynamoDBStack(
            self, f"{config['project_name']}DynamoDBStack", config=config
        )

        # Update config with the DynamoDB table
        config["dynamodb_table"] = dynamodb_stack.table

        # Create the Storage nested stack
        storage_stack = StorageStack(
            self, f"{config['project_name']}StorageStack", config=config
        )

        # Update config with necessary values
        config.update(
            {
                "rekognition_collection_id": "AssistedWayfindingFaces",
                "s3_bucket_name": storage_stack.passenger_photos_bucket.bucket_name,
                "map_image_bucket": storage_stack.map_images_bucket.bucket_name,  # Add this line
                "dynamodb_table_name": dynamodb_stack.table_name,  # Use the table_name property
            }
        )

        # Create the Lambda nested stack
        lambda_stack = LambdaStack(
            self, f"{config['project_name']}LambdaStack", config=config
        )

        # Pass S3 bucket name and DynamoDB table name to Lambda functions
        lambda_stack.face_indexing_function.add_environment(
            "S3_BUCKET_NAME", storage_stack.passenger_photos_bucket.bucket_name
        )
        lambda_stack.face_recognition_function.add_environment(
            "S3_BUCKET_NAME", storage_stack.passenger_photos_bucket.bucket_name
        )
        lambda_stack.face_recognition_function.add_environment(
            "DYNAMODB_TABLE_NAME", dynamodb_stack.table_name
        )
        lambda_stack.face_indexing_function.add_environment(
            "DYNAMODB_TABLE_NAME", dynamodb_stack.table_name
        )

        # Create API Gateway
        api = apigw.RestApi(
            self,
            f"{config['project_name']}Api",
            rest_api_name=f"{config['project_name']} API",
            description="API for Assisted Wayfinding",
        )

        face_recognition_integration = apigw.LambdaIntegration(
            lambda_stack.face_recognition_function
        )
        face_indexing_integration = apigw.LambdaIntegration(
            lambda_stack.face_indexing_function
        )

        api.root.add_resource("recognize").add_method(
            "POST", face_recognition_integration
        )
        api.root.add_resource("index").add_method("POST", face_indexing_integration)

        remove_all_faces_integration = apigw.LambdaIntegration(
            lambda_stack.remove_all_faces_function
        )

        api.root.add_resource("remove_all_faces").add_method(
            "POST", remove_all_faces_integration
        )

        directions_integration = apigw.LambdaIntegration(
            lambda_stack.directions_function
        )
        directions_resource = api.root.add_resource("directions")
        from_resource = directions_resource.add_resource("{from}")
        to_resource = from_resource.add_resource("{to}")
        to_resource.add_method("GET", directions_integration)

        # Add manual user lookup integration
        manual_user_lookup_integration = apigw.LambdaIntegration(
            lambda_stack.manual_user_lookup_function
        )

        # Add the /manual-lookup endpoint with GET method
        api.root.add_resource("manual-lookup").add_method(
            "GET", manual_user_lookup_integration
        )
