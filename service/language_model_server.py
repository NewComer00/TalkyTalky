from gpt4all import GPT4All
from base import ServerBase


class LanguageModelServer(ServerBase):
    def __init__(self,
                 model_name="orca-mini-3b.ggmlv3.q4_0.bin", infer_device='cpu',
                 ip='127.0.0.1', port=12345, recv_buflen=10240):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

        self._server_log(
            f"Loading Language model {model_name} using {infer_device}")
        self.model = GPT4All(model_name, device=infer_device)

    def run(self):
        with self.model.chat_session():
            # Communication loop
            while True:
                recv_data = self.client_socket.recv(
                    self.recv_buflen).decode('utf-8')
                if recv_data:
                    self._server_log(
                        f"Received from {self.client_ip} << {recv_data}")
                    response = self.model.generate(prompt=recv_data, temp=0)
                    self.client_socket.send(response.encode('utf-8'))
                    self._server_log(f"Send >> {response}")


if __name__ == '__main__':
    lms = LanguageModelServer()
    lms.connect()
    lms.run()
