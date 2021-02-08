import time
import _thread as thread

import click
import websocket

from termcolor import colored


def on_message(ws, message):
    """

    :param ws:
    :param message:
    :return:
    """
    print(colored(message, "green"))


def on_error(ws, error):
    """

    :param ws:
    :param error:
    :return:
    """
    print(colored(error, "red"))


def on_close(ws):
    """

    :param ws:
    :return:
    """
    print(colored("Bye! See you again.", "blue"))
    ws.close()


def on_open(ws):
    """

    :param ws:
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

    :param server_url:
    :param username:
    :return:
    """
    ws_url = f"{server_url}?username={username}"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


if __name__ == '__main__':
    main()
