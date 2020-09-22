import socket
import select
import json
from datetime import datetime
from random import randint
import argparse

HEADER_LENGTH = 1024
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
        data = message['data']
        return {'message_type': message_type, 'data': data}
    except:
        return False


def send_message_to_another_clients_from(client_socket, message_type, username, data):
    data_to_client = {
        'message_type': message_type,
        'sender': username,
        'data': data

    }
    message = json.dumps(data_to_client)
    for sock in CLIENTS:
        if sock != client_socket:
            sock.send(bytes(message, encoding="utf-8"))


def send_message_to_client(client_socket, message_type, username, data):
    data_to_client = {
        'message_type': message_type,
        'sender': username,
        'data': data
    }
    message = json.dumps(data_to_client)
    client_socket.send(bytes(message, encoding="utf-8"))


def rock_paper_scissors_game(command):
    error_msg = "Incorrect command format. Please enter again: 'cmd!start_game:option' " \
                "where option is one of the proposed: rock, scissors, paper"
    index = command.find(":")
    if index == -1:
        return error_msg

    client_option = command[index + 1:]

    options = ["rock", "paper", "scissors"]

    if client_option not in options:
        return error_msg

    server_option = options[randint(0, 2)]
    game_result = ""

    if client_option == server_option:
        game_result = "Tie!"
    elif client_option == "rock":
        if server_option == "paper":
            game_result = "You lose!"
        else:
            game_result = "You win!"
    elif client_option == "paper":
        if server_option == "scissors":
            game_result = "You lose!"
        else:
            game_result = "You win!"
    elif client_option == "scissors":
        if server_option == "rock":
            game_result = "You lose!"
        else:
            game_result = "You win!"
    return game_result + " Server option: {}, your option {}".format(server_option, client_option)


def main(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # to overcome the "Address already in use". This modifies the socket to allow us to reuse the address.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    SOCKETS_LIST.append(server_socket)

    print(f'Listening for connections on {host}:{port}...')

    while True:
        ready_to_read, ready_to_write, exception_sockets = select.select(SOCKETS_LIST, [], SOCKETS_LIST)
        for sock in ready_to_read:
            if sock == server_socket:
                client_socket, client_address = server_socket.accept()
                user = get_user_data(client_socket)
                if user is False:
                    client_socket.close()
                    continue

                SOCKETS_LIST.append(client_socket)
                CLIENTS[client_socket] = user
                print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['username']))
            else:
                message = parse_message_from_client(sock)
                user = CLIENTS[sock]
                client_name = user['username']

                if message is False:
                    print('Closed connection from: {}'.format(client_name))
                    SOCKETS_LIST.remove(sock)
                    del CLIENTS[sock]
                    sock.close()
                    continue

                message_type = message['message_type']
                if message_type == "command":
                    command = str(message['data'])
                    print("The client '{}' has requested the command: '{}'".format(client_name, command))
                    if command == "cmd!client_exit" or command == "cmd!error":
                        data = "Client '{}' left the chat".format(client_name)
                        send_message_to_another_clients_from(sock, 'system_message', client_name, data)
                        SOCKETS_LIST.remove(sock)
                        del CLIENTS[sock]
                        sock.close()
                        continue
                    elif command == "cmd!participants_count":
                        data = "Participants count: {}".format(len(CLIENTS))
                        send_message_to_client(sock, 'system_message', client_name, data)
                        continue
                    elif command == "cmd!current_time":
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        data = "Current time: {}".format(current_time)
                        send_message_to_client(sock, 'system_message', client_name, data)
                        continue
                    elif command.startswith("cmd!start_game"):
                        data = rock_paper_scissors_game(command)
                        send_message_to_client(sock, 'system_message', client_name, data)
                        continue
                    else:
                        data = "The command: '{}' is not supported by the server".format(command)
                        send_message_to_client(sock, 'system_message', client_name, data)
                        continue

                data = message['data']
                print(f'Received message from {client_name}: {data}')

                send_message_to_another_clients_from(sock, 'message', client_name, data)

            for notified_socket in exception_sockets:
                SOCKETS_LIST.remove(notified_socket)
                del CLIENTS[notified_socket]
                sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Server will be reachable by this address.(default = 127.0.0.1)",
                        type=str, default='127.0.0.1')
    parser.add_argument("--port", help="Server will listening this port. (default = 9009)", type=int,
                        default=9009)
    args = parser.parse_args()
    main(args.host, args.port)
