import socket
import select

HEADER_LENGTH = 1024
HOST = '127.0.0.1'
PORT = 9009
SOCKET_LIST = []
CLIENTS = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
SOCKET_LIST.append(server_socket)

print(f'Listening for connections on {HOST}:{PORT}...')


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False


while True:

    ready_to_read, ready_to_write, exception_sockets = select.select(SOCKET_LIST, [], SOCKET_LIST)
    for sock in ready_to_read:
        if sock == server_socket:
            client_socket, client_address = server_socket.accept()
            SOCKET_LIST.append(client_socket)

            print(f'Client connected: {client_address}')

            user = receive_message(client_socket)
            #print(user)
            if user is False:
                continue
            SOCKET_LIST.append(client_socket)
            CLIENTS[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                            user['data'].decode('utf-8')))
        else:
            message = receive_message(sock)
            if message is False:
                print('Closed connection from: {}'.format(CLIENTS[sock]['data'].decode('utf-8')))
                SOCKET_LIST.remove(sock)
                del CLIENTS[sock]
                continue

            user = CLIENTS[sock]

            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            for client_socket in CLIENTS:
                if client_socket != sock:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])


        for notified_socket in exception_sockets:
            SOCKET_LIST.remove(notified_socket)
            del CLIENTS[notified_socket]