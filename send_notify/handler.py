import boto3
import os


def send_to_all(apigatewaymanagementapi, connection_ids, data):
    """
    Send message to all alive connections

    :param apigatewaymanagementapi: apigatewaymanagemntapi client
    :param connection_ids: List of connection ids from DDB
    :param data: String message
    :return:
    """
    dynamodb = boto3.client('dynamodb')
    for connection_id in connection_ids:
        try:
            apigatewaymanagementapi.post_to_connection(Data=data, ConnectionId=connection_id['connectionId']['S'])
        except Exception as e:
            print(e)
            # Remove connection id from DDB
            dynamodb.delete_item(
                TableName=os.environ.get('CONNECTION_TABLE_NAME'),
                Key={'connectionId': {'S': connection_id['connectionId']['S']}}
            )


def send_to_self(apigatewaymanagementapi, connection_id, data):
    """
    Send message to self

    :param apigatewaymanagementapi: apigatewaymanagemntapi client
    :param connection_id: Self connection Id
    :param data: String message
    :return:
    """
    apigatewaymanagementapi.post_to_connection(
        Data=data,
        ConnectionId=connection_id
    )


def get_messages():
    """
    Method to get last 20 messages from users.

    :return: List of messages
    """
    dynamodb = boto3.client('dynamodb')
    messages = []
    _messages = []
    paginator = dynamodb.get_paginator('scan')
    for page in paginator.paginate(TableName=os.environ.get('MESSAGE_TABLE_NAME')):
        _messages.extend(page['Items'])

    if not _messages:
        return _messages

    for message in _messages:
        m = {
            message['timestamp']['N']: message['data']['S']
        }
        messages.append(m)

    # sort list of dict by timestamp
    messages = list(map(dict, sorted(list(i.items()) for i in messages)))

    _messages = []
    for message in messages:
        _, v = list(message.items())[0]
        _messages.append(v)

    return _messages


def handle(event, context):
    """
    Method that handle sendnotify action. It will send chat history to client, and send messaage to all alive client
    to notify that someone has joined the chat room.

    :param event: JSON-formatted document that contains data for a Lambda function to process.
    :param context: A context object is passed to your function by Lambda at runtime.
    This object provides methods and properties that provide information about the invocation,
    function, and runtime environment.
    :return: {}
    """
    dynamodb = boto3.client('dynamodb')
    connection_id = event['requestContext']['connectionId']
    connection_ids = []
    paginator = dynamodb.get_paginator('scan')

    # Retrieve all connection_ids from the database
    for page in paginator.paginate(TableName=os.environ.get('CONNECTION_TABLE_NAME')):
        connection_ids.extend(page['Items'])

    endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)

    msg_counter = dynamodb.get_item(TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'), Key={'myid': {'S': 'counter'}})
    if not msg_counter:
        msg_counter = 0
    else:
        msg_counter = msg_counter['Item']['msgCount']['N']

    data = f"Welcome to Simple Chat\n" \
           f"There are {len(connection_ids)} users connected.\n" \
           f"Total of {msg_counter} messages recorded as of today.\n\n"

    messages = get_messages()
    data = data + '\n'.join(messages)
    send_to_self(apigatewaymanagementapi, connection_id, data)

    response = dynamodb.get_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Key={'connectionId': {'S': connection_id}}
    )
    data = f"{response['Item']['username']['S']} has joined the chat room"
    send_to_all(apigatewaymanagementapi, connection_ids, data)

    return {}

