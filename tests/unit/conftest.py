import pytest


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('CONNECTION_TABLE_NAME', 'TestConnectionTable')
    monkeypatch.setenv('MSG_COUNTER_TABLE_NAME', 'TestMsgCounterTable')
    monkeypatch.setenv('MESSAGE_TABLE_NAME', 'TestMessageTable')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')


@pytest.fixture
def mocker():
    pass


@pytest.fixture
def apigw_event():
    return {
        'requestContext': {
            'connectionId': 'abc123=',
            'domainName': 'testdomain',
            'stage': 'test'
        },
    }
