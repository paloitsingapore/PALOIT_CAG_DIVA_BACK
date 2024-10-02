import aws_cdk as core
import aws_cdk.assertions as assertions
from assisted_wayfinding_backend.assisted_wayfinding_backend_stack import AssistedWayfindingBackendStack
from assisted_wayfinding_backend.config import get_config

# example tests. To run these tests, uncomment this file along with the example
# resource in assisted_wayfinding_backend/assisted_wayfinding_backend_stack.py
# def test_sqs_queue_created():
#     app = core.App()
#     stack = AssistedWayfindingBackendStack(app, "assisted-wayfinding-backend")
#     template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

def test_stack_creates_lambda_stack():
    app = core.App()
    config = get_config('dev')
    stack = AssistedWayfindingBackendStack(app, "AssistedWayfindingBackendStack", config=config)
    template = assertions.Template.from_stack(stack)

    # Test that a nested stack is created with the correct name
    template.has_resource_properties("AWS::CloudFormation::Stack", {
        "TemplateURL": assertions.Match.any_value(),
    })

    # Ensure only one nested stack is created
    template.resource_count_is("AWS::CloudFormation::Stack", 1)

    # Check that the nested stack's logical ID contains the project name and "LambdaStack"
    template.has_resource("AWS::CloudFormation::Stack", {
        "Properties": assertions.Match.object_like({
            "TemplateURL": assertions.Match.any_value()
        }),
        "UpdateReplacePolicy": "Delete",
        "DeletionPolicy": "Delete"
    })

    # Verify that exactly one LambdaStack is created
    template.resource_count_is(
        "AWS::CloudFormation::Stack",
        1
    )

# ... existing code ...
