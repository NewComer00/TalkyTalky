from faster_whisper import WhisperModel
from service.base import ServerBase, ClientBase


class Speech2TextClient(ClientBase):
    def __init__(self,
                 server_ip='127.0.0.1', server_port=12344, recv_buflen=4096):

        super().__init__(server_ip=server_ip, server_port=server_port,
                         recv_buflen=recv_buflen)

    def get_text(self, wav_file_path):
        self.socket.sendall(wav_file_path.encode('utf-8'))
        answer = self.socket.recv(self.recv_buflen).decode('utf-8')
        return answer


class Speech2TextServer(ServerBase):
    def __init__(self,
                 model_dir, model_name="base.en",
                 infer_device='cpu', compute_type='int8',
                 ip='127.0.0.1', port=12344, recv_buflen=4096):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

        self._server_log(
            f"Loading speech-to-text model {model_name} using {infer_device}")
        try:
            # we first try to use the local model
            self.model = WhisperModel(model_name, download_root=model_dir,
                                      device=infer_device,
                                      compute_type=compute_type,
                                      local_files_only=True)
        except FileNotFoundError:
            self.model = WhisperModel(model_name, download_root=model_dir,
                                      device=infer_device,
                                      compute_type=compute_type,
                                      local_files_only=False)


    def run(self):
        # Communication loop
        while True:
            recv_data = self.client_socket.recv(
                self.recv_buflen).decode('utf-8')
            self._server_log(
                f"Received from {self.client_ip} << {recv_data}")

            wav_file_path = recv_data
            speech_text = self._speech_to_text(wav_file_path)
            response = speech_text

            self.client_socket.send(response.encode('utf-8'))
            self._server_log(f"Send >> {response}")

    def _speech_to_text(self, wav_file_path):
        segments, _ = self.model.transcribe(wav_file_path)
        segments = list(segments)
        speech_text = ''.join([seg.text for seg in segments]).strip()

        # deal with empty speech
        if len(speech_text) == 0:
            speech_text = "[EMPTY SPEECH]"

        return speech_text


if __name__ == '__main__':
    sts = Speech2TextServer()
    sts.connect()
    sts.run()
