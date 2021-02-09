import boto3
import os
import pytest

from moto import mock_dynamodb2
from send_notify import handler


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
        dynamodb.put_item(
            TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'),
            Item={'myid': {'S': 'counter'}, 'msgCount': {'N': '0'}}
        )
        return dynamodb
    return dynamodb_client


@mock_dynamodb2
def test_handle(apigw_event, mocker, use_moto, monkeypatch):
    ddb = use_moto()
    apig_management_client = boto3.client('apigatewaymanagementapi')
    expected_connection_ids = [
        {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}},
        {'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
    ]
    expected_data = f"Welcome to Simple Chat\n"\
                    f"There are {len(expected_connection_ids)} users connected.\n" \
                    f"Total of {0} messages recorded as of today.\n\n"

    def mock_get_messages():
        return []

    def mock_send_to_all(apig_management_client, connection_ids, data):
        assert data == 'foo has joined the chat room'
        assert connection_ids == expected_connection_ids
        return None

    def mock_send_to_self(apig_management_client, connection_id, data):
        assert connection_id == 'abc123='
        assert data == expected_data
        return None

    monkeypatch.setattr(handler, 'get_messages', mock_get_messages)
    monkeypatch.setattr(handler, "send_to_all", mock_send_to_all)
    monkeypatch.setattr(handler, "send_to_self", mock_send_to_self)
    handler.handle(apigw_event, mocker)


@mock_dynamodb2
def test_handle_with_messages(apigw_event, mocker, use_moto, monkeypatch):
    ddb = use_moto()
    apig_management_client = boto3.client('apigatewaymanagementapi')

    ddb.put_item(
        TableName=os.environ.get('MSG_COUNTER_TABLE_NAME'),
        Item={'myid': {'S': 'counter'}, 'msgCount': {'N': '2'}}
    )
    expected_connection_ids = [
        {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}},
        {'connectionId': {'S': 'def123='}, 'username': {'S': 'bar'}}
    ]
    expected_data = f"Welcome to Simple Chat\n"\
                    f"There are {len(expected_connection_ids)} users connected.\n" \
                    f"Total of {2} messages recorded as of today.\n\n"

    def mock_get_messages():
        return ['[2021-02-08 07:53:58 Zaki] test 1', '[2021-02-08 07:54:04 Zaki] test 2']

    messages = mock_get_messages()
    expected_data = expected_data + '\n'.join(messages)

    def mock_send_to_all(apig_management_client, connection_ids, data):
        assert data == 'foo has joined the chat room'
        assert connection_ids == expected_connection_ids
        return None

    def mock_send_to_self(apig_management_client, connection_id, data):
        assert connection_id == 'abc123='
        assert data == expected_data
        return None

    monkeypatch.setattr(handler, 'get_messages', mock_get_messages)
    monkeypatch.setattr(handler, "send_to_all", mock_send_to_all)
    monkeypatch.setattr(handler, "send_to_self", mock_send_to_self)
    handler.handle(apigw_event, mocker)


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
def test_send_to_self(use_moto, monkeypatch):
    ddb = use_moto()
    connection_id = {'connectionId': {'S': 'abc123='}, 'username': {'S': 'foo'}}
    data = 'test message'

    def mock_post_to_connection(Data, ConnectionId):
        assert Data == data
        assert ConnectionId == connection_id['connectionId']['S']
        return None

    apig_management_client = boto3.client('apigatewaymanagementapi')
    monkeypatch.setattr(apig_management_client, 'post_to_connection', mock_post_to_connection)
    handler.send_to_self(apig_management_client, connection_id['connectionId']['S'], data)


@mock_dynamodb2
def test_get_messages(use_moto):
    ddb = use_moto()

    ddb.put_item(
        TableName=os.environ.get('MESSAGE_TABLE_NAME'),
        Item={'myid': {'S': 'uuid-1'},
              'timestamp': {'N': '1612770838.718373'},
              'data': {'S': '[2021-02-08 07:53:58 Zaki] test 1'}}
    )
    ddb.put_item(
        TableName=os.environ.get('MESSAGE_TABLE_NAME'),
        Item={'myid': {'S': 'uuid-2'},
              'timestamp': {'N': '1612770844.578127'},
              'data': {'S': '[2021-02-08 07:54:04 Zaki] test 2'}}
    )

    messages = handler.get_messages()
    assert messages == ['[2021-02-08 07:53:58 Zaki] test 1', '[2021-02-08 07:54:04 Zaki] test 2']


@mock_dynamodb2
def test_get_messages_empty(use_moto):
    ddb = use_moto()

    messages = handler.get_messages()
    assert messages == []
