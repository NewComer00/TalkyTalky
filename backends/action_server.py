import os
import time
import enum
import socket
import threading
import pyttsx3
from base import ServerBase


class Action(enum.Enum):
    IDLE = 'idle'
    SPEAKING = 'speaking'


class ActionServer(ServerBase):

    OPENSEEFACE_FRAME_LEN = 1785
    OPENSEEFACE_ACTION_DIR = r'actions/openseeface/'

    def __init__(self,
                 action_fps=24,
                 openseeface_client_ip='127.0.0.1',
                 openseeface_client_port=11573,
                 ip='127.0.0.1', port=12346, recv_buflen=10240):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)

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
                self._server_print(
                    f"Received from {self.client_ip} << {bot_answer}")
                self.actor_state = Action.SPEAKING
                pyttsx3.speak(bot_answer)
                self.actor_state = Action.IDLE

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
