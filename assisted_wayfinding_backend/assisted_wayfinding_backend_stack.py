from aws_cdk import Stack
from constructs import Construct
from .nested_stacks.lambda_stack import LambdaStack

class AssistedWayfindingBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print(f"Initializing stack for project: {config['project_name']}")

        # Create the Lambda nested stack
        lambda_stack = LambdaStack(self, f"{config['project_name']}LambdaStack", config=config)
