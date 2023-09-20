import socket
from select import select
from faster_whisper import WhisperModel
from base import ServerBase


class Speech2TextServer(ServerBase):
    def __init__(self,
                 model_name="base.en", infer_device='cpu', compute_type='int8',
                 ip='127.0.0.1', port=12344, recv_buflen=1024):

        self._server_print("Initializing the server...")

        self.port = port
        self.server_ip = ip
        self.server_socket = None
        self.client_ip = None
        self.client_socket = None
        self.recv_buflen = recv_buflen

        self._server_print(
            f"Loading speech-to-text model {model_name} using {infer_device}")
        self.model = WhisperModel(model_name, device=infer_device,
                                  compute_type=compute_type)

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
        # Communication loop
        while True:
            recv_data = self.client_socket.recv(
                self.recv_buflen).decode('utf-8')
            if recv_data:
                self._server_print(
                    f"Received from {self.client_ip} << {recv_data}")

                wav_file_path = recv_data
                speech_text = self._speech_to_text(wav_file_path)
                response = speech_text

                self.client_socket.send(response.encode('utf-8'))
                self._server_print(f"Send >> {response}")

    def _speech_to_text(self, wav_file_path):
        segments, _ = self.model.transcribe(wav_file_path)
        segments = list(segments)
        speech_text = ''.join([seg.text for seg in segments])

        return speech_text


if __name__ == '__main__':
    sts = Speech2TextServer()
    sts.connect()
    sts.run()
