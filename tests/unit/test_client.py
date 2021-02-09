import client
import termcolor
import websocket

from click.testing import CliRunner


def test_on_message(mocker, monkeypatch):
    def mock_colored(msg, color):
        assert msg == 'hello world...'
        assert color == 'green'
        return None

    monkeypatch.setattr(termcolor, 'colored', mock_colored)
    message = 'hello world...'
    client.on_message(mocker, message)


def test_on_error(mocker, monkeypatch):
    def mock_colored(msg, color):
        assert msg == 'error found'
        assert color == 'red'
        return None

    monkeypatch.setattr(termcolor, 'colored', mock_colored)
    message = 'error found'
    client.on_error(mocker, message)


def test_on_close(monkeypatch):
    def mock_colored(msg, color):
        assert msg == 'Bye! See you again.'
        assert color == 'blue'
        return None

    def mock_close():
        return None

    class Struct(object):
        pass

    mocker = Struct()
    mocker.close = Struct()

    monkeypatch.setattr(termcolor, 'colored', mock_colored)
    monkeypatch.setattr(mocker, 'close', mock_close)
    client.on_close(mocker)


def test_main(monkeypatch):
    runner = CliRunner()

    def mock_web_socket_app(ws_url, on_message, on_error, on_close):
        assert ws_url == 'wss://testdomain/test?username=Test User'

        class Struct(object):
            def run_forever(self):
                pass

        mocker = Struct()
        mocker.on_open = None

        return mocker

    monkeypatch.setattr(websocket, 'WebSocketApp', mock_web_socket_app)
    mock_ws_server_url = 'wss://testdomain/test'
    mock_username = 'Test User'
    result = runner.invoke(client.main, ['--server-url', mock_ws_server_url, '--username', mock_username])

    assert result.exit_code == 0
