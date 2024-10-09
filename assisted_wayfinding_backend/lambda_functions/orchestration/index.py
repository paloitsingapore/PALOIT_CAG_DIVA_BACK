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
    resp = {
        'input': {'text': input_text},
        'output': {'text': f"Echo: {input_text}"},
        'variables': {}
    }

    optional_args = req.get('optionalArgs', {})
    if optional_args.get('kind') == 'init':
        resp['output']['text'] = 'Hi there!'

    if input_text.lower().startswith('why'):
        resp['output']['text'] = 'I do not know how to answer that'
        resp['fallback'] = True

    if input_text.lower() == 'show card':
        resp['output']['text'] = 'Here is a cat @showcards(cat)'
        resp['variables']['public-cat'] = {
            'component': 'image',
            'data': {
                'alt': 'A cute kitten',
                'url': 'https://placekitten.com/300/300'
            }
        }

    return resp

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