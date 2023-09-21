import socket
import time

UDP_IP = "127.0.0.1"  # Replace with the IP address of the UDP server
UDP_PORT = 11573  # Replace with the port number the UDP server is listening on

# Open the binary file for reading
file_path = "received_data.bin"  # Replace with the path to your binary file
frames = []

with open(file_path, "rb") as file:
    while True:
        frame = file.read(1785)  # Read one frame (1785 bytes) from the binary file
        if not frame:
            break  # End of file

        frames.append(frame)

# Create a UDP socket and send each frame in the list
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    for frame in frames:
        sock.sendto(frame, (UDP_IP, UDP_PORT))

        # Optionally, you can print a message to confirm frame transmission
        print(f"Sent {len(frame)} bytes")
        time.sleep(1/25)

sock.close()

print("Transmission complete.")

