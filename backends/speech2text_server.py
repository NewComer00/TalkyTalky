from faster_whisper import WhisperModel
from base import ServerBase


class Speech2TextServer(ServerBase):
    def __init__(self,
                 model_name="base.en", infer_device='cpu', compute_type='int8',
                 ip='127.0.0.1', port=12344, recv_buflen=1024):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

        self._server_print(
            f"Loading speech-to-text model {model_name} using {infer_device}")
        self.model = WhisperModel(model_name, device=infer_device,
                                  compute_type=compute_type)

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
