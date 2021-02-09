import boto3
import os
import pytest

from moto import mock_dynamodb2
from on_connect import handler


@pytest.fixture
def use_moto():
    @mock_dynamodb2
    def dynamodb_client():
        dynamodb = boto3.client('dynamodb')

        # Create the table
        dynamodb.create_table(
            TableName=os.environ.get('CONNECTION_TABLE_NAME'),
            KeySchema=[
                {
                    'AttributeName': 'connectionId',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'connectionId',
                    'AttributeType': 'S'
                },
            ],
        )
        return dynamodb
    return dynamodb_client


@mock_dynamodb2
def test_handle(apigw_event, mocker, use_moto):
    ddb = use_moto()
    apigw_event['queryStringParameters'] = {'username': 'foo'}
    handler.handle(apigw_event, mocker)

    connection_id = 'abc123='
    result = ddb.get_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Key={'connectionId': {'S': connection_id}}
    )

    assert result['Item']['connectionId']['S'] == connection_id
    assert result['Item']['username']['S'] == 'foo'


@mock_dynamodb2
def test_handle_with_exception(use_moto, mocker):
    use_moto()

    with pytest.raises(Exception) as e:
        handler.handle('', mocker)

    assert e.type.__name__ == 'TypeError'
