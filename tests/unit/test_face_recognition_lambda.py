import json
from assisted_wayfinding_backend.lambda_functions.face_recognition import index

def test_face_recognition_lambda_handler():
    # Test event
    event = {}
    context = {}

    # Call the handler function
    response = index.handler(event, context)

    # Assert the response
    assert response['statusCode'] == 200
    assert response['body'] == 'Face Recognition function executed successfully!'