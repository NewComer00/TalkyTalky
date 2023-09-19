import socket
from select import select
from gpt4all import GPT4All
from base import ServerBase


class LanguageModelServer(ServerBase):
    def __init__(self,
                 model_name="orca-mini-3b.ggmlv3.q4_0.bin", infer_device='cpu',
                 ip='127.0.0.1', port=12345, recv_buflen=10240):

        self._server_print("Initializing the server...")

        self.port = port
        self.server_ip = ip
        self.server_socket = None
        self.client_ip = None
        self.client_socket = None
        self.recv_buflen = recv_buflen

        self._server_print(
            f"Loading Language model {model_name} using {infer_device}")
        self.model = GPT4All(model_name, device=infer_device)

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
        with self.model.chat_session():
            # Communication loop
            while True:
                recv_data = self.client_socket.recv(
                    self.recv_buflen).decode('utf-8')
                if recv_data:
                    self._server_print(
                        f"Received from {self.client_ip} << {recv_data}")
                    response = self.model.generate(prompt=recv_data, temp=0)
                    self.client_socket.send(response.encode('utf-8'))
                    self._server_print(f"Send >> {response}")


if __name__ == '__main__':
    lms = LanguageModelServer()
    lms.connect()
    lms.run()
