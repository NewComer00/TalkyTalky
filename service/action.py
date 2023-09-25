import os
import time
import enum
import socket
import threading
from service.base import ServerBase, ClientBase
from service.text2speech import Text2SpeechClient


class Action(enum.Enum):
    IDLE = 'idle'
    SPEAKING = 'speaking'


class ActionClient(ClientBase):
    def __init__(self,
                 server_ip='127.0.0.1', server_port=12346, recv_buflen=4096):

        super().__init__(server_ip=server_ip, server_port=server_port,
                         recv_buflen=recv_buflen)

    def react_to(self, sentence):
        self.socket.sendall(sentence.encode('utf-8'))
        self.socket.recv(self.recv_buflen).decode('utf-8')


class ActionServer(ServerBase):

    OPENSEEFACE_FRAME_LEN = 1785
    OPENSEEFACE_ACTION_DIR = r'action/openseeface/'

    def __init__(self,
                 action_fps: int = 24,
                 tts_server_ip: str = '127.0.0.1',
                 tts_server_port: int = 12347,
                 openseeface_client_ip: str = '127.0.0.1',
                 openseeface_client_port: int = 11573,
                 ip: str = '127.0.0.1',
                 port: str = 12346,
                 recv_buflen: int = 4096):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

        self.tts_client = Text2SpeechClient(tts_server_ip, tts_server_port)

        # the role is in the idle state by default
        self.actor_state = Action.IDLE
        self.action_fps = action_fps
        self.action_daemon_thread = None

        self.openseeface_client_ip = openseeface_client_ip
        self.openseeface_client_port = openseeface_client_port
        # Openseeface uses UDP, so we init the socket here
        self.openseeface_client_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.openseeface_actions = self._init_actions()

    def __del__(self):
        super().__del__()

        if self.openseeface_client_socket:
            self.openseeface_client_socket.close()
        if self.action_daemon_thread:
            self.action_daemon_thread.join()

    def connect(self, listen_timeout=1):
        super().connect(listen_timeout)
        self.tts_client.connect()

    def run(self):
        self.action_daemon_thread = threading.Thread(
            target=self._action_daemon)
        self.action_daemon_thread.daemon = True
        self.action_daemon_thread.start()

        # Communication loop
        while True:
            bot_answer = self.client_socket.recv(
                self.recv_buflen).decode('utf-8')

            if bot_answer:
                self._server_log(
                    f"Received from {self.client_ip} << {bot_answer}")
                iter_reader = self.tts_client.read_aloud(bot_answer)
                next(iter_reader)
                self.actor_state = Action.SPEAKING
                next(iter_reader)
                self.actor_state = Action.IDLE

                response = "[ACTION DONE]"
                self.client_socket.sendall(response.strip().encode('utf-8'))
                self._server_log(f"Send >> {response}")

    def _init_actions(self):
        # List all action files in the directory
        action_files = [f for f in os.listdir(
            ActionServer.OPENSEEFACE_ACTION_DIR) if os.path.isfile(
            os.path.join(ActionServer.OPENSEEFACE_ACTION_DIR, f))]

        # Read actions into memory
        action_frames = {}
        for file in action_files:
            # Filename should be the valid value of Enum Action
            if any((file == a.value) for a in Action):
                action = Action(file)
            else:
                continue

            frames = []
            with open(os.path.join(
                    ActionServer.OPENSEEFACE_ACTION_DIR, file),
                    'rb') as fp:
                while True:
                    frame = fp.read(ActionServer.OPENSEEFACE_FRAME_LEN)
                    if not frame:
                        break  # End of file
                    frames.append(frame)
                action_frames[action] = frames
        return action_frames

    # Perform different actions based on self.actor_state
    def _action_daemon(self):
        delay = 1 / self.action_fps
        while True:
            for action in Action:
                if self.actor_state is action:
                    for frame in self.openseeface_actions[action]:
                        if self.actor_state is not action:
                            break
                        self.openseeface_client_socket.sendto(
                            frame, (self.openseeface_client_ip,
                                    self.openseeface_client_port))
                        time.sleep(delay)
                    break


if __name__ == '__main__':
    acts = ActionServer()
    acts.connect()
    acts.run()
