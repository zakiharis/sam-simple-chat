import boto3
import os
import pytest

from moto import mock_dynamodb2
from on_disconnect import handler


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

        dynamodb.put_item(
            TableName=os.environ.get('CONNECTION_TABLE_NAME'),
            Item={'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}}
        )
        dynamodb.put_item(
            TableName=os.environ.get('CONNECTION_TABLE_NAME'),
            Item={'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
        )
        return dynamodb
    return dynamodb_client


@mock_dynamodb2
def test_handle(apigw_event, mocker, use_moto, monkeypatch):
    ddb = use_moto()

    def mock_return(apig_management_client, connection_ids, data):
        expected_connection_ids = [
            {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}},
            {'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
        ]

        assert data == 'foo has left the chat room'
        assert connection_ids == expected_connection_ids
        return None

    monkeypatch.setattr(handler, "send_to_all", mock_return)
    handler.handle(apigw_event, mocker)

    connection_id = 'abc123='
    result = ddb.get_item(
        TableName=os.environ.get('CONNECTION_TABLE_NAME'),
        Key={'connectionId': {'S': connection_id}}
    )

    # assert data deleted
    assert not(result.get('Item', None))


@mock_dynamodb2
def test_send_to_all(use_moto, monkeypatch):
    ddb = use_moto()
    connection_ids = [
        {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}},
        {'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
    ]
    data = 'foo has left the chat room'

    def mock_post_to_connection(Data, ConnectionId):
        assert Data == data
        assert ConnectionId == connection_ids[0]['connectionId']['S'] or ConnectionId == connection_ids[1]['connectionId']['S']
        return None

    apig_management_client = boto3.client('apigatewaymanagementapi')
    monkeypatch.setattr(apig_management_client, 'post_to_connection', mock_post_to_connection)
    handler.send_to_all(apig_management_client, connection_ids, data)
