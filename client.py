from threading import Condition, Thread
import socket
import errno
import sys
import json

HEADER_LENGTH = 1024
IP = '127.0.0.1'
PORT = 9009

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
                    sys.exit()
                cv.wait(0.2)
            except Exception as ex:
                print('Reading error: {}'.format(str(ex)))
                send_message(client_socket, "command", "cmd!error")
                client_socket.close()
                sys.exit()


def main():
    # if (len(sys.argv) < 3):
    #     print('To run : python client.py hostname port (e.g python client.py localhost 9009)')
    #     sys.exit()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((IP, PORT))
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
    main()
