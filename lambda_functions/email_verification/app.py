import boto3
import json
import jwt
from botocore.exceptions import ClientError

client = boto3.client('ses')

_secret = "my_secret"
_base_url = "https://3p49xksrz3.execute-api.us-east-1.amazonaws.com/api/email_verification?token="

_redirect_url = "http://psyduckstaticwebsite.s3-website.us-east-2.amazonaws.com/Website/static/email_success.html?"
_redirect_url += "lastname={}&firstname={}&email={}"

_verification_email_sender = "niejingjing1025@163.com"

client = boto3.client('ses')


def generate_token(event):
    
    encoded = jwt.encode(event, _secret)
    return encoded


def send_verification_email(normal_event):

    SENDER = _verification_email_sender

    data.= normal_event.get(data)
    RECIPIENT = data.get("email", None)

    if RECIPIENT is None:
        print("Invalid notification event = \n", json.dumps(normal_event, indent=3, default=str))
        return None

    AWS_REGION = "us-east-2"

    # The subject line for the email.
    SUBJECT = "Verify your email for Psyduck"

    encoded_token = generate_token(normal_event)
    click_url = _base_url + encoded_token.decode()

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto)."
                 )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
        <h1>Amazon SES Test (SDK for Python)</h1>
        <p>This email was sent with
            <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
            <a href='https://aws.amazon.com/sdk-for-python/'>
            AWS SDK for Python (Boto)</a>.</p>
        <p>Click here {} to verify your email!</p>
    </body>
    </html>
                """

    BODY_HTML = BODY_HTML.format(click_url)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])



def normalize_event(event):

    normal_event = None

    try:
        inp = event["Records"][0]["Sns"]["Message"]
        print("SNS Event, message = ", inp)
        normal_message = {}
        normal_message = json.loads(inp)
        print("Parsed JSON")
        normal_message["type"] = "SNS"
    except Exception as e:
        pass

    try:
        inp = event["httpMethod"]
        print("HTTP Method = ", inp)
        normal_message = {}
        normal_message["type"] = "HTTP"
        normal_message["query_params"] = event["queryStringParameters"]
    except Exception as e:
        pass

    return normal_message


def handle_verification(normal_event):

    tok = None
    dec_tok = None

    tok = normal_event.get('query_params', None)
    if tok is not None:
        tok = tok.get('token', None)
        tok = str.encode(tok)

    if tok is not None:
        print("Token = ", tok)
        dec_tok = jwt.decode(tok, _secret)
        print("Decoded token = ", dec_tok)

    return dec_tok


def generate_response(result):

    lastname = result.get("last_name", None)
    firstname = result.get("first_name", None)
    email = result.get("email", None)

    redirect_url = _redirect_url.format(lastname, firstname, email)
    headers = {}
    headers["location"] = redirect_url

    result["message"] = "Congratulation! Email Verified!"
    result = {
        "statusCode": 302,
        "headers": headers
    }
    return result


def lambda_handler(event, context):
    final_result = None
    result = None

    print("Incoming event = \n", json.dumps(event, indent=4, default=str))

    normal_event = normalize_event(event)
    print("normalized event = \n", json.dumps(normal_event, indent=4, default=str))

    event_type = normal_event.get("type")

    if event_type == "SNS":
        send_verification_email(normal_event)
    elif event_type == "HTTP":
        result = handle_verification(normal_event)
        final_result = generate_response(result)
    else:
        raise(ValueError("Invalid event type"))

    if final_result is not None:
        print("Returning ... ... \n", json.dumps(final_result))
        return final_result

