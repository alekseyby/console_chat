from threading import Condition, Thread
import socket
import errno
import sys
import json
import argparse

HEADER_LENGTH = 1024

cv = Condition()


def register_client(client_socket, username):
    data_to_server = {
        'username': username
    }
    message = json.dumps(data_to_server)
    client_socket.send(bytes(message, encoding="utf-8"))


def send_message(client_socket, message_type, data):
    data_to_server = {
        'message_type': message_type,
        'data': data
    }
    message = json.dumps(data_to_server)
    client_socket.send(bytes(message, encoding="utf-8"))


def get_message(client_socket):
    data_from_server = client_socket.recv(HEADER_LENGTH)
    # if a client closes a connection correctly
    if not len(data_from_server):
        print('Connection closed by the server')
        client_socket.close()
        sys.exit()

    message = json.loads(data_from_server)
    return message


def refresh_client_window(client_socket):
    while True:
        with cv:
            try:
                message = get_message(client_socket)

                message_type = message['message_type']
                sender = message['sender']
                data = message['data']

                if message_type == 'system_message':
                    print(f'{data}')
                else:
                    print(f'{sender} > {data}')
            except IOError as ex:
                if ex.errno != errno.EAGAIN and ex.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(ex)))
                    client_socket.close()
                    sys.exit()
                cv.wait(0.2)
            except Exception as ex:
                print('Reading error: {}'.format(str(ex)))
                send_message(client_socket, "command", "cmd!error")
                client_socket.close()
                sys.exit()


def main(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        client_socket.setblocking(False)
    except:
        print('Unable to connect')
        client_socket.close()
        sys.exit()

    username = input("Username: ")
    register_client(client_socket, username)
    thread1 = Thread(target=refresh_client_window, args=(client_socket,))
    thread1.start()

    while True:
        try:
            data = input()
            if data:
                print(f'{username} > {data}')
                if data.startswith("cmd!"):
                    send_message(client_socket, "command", data)
                else:
                    send_message(client_socket, "message", data)
                with cv:
                    cv.notify_all()
        except KeyboardInterrupt:
            send_message(client_socket, "command", "cmd!client_exit")
            client_socket.close()
            sys.exit()
        except Exception as ex:
            print('Reading error: {}'.format(str(ex)))
            send_message(client_socket, "command", "cmd!error")
            client_socket.close()
            sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="Client will be connected to this address.(default = 127.0.0.1)", type=str,
                        default='127.0.0.1')
    parser.add_argument("--port", help="Client will be connected to this port. (default = 9009)",
                        type=int, default=9009)
    args = parser.parse_args()
    main(args.host, args.port)
