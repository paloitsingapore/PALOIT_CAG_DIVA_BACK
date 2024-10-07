from aws_cdk import (
    NestedStack,
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

        self._table = dynamodb.Table(
            self,
            "AssistedWayfindingTable",
            partition_key=dynamodb.Attribute(
                name="userId", type=dynamodb.AttributeType.STRING
            ),
            # ... other table properties ...
        )

    @property
    def table_name(self):
        return self._table.table_name

    @property
    def table(self):
        return self._table
