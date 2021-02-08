import boto3
import os

dynamodb = boto3.client('dynamodb')


def handle(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    username = event['queryStringParameters']['username']
    connection_id = event['requestContext']['connectionId']

    # Insert the connectionId of the connected device to the database
    dynamodb.put_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Item={'connectionId': {'S': connection_id}, 'username': {'S': username}}
    )

    return {}
