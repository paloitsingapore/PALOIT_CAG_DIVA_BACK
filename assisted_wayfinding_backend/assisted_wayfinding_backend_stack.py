from aws_cdk import Stack
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

        # Pass the DynamoDB table name to the Lambda function
        lambda_stack.face_recognition_function.add_environment(
            "DYNAMODB_TABLE_NAME", dynamodb_stack.table_name
        )

        # Grant the Lambda function read/write permissions to the DynamoDB table
        dynamodb_stack.passenger_table.grant_read_write_data(lambda_stack.face_recognition_function)
