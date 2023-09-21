import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 11573

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

DATA_FRAME_LEN = 1785

file_path = "received_data.bin"

with open(file_path, "wb") as file:
    while True:
        try:
            # Receive data from the UDP socket
            data, addr = sock.recvfrom(2048)  # 1024 is the buffer size, you can adjust it as needed

            # Write the received binary data to the file
            if len(data) == DATA_FRAME_LEN:
                file.write(data)

            # Optionally, you can print a message to confirm data reception
            print(f"Received {len(data)} bytes from {addr}")

        except KeyboardInterrupt:
            # Close the socket and exit if the user interrupts with Ctrl+C
            sock.close()
            break
