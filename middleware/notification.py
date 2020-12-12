import boto3
import json

client = boto3.client('sns')

filters = {
	'/api/registration': {
		"methods": ["POST"],
		"topic": "arn:aws:sns:us-east-2:596702767460:EmailSNS"
	}
}

def publish_string(topic, json_data):
	s = json.dumps(json_data, default = str)
	print("Emitting ", s, "to ", topic)
	res = client.publish(topicArn=topic, Message=s)
	return res

def notify(request, response):

	path = request.path
	method = request.method
	body = request.json

	filter = filters.get(path, None)

	if filter is not None:
		if methor in filter["methods"]:

			event = {
				"resource": path,
				"method": method,
				"data": body
			}
			topic = filter["topic"]

			publish_string(topic, event)