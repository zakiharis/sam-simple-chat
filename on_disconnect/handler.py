import boto3
import os


def send_to_all(apigatewaymanagementapi, connection_ids, data):
    """
    Send message to all alive connections

    :param apigatewaymanagementapi: apigatewaymanagemntapi client
    :param connection_ids: List of connection ids from DDB
    :param data: String message
    :return: None
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


def handle(event, context):
    """
    Method that handle on_disconnect event such as sending message to notify other users that someone is leaving

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

    response = dynamodb.get_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Key={'connectionId': {'S': connection_id}}
    )

    if response['Item']:
        data = f"{response['Item']['username']['S']} has left the chat room"
        send_to_all(apigatewaymanagementapi, connection_ids, data)

    # Delete connectionId from the database
    dynamodb.delete_item(TableName=os.environ.get('CONNECTION_TABLE_NAME'), Key={'connectionId': {'S': connection_id}})

    return {}
