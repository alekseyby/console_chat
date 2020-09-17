from threading import Condition, Thread
import socket
import errno
import sys

cv = Condition()


def refresh_client_window():
    while True:
        with cv:
            try:
                username_header = client_socket.recv(HEADER_LENGTH)
                if not len(username_header):
                    print('Connection closed by the server')
                    sys.exit()

                username_length = int(username_header.decode('utf-8').strip())
                username = client_socket.recv(username_length).decode('utf-8')
                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket.recv(message_length).decode('utf-8')
                print(f'{username} > {message}')
            except IOError as ex:
                if ex.errno != errno.EAGAIN and ex.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(ex)))
                    sys.exit()
                cv.wait(0.2)
            except Exception as ex:
                print('Reading error: {}'.format(str(ex)))
                sys.exit()


if (len(sys.argv) < 3):
    print('To run : python client.py hostname port (e.g python client.py localhost 9009)')
    sys.exit()

HEADER_LENGTH = 1024
IP = sys.argv[1]
PORT = int(sys.argv[2])

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((IP, PORT))
    client_socket.setblocking(False)
except:
    print('Unable to connect')
    sys.exit()

my_username = input("Username: ")
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)
thread1 = Thread(
    target=refresh_client_window)
thread1.start()

while True:
    try:
        # message = input(f'{my_username} > ')
        message = input()
        if message:
            message = message.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(message_header + message)
            with cv:
                cv.notify_all()
    except Exception as ex:
        print('Reading error: {}'.format(str(ex)))
        sys.exit()
