import socket
import select
import json

HEADER_LENGTH = 1024
HOST = '127.0.0.1'
PORT = 9009
SOCKETS_LIST = []
CLIENTS = {}


def get_user_data(client_socket):
    try:
        data_from_client = client_socket.recv(HEADER_LENGTH)
        # if a client closes a connection correctly
        if not len(data_from_client):
            return False

        message = json.loads(data_from_client)
        username = message['username']

        return {'username': username}
    except:
        return False


def parse_message_from_client(client_socket):
    try:
        data_from_client = client_socket.recv(HEADER_LENGTH)
        # if a client closes a connection correctly
        if not len(data_from_client):
            return False

        message = json.loads(data_from_client)
        message_type = message['message_type']
        sender = message['sender']
        data = message['data']

        return {'message_type': message_type, 'sender': sender, 'data': data}
    except:
        return False


def send_message_to_all_clients(username, data):
    data_to_client = {
        'message_type': 'message',
        'sender': username,
        'data': data

    }
    message = json.dumps(data_to_client)
    for client_socket in CLIENTS:
        client_socket.send(bytes(message, encoding="utf-8"))


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # to overcome the "Address already in use". This modifies the socket to allow us to reuse the address.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    SOCKETS_LIST.append(server_socket)

    print(f'Listening for connections on {HOST}:{PORT}...')

    while True:

        ready_to_read, ready_to_write, exception_sockets = select.select(SOCKETS_LIST, [], SOCKETS_LIST)
        for sock in ready_to_read:
            if sock == server_socket:
                client_socket, client_address = server_socket.accept()
                user = get_user_data(client_socket)

                if user is False:
                    continue
                SOCKETS_LIST.append(client_socket)
                CLIENTS[client_socket] = user

                print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['username']))
            else:
                message = parse_message_from_client(sock)
                user = CLIENTS[sock]
                client_name = user['username']
                data = message["data"]
                if message is False:
                    print('Closed connection from: {}'.format(client_name))
                    SOCKETS_LIST.remove(sock)
                    del CLIENTS[sock]
                    continue

                print(f'Received message from {client_name}: {data}')

                send_message_to_all_clients(client_name, data)

            for notified_socket in exception_sockets:
                SOCKETS_LIST.remove(notified_socket)
                del CLIENTS[notified_socket]


if __name__ == "__main__":
    main()
