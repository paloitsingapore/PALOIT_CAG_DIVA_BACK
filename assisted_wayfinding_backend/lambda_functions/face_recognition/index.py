def handler(event, context):
    print('Face Recognition Lambda function invoked')
    return {
        'statusCode': 200,
        'body': 'Face Recognition function executed successfully!'
    }