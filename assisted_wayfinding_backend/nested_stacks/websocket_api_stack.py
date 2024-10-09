from aws_cdk import (
    NestedStack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
)
from constructs import Construct

class WebSocketApiStack(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, orchestration_function, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create WebSocket API with a route selection expression (even if using only the default route)
        self.websocket_api = apigwv2.WebSocketApi(
            self, "WebSocketAPI",
            route_selection_expression="$request.body.action" 
        )

        # Create WebSocket Stage
        self.websocket_stage = apigwv2.WebSocketStage(
            self, "WebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name="prod",
            auto_deploy=True
        )

        # Create Lambda integration for handling the WebSocket connection
        integration = integrations.WebSocketLambdaIntegration(
            "OrchestrationIntegration",
            handler=orchestration_function
        )

        # Add default route for handling all WebSocket messages
        self.websocket_api.add_route("$default", integration=integration, return_response=True)