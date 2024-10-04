from aws_cdk import (
    NestedStack,
    RemovalPolicy,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class DynamoDBStack(NestedStack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a DynamoDB table for passenger information
        self.passenger_table = dynamodb.Table(
            self,
            "PassengerTable",
            table_name=f"{config['project_name']}-PassengerTable-{config['environment']}",
            partition_key=dynamodb.Attribute(
                name="passengerId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            if config["environment"] == "dev"
            else RemovalPolicy.RETAIN,
        )

        # Add GSI for lookups by age range and gender
        self.passenger_table.add_global_secondary_index(
            index_name="AgeGenderIndex",
            partition_key=dynamodb.Attribute(
                name="ageRange", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="gender", type=dynamodb.AttributeType.STRING
            ),
        )

        # Add a secondary index on faceId
        self.passenger_table.add_global_secondary_index(
            index_name="faceId-index",
            partition_key=dynamodb.Attribute(
                name="faceId", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Expose table properties
        self.table_name = self.passenger_table.table_name
        self.table_arn = self.passenger_table.table_arn
