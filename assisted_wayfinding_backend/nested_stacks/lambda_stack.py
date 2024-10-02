from aws_cdk import (
    NestedStack,
    aws_lambda as _lambda,
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
            timeout=Duration.seconds(config['lambda_timeout'])
        )