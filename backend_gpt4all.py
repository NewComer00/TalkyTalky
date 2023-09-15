from gpt4all import GPT4All
import socket
from select import select

# Define server settings
HOST = '127.0.0.1'  # Loopback address for local communication
PORT = 12345       # Port to listen on

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the host and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
print(f"Server is listening on {HOST}:{PORT}")
while True:
    server_socket.listen()
    # Accept incoming connections
    ready, _, _ = select([server_socket], [], [], 1) #Timeout set to 1 seconds
    if ready:
        client_socket, client_address = server_socket.accept()
        break
print(f"Connected to {client_address}")

model = GPT4All("orca-mini-3b.ggmlv3.q4_0.bin")
with model.chat_session():

    # Communication loop
    while True:
        data = client_socket.recv(1024).decode('utf-8')  # Receive data from the client
        if not data:
            pass
        print(f"Received: {data}")

        response = model.generate(prompt=data, temp=0)
        # Send a response to the client
        client_socket.send(response.encode('utf-8'))

# Clean up
client_socket.close()
server_socket.close()
