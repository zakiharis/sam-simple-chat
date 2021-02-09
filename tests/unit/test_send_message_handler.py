import boto3
import os
import pytest

from datetime import datetime
from moto import mock_dynamodb2
from send_message import handler


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

        dynamodb.create_table(
            TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'),
            KeySchema=[
                {
                    'AttributeName': 'myid',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'myid',
                    'AttributeType': 'S'
                },
            ],
        )

        dynamodb.create_table(
            TableName=os.environ.get('MESSAGE_TABLE_NAME'),
            KeySchema=[
                {
                    'AttributeName': 'myid',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'myid',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'N'
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


@mock_dynamodb2
def test_increment_message_first_time(use_moto):
    ddb = use_moto()
    handler.increment_message()

    result = ddb.get_item(TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'), Key={'myid': {'S': 'counter'}})
    assert result['Item']['msgCount']['N'] == '1'


@mock_dynamodb2
def test_increment_message_existing(use_moto):
    ddb = use_moto()

    ddb.put_item(
        TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'),
        Item={'myid': {'S': 'counter'}, 'msgCount': {'N': '55'}}
    )

    handler.increment_message()

    result = ddb.get_item(TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'), Key={'myid': {'S': 'counter'}})
    assert result['Item']['msgCount']['N'] == '56'


@mock_dynamodb2
def test_store_message_not_exceed_20(use_moto):
    ddb = use_moto()
    ddb.put_item(
        TableName=os.environ.get('MESSAGE_TABLE_NAME'),
        Item={'myid': {'S': 'uuid-1'},
              'timestamp': {'N': '1612770838.718373'},
              'data': {'S': '[2021-02-08 07:53:58 Zaki] test 1'}}
    )

    data = '[2021-02-08 07:54:04 Zaki] test 2'
    handler.store_message(data)

    _messages = []
    paginator = ddb.get_paginator('scan')
    for page in paginator.paginate(TableName=os.environ.get('MESSAGE_TABLE_NAME')):
        _messages.extend(page['Items'])

    assert len(_messages) == 2


@mock_dynamodb2
def test_store_message_exceed_20(use_moto):
    ddb = use_moto()

    for i in range(19):
        ddb.put_item(
            TableName=os.environ.get('MESSAGE_TABLE_NAME'),
            Item={'myid': {'S': f'uuid-{i}'},
                  'timestamp': {'N': str(datetime.now().timestamp())},
                  'data': {'S': f'[2021-02-08 07:53:58 Zaki] test {i}'}}
        )

    data = '[2021-02-08 07:54:04 Zaki] test 2'

    # call store 2 times
    handler.store_message(data)
    handler.store_message(data)

    _messages = []
    paginator = ddb.get_paginator('scan')
    for page in paginator.paginate(TableName=os.environ.get('MESSAGE_TABLE_NAME')):
        _messages.extend(page['Items'])

    assert len(_messages) == 20


@mock_dynamodb2
def test_handle(apigw_event, mocker, use_moto, monkeypatch):
    ddb = use_moto()
    apigw_event['body'] = '{"message": "Hello world..."}'
    expected_connection_ids = [
        {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}},
        {'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
    ]

    def mock_store_message(data):
        assert 'Hello world...' in data
        assert 'foo' in data
        return None

    def mock_send_to_all(apig_management_client, connection_ids, data):
        assert 'Hello world...' in data
        assert 'foo' in data
        assert connection_ids == expected_connection_ids
        return None

    monkeypatch.setattr(handler, 'store_message', mock_store_message)
    monkeypatch.setattr(handler, "send_to_all", mock_send_to_all)
    handler.handle(apigw_event, mocker)
