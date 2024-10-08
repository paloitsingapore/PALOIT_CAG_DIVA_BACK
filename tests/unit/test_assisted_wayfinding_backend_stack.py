import aws_cdk as core
import aws_cdk.assertions as assertions

from assisted_wayfinding_backend.assisted_wayfinding_backend_stack import (
    AssistedWayfindingBackendStack,
)
from assisted_wayfinding_backend.config import get_config


def test_stack_creates_nested_stacks():
    app = core.App()
    config = get_config("dev")
    stack = AssistedWayfindingBackendStack(
        app, "AssistedWayfindingBackendStack", config=config
    )
    template = assertions.Template.from_stack(stack)

    # Verify that exactly three nested stacks are created
    template.resource_count_is("AWS::CloudFormation::Stack", 3)

    # Test that nested stacks are created with the correct names
    stack_names = [
        f"{config['project_name']}DynamoDBStack",
        f"{config['project_name']}StorageStack",
        f"{config['project_name']}LambdaStack",
    ]

    for stack_name in stack_names:
        template.has_resource_properties(
            "AWS::CloudFormation::Stack",
            {
                "TemplateURL": assertions.Match.any_value(),
            },
        )


def test_nested_stack_properties():
    app = core.App()
    config = get_config("dev")
    stack = AssistedWayfindingBackendStack(
        app, "AssistedWayfindingBackendStack", config=config
    )
    template = assertions.Template.from_stack(stack)

    # Check properties for each nested stack
    stack_names = [
        f"{config['project_name']}DynamoDBStack",
        f"{config['project_name']}StorageStack",
        f"{config['project_name']}LambdaStack",
    ]

    for stack_name in stack_names:
        template.has_resource(
            "AWS::CloudFormation::Stack",
            {
                "Properties": assertions.Match.object_like(
                    {"TemplateURL": assertions.Match.any_value()}
                ),
                "UpdateReplacePolicy": "Delete",
                "DeletionPolicy": "Delete",
            },
        )


def test_main_stack_iam_role():
    app = core.App()
    config = get_config("dev")
    stack = AssistedWayfindingBackendStack(
        app, "AssistedWayfindingBackendStack", config=config
    )
    template = assertions.Template.from_stack(stack)

    # Check if IAM role is created in the main stack
    template.resource_count_is("AWS::IAM::Role", 1)

    # Verify IAM role properties
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": assertions.Match.object_like(
                {
                    "Statement": assertions.Match.array_with(
                        [
                            assertions.Match.object_like(
                                {
                                    "Action": "sts:AssumeRole",
                                    "Effect": "Allow",
                                    "Principal": {
                                        "Service": assertions.Match.any_value()
                                    },
                                }
                            )
                        ]
                    ),
                }
            ),
        },
    )


def test_api_gateway():
    app = core.App()
    config = get_config("dev")
    stack = AssistedWayfindingBackendStack(
        app, "AssistedWayfindingBackendStack", config=config
    )
    template = assertions.Template.from_stack(stack)

    # Check if API Gateway is created
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)

    # Verify API Gateway properties
    template.has_resource_properties(
        "AWS::ApiGateway::RestApi",
        {
            "Name": "AssistedWayfinding API",
            "Description": "API for Assisted Wayfinding",
        },
    )
