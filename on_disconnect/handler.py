import boto3
import os

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


def handle(event, context):
    """

    :param event:
    :param context:
    :return:
    """
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
