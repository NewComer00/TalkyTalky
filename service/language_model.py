from gpt4all import GPT4All
from service.base import ServerBase, ClientBase


class LanguageModelClient(ClientBase):
    def __init__(self,
                 server_ip='127.0.0.1', server_port=12345, recv_buflen=4096):

        super().__init__(server_ip=server_ip, server_port=server_port,
                         recv_buflen=recv_buflen)

    def get_answer(self, prompt):
        self.socket.sendall(prompt.encode('utf-8'))
        answer = self.socket.recv(self.recv_buflen).decode('utf-8')
        return answer


class LanguageModelServer(ServerBase):
    def __init__(self,
                 model_name="orca-mini-3b.ggmlv3.q4_0.bin", infer_device='cpu',
                 ip='127.0.0.1', port=12345, recv_buflen=4096):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

        self._server_log(
            f"Loading Language model {model_name} using {infer_device}")
        self.model = GPT4All(model_name, device=infer_device)

    def run(self):
        with self.model.chat_session():
            # Communication loop
            while True:
                recv_data = self.client_socket.recv(
                    self.recv_buflen).decode('utf-8').strip()
                self._server_log(
                    f"Received from {self.client_ip} << {recv_data}")

                response = self.model.generate(prompt=recv_data, temp=0)
                self.client_socket.sendall(response.strip().encode('utf-8'))
                self._server_log(f"Send >> {response}")


if __name__ == '__main__':
    lms = LanguageModelServer()
    lms.connect()
    lms.run()
