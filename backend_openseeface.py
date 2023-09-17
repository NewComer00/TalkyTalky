import os
import time
import socket
import threading
from select import select
import pyttsx3

# Define server settings
HOST = '127.0.0.1'
PORT = 12346
DATA_FRAME_LEN = 10240

# Live2d frontend is listening...
LIVE2D_FRONTEND_IP = "127.0.0.1"
LIVE2D_FRONTEND_PORT = 11573

OPENSEEFACE_FRAME_LEN = 1785
OPENSEEFACE_EXPRESSIONS_DIR = r'expressions/openseeface/'


# List all expression files in the directory
expression_files = [f for f in os.listdir(OPENSEEFACE_EXPRESSIONS_DIR) if os.path.isfile(
    os.path.join(OPENSEEFACE_EXPRESSIONS_DIR, f))]

# read expressions into memory
expression_frames = {}
for file in expression_files:
    frames = []
    with open(os.path.join(OPENSEEFACE_EXPRESSIONS_DIR, file), 'rb') as fp:
        while True:
            frame = fp.read(OPENSEEFACE_FRAME_LEN)
            if not frame:
                break  # End of file
            frames.append(frame)
        expression_frames[file] = frames


# Create a UDP socket
live2d_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the host and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
print(f"Server is listening on {HOST}:{PORT}")
while True:
    server_socket.listen()
    # Accept incoming connections
    # Timeout set to 1 seconds
    ready, _, _ = select([server_socket], [], [], 1)
    if ready:
        client_socket, client_address = server_socket.accept()
        break
print(f"Connected to {client_address}")


ACTION_STATE = 'normal'


def action_daemon(live2d_sock, live2d_ip, live2d_port, exp_frames):
    global ACTION_STATE

    while True:
        if ACTION_STATE == 'normal':
            for frame in exp_frames['normal']:
                if ACTION_STATE != 'normal':
                    break
                live2d_sock.sendto(frame, (live2d_ip, live2d_port))
                time.sleep(0.04)

        elif ACTION_STATE == 'speaking':
            for frame in exp_frames['speaking']:
                if ACTION_STATE != 'speaking':
                    break
                live2d_sock.sendto(frame, (live2d_ip, live2d_port))
                time.sleep(0.04)


action_daemon_thread = threading.Thread(target=action_daemon, args=(
    live2d_udp_socket, LIVE2D_FRONTEND_IP, LIVE2D_FRONTEND_PORT, expression_frames))
action_daemon_thread.start()
# Communication loop
while True:
    bot_answer = client_socket.recv(DATA_FRAME_LEN).decode('utf-8')

    if len(bot_answer) > 0:
        print(f"Received: {bot_answer}")
        ACTION_STATE = 'speaking'
        pyttsx3.speak(bot_answer)
        ACTION_STATE = 'normal'
    else:
        pass

# Clean up
action_daemon_thread.join()
client_socket.close()
server_socket.close()
