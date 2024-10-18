import json
import os
import boto3

def handler(event, context):
    print("Orchestration Lambda function invoked")

    connection_id = event['requestContext']['connectionId']
    api_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_API_ENDPOINT'])

    try:
        body = json.loads(event['body'])
        message = body.get('message', {})

        if message.get('name') == 'conversationRequest':
            request = message.get('body', {})
            response = handle_request(request)
            send_message(api_client, connection_id, response)
        else:
            print('Unrecognized message:', body)

        return {'statusCode': 200, 'body': 'Message processed'}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def handle_request(req):
    print('Conv request:', req)

    input_text = req.get('input', {}).get('text', '')
    persona_id = req.get('personaId')

    # Call the get_passenger_data Lambda function
    passenger_data_response = call_get_passenger_data_lambda(persona_id)

    # Use the passenger data response as context for the chat
    context = generate_context(passenger_data_response)

    resp = {
        'input': {'text': input_text},
        'output': {'text': generate_response(input_text, context)},
        'variables': {}
    }

    optional_args = req.get('optionalArgs', {})
    if optional_args.get('kind') == 'init':
        resp['output']['text'] = f"Hi there, {context['name']}!"

    return resp

def call_get_passenger_data_lambda(persona_id):
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName='get_passenger_data_lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({'personaId': persona_id})
        )
        return json.loads(response['Payload'].read())
    except Exception as e:
        print(f"Error calling get_passenger_data_lambda: {str(e)}")
        return {'passengerData': {}}  # Return default data on error

def generate_context(passenger_data_response):
    passenger_data = passenger_data_response.get('passengerData', {})
    return {
        'name': passenger_data.get('name', 'Guest'),
        'gender': passenger_data.get('gender', 'Unknown'),
        'age': passenger_data.get('age', 'Unknown'),
        'userId': passenger_data.get('userId', 'Unknown')
    }

def generate_response(input_text, context):
    # TODO: Implement more sophisticated response generation using the context
    return f"Hello {context['name']}, how can I assist you today?"

def send_message(api_client, connection_id, resp):
    message = {
        'category': 'scene',
        'kind': 'request',
        'name': 'conversationResponse',
        'body': resp
    }

    api_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(message)
    )
