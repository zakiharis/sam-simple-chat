import time
import _thread as thread

import click
import websocket

from termcolor import colored


def on_message(ws, message):
    """
    Handle on_message event.

    :param ws: websocket instance
    :param message: Message received
    :return:
    """
    print(colored(message, "green"))


def on_error(ws, error):
    """
    Handle on_error event

    :param ws: websocket instance
    :param error: Error message received
    :return:
    """
    print(colored(error, "red"))


def on_close(ws):
    """
    Handle on_close event

    :param ws: websocket instance
    :return:
    """
    print(colored("Bye! See you again.", "blue"))
    ws.close()


def on_open(ws):
    """
    Handle on_open event

    :param ws: websocket instance
    :return:
    """
    def run():
        ws.send('{"action": "sendnotify"}')

        while True:
            message = input()
            print("\033[A\033[A")  # clear the entered input
            data = f'{{"action": "sendmessage", "message": "{message}"}}'
            ws.send(data)
            time.sleep(1)
    thread.start_new_thread(run, ())


@click.command()
@click.option("--server-url", default="wss://nss4v73glk.execute-api.ap-southeast-1.amazonaws.com/Prod", help="Websocket Server URL")
@click.option("--username", prompt="Your username", help="Your chat username")
def main(server_url, username):
    """
    Main method to start chat client.

    :param server_url: WebSocket server url
    :param username: A username to chat
    :return:
    """
    ws_url = f"{server_url}?username={username}"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


if __name__ == '__main__':
    main()
