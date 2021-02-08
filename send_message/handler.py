import boto3
import json
import os
from datetime import datetime
from uuid import uuid1

dynamodb = boto3.client('dynamodb')


def send_to_all(apigatewaymanagementapi, connection_ids, data):
    """

    :param apigatewaymanagementapi:
    :param connection_ids:
    :param data:
    :return:
    """
    for connection_id in connection_ids:
        try:
            apigatewaymanagementapi.post_to_connection(Data=data, ConnectionId=connection_id['connectionId']['S'])
        except Exception as e:
            print(e)
            # Remove connection id from DDB
            dynamodb.delete_item(
                TableName=os.environ.get('CONNECTION_TABLE_NAME'),
                Key={"connectionId": {"S": connection_id['connectionId']['S']}}
            )


def increment_message():
    """

    :return:
    """
    dynamodb.update_item(
        TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'),
        Key={'myid': {'S': 'counter'}},
        UpdateExpression="ADD #msgCount :increment",
        ExpressionAttributeNames={'#msgCount': 'msgCount'},
        ExpressionAttributeValues={':increment': {'N': '1'}}
    )


def store_message(data):
    """

    :param data:
    :return:
    """
    messages = []
    _messages = []
    paginator = dynamodb.get_paginator('scan')
    for page in paginator.paginate(TableName=os.environ.get('MESSAGE_TABLE_NAME')):
        _messages.extend(page['Items'])

    for message in _messages:
        m = {
            message['timestamp']['N']: message['myid']['S']
        }
        messages.append(m)

    # sort list of dict by timestamp
    messages = list(map(dict, sorted(list(i.items()) for i in messages)))

    if len(messages) > 19:
        k, v = list(messages[0].items())[0]
        dynamodb.delete_item(
            TableName=os.environ.get('MESSAGE_TABLE_NAME'),
            Key={
                "myid": {"S": v},
                "timestamp": {"N": k}
            }
        )

    dynamodb.put_item(
        TableName=os.environ.get('MESSAGE_TABLE_NAME'),
        Item={
            'myid': {'S': str(uuid1())},
            'timestamp': {'N': str(datetime.now().timestamp())},
            'data': {'S': data}
        }
    )

    increment_message()


def handle(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    connection_id = event['requestContext']['connectionId']
    response = dynamodb.get_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Key={'connectionId': {'S': connection_id}}
    )

    username = response['Item']['username']['S']
    message = json.loads(event['body'])['message']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = f"[{now} {username}] {message}"
    store_message(data)

    connection_ids = []
    paginator = dynamodb.get_paginator('scan')

    # Retrieve all connection_ids from the database
    for page in paginator.paginate(TableName=os.environ.get('CONNECTION_TABLE_NAME')):
        connection_ids.extend(page['Items'])

    endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
    send_to_all(apigatewaymanagementapi, connection_ids, data)

    return {}
