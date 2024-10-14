import json
from unittest.mock import MagicMock, patch
import pytest
from assisted_wayfinding_backend.lambda_functions.orchestration.index import handler

@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv("WEBSOCKET_API_ENDPOINT", "https://test-api-id.execute-api.region.amazonaws.com/prod")

@pytest.fixture
def mock_event():
    return {
        'requestContext': {'connectionId': 'test-connection-id'},
        'body': json.dumps({
            'message': {
                'name': 'conversationRequest',
                'body': {
                    'input': {'text': 'Hello'},
                    'optionalArgs': {'kind': 'init'}
                }
            }
        })
    }

@patch('boto3.client')
def test_orchestration_handler(mock_boto3_client, mock_environment, mock_event):
    mock_api = MagicMock()
    mock_boto3_client.return_value = mock_api

    response = handler(mock_event, {})

    assert response['statusCode'] == 200
    mock_api.post_to_connection.assert_called_once()
    
    # Check the sent message
    sent_message = json.loads(mock_api.post_to_connection.call_args[1]['Data'])
    assert sent_message['name'] == 'conversationResponse'
    assert sent_message['body']['output']['text'] == 'Hi there!'

@pytest.mark.parametrize("input_text,expected_output", [
    ("Why is the sky blue?", "I do not know how to answer that"),
    ("show card", "Here is a cat @showcards(cat)"),
    ("Hello", "Echo: Hello"),
])
def test_handle_request(input_text, expected_output, mock_environment):
    from assisted_wayfinding_backend.lambda_functions.orchestration.index import handle_request
    
    request = {
        'input': {'text': input_text},
    }
    
    response = handle_request(request)
    assert response['output']['text'] == expected_output

    if input_text == "show card":
        assert 'public-cat' in response['variables']