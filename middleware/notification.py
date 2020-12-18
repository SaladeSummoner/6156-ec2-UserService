import boto3
import json
import os

AWS_KEY_ID = os.environ['aws_access_key_id']
AWS_KEY = os.environ['aws_secret_access_key']

client = boto3.client('sns',
                      aws_access_key_id=AWS_KEY_ID,
                      aws_secret_access_key=AWS_KEY,
                      region_name='us-east-2')

filters = {
    '/api/registration': {
        "methods": ["POST"],
        "topic": "arn:aws:sns:us-east-2:596702767460:EmailSNS"
    }
}


def publish_string(topic, json_data):
    s = json.dumps(json_data, default=str)
    print("Emitting ", s, "to ", topic)
    res = client.publish(TopicArn=topic, Message=s)
    return res


def notify(request, response):
    path = request.path
    method = request.method
    body = request.json

    f = filters.get(path, None)

    if f is not None:
        if method in f["methods"]:
            event = {
                "resource": path,
                "method": method,
                "data": body
            }
            topic = f["topic"]

            publish_string(topic, event)
