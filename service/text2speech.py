import os
import asyncio
import platform
import tempfile
from pathlib import Path
import pyttsx3
import edge_tts
from playsound import playsound
from service.base import ServerBase, ClientBase


class Text2SpeechClient(ClientBase):
    def __init__(self,
                 server_ip='127.0.0.1', server_port=12347, recv_buflen=4096):

        super().__init__(server_ip=server_ip, server_port=server_port,
                         recv_buflen=recv_buflen)

    def read_aloud(self, text):
        self.socket.sendall(text.encode('utf-8'))
        start_reading = self.socket.recv(self.recv_buflen).decode('utf-8')
        yield start_reading
        finish_reading = self.socket.recv(self.recv_buflen).decode('utf-8')
        yield finish_reading


class Text2SpeechServerBase(ServerBase):
    def __init__(self,
                 voice="",
                 ip='127.0.0.1', port=12347, recv_buflen=4096):

        super().__init__(ip=ip, port=port, recv_buflen=recv_buflen)
        self.voice = voice

    def run(self):
        # Communication loop
        while True:
            recv_data = self.client_socket.recv(
                self.recv_buflen).decode('utf-8')
            self._server_log(
                f"Received from {self.client_ip} << {recv_data}")

            self._text_to_speech(recv_data)

    def _text_to_speech(self, text):
        response = '[START READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")
        pass
        response = '[FINISH READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")


class Pyttsx3Server(Text2SpeechServerBase):
    def _text_to_speech(self, text):
        response = '[START READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")

        pyttsx3.speak(text)

        response = '[FINISH READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")


class EdgettsServer(Text2SpeechServerBase):
    def __init__(self,
                 voice="en-US-AriaNeural",
                 ip='127.0.0.1', port=12347, recv_buflen=4096):

        super().__init__(voice=voice,
                         ip=ip, port=port, recv_buflen=recv_buflen)

    def _text_to_speech(self, text):
        async def amain(text, voice, output_file):
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

        mp3_fp, mp3_path = tempfile.mkstemp(suffix='.mp3')

        # https://stackoverflow.com/a/70758881/15283141
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.get_event_loop_policy().get_event_loop()
        try:
            loop.run_until_complete(amain(text, self.voice, mp3_path))
        finally:
            loop.close()

        response = '[START READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")

        # To solve playsound issue: a problem occurred in initializing MCI
        os.close(mp3_fp)
        playsound(Path(mp3_path).as_uri())
        os.remove(mp3_path)

        response = '[STOP READING]'
        self.client_socket.send(response.encode('utf-8'))
        self._server_log(f"Send >> {response}")


if __name__ == '__main__':
    ttss = Pyttsx3Server()
    ttss.connect()
    ttss.run()
