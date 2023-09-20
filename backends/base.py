# TODO: Rewrite me using socketserver
# https://docs.python.org/3/library/socketserver.html
# https://stackoverflow.com/questions/12233940/passing-extra-metadata-to-a-requesthandler-using-pythons-socketserver-and-child

import socket
import datetime
from select import select


class ServerBase:
    def __init__(self, ip, port, recv_buflen):
        self._server_print("Initializing the server...")
        self.port = port
        self.server_ip = ip
        self.server_socket = None
        self.client_ip = None
        self.client_socket = None
        self.recv_buflen = recv_buflen

    def __del__(self):
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()

    def connect(self, listen_timeout=1):
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.port))

        self._server_print(f"Listening on {self.server_ip}:{self.port}")
        while True:
            self.server_socket.listen()
            # Accept incoming connections
            ready, _, _ = select([self.server_socket], [], [], listen_timeout)
            if ready:
                self.client_socket, self.client_ip = \
                    self.server_socket.accept()
                break
        self._server_print(f"Connected to {self.client_ip}")

    def run(self):
        pass

    def _server_print(self, msg):
        class_name = self.__class__.__name__
        obj_id = id(self)
        time_stamp = datetime.datetime.now(datetime.timezone.utc)
        print(f"[{time_stamp}][{class_name}@{obj_id}] {msg}")
