import boto3
import os

dynamodb = boto3.client('dynamodb')


def handle(event, context):
    """
    Method that handle on_connect event, it will store connection_id and username into DDB

    :param event: JSON-formatted document that contains data for a Lambda function to process.
    :param context: A context object is passed to your function by Lambda at runtime.
    This object provides methods and properties that provide information about the invocation,
    function, and runtime environment.
    :return: {}
    """
    username = event['queryStringParameters']['username']
    connection_id = event['requestContext']['connectionId']

    # Insert the connectionId of the connected device to the database
    dynamodb.put_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Item={'connectionId': {'S': connection_id}, 'username': {'S': username}}
    )

    return {}
