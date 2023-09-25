import os
import sys
import time
import wave
import tempfile
import argparse
from multiprocessing import Process

import pyaudio
from termcolor import colored
from textual import work
from textual.widgets import Header, Footer
from textual.widgets import Log, RichLog
from textual.app import App, ComposeResult

from service.action import ActionServer, ActionClient
from service.language_model import LanguageModelServer, LanguageModelClient
from service.speech2text import Speech2TextServer, Speech2TextClient
from service.text2speech import EdgettsServer, Pyttsx3Server


def config():
    parser = argparse.ArgumentParser(description="Text-to-Speech Engine")
    parser.add_argument(
        "--tts",
        default="pyttsx3",
        choices=["pyttsx3", "edge-tts"],
        help="Select the text-to-speech engine \
                (valid values: pyttsx3, edge-tts)",
    )
    args = parser.parse_args()

    print(colored("======== Application Configuration Begin ========", 'green'))
    print(f"Text-to-Speech Engine: {args.tts}")
    print(colored("======== Application Configuration End ========", 'green'))
    return args


def run_action_server():
    sys.stdout = None
    acts = ActionServer()
    acts.connect()
    acts.run()


def run_language_server():
    sys.stdout = None
    lms = LanguageModelServer()
    lms.connect()
    lms.run()


def run_speech2text_server():
    sys.stdout = None
    s2ts = Speech2TextServer()
    s2ts.connect()
    s2ts.run()


def run_tts_server(tts_engine):
    sys.stdout = None
    if tts_engine == "pyttsx3":
        ttss = Pyttsx3Server()
    elif tts_engine == "edge-tts":
        ttss = EdgettsServer()
    else:
        ttss = Pyttsx3Server()
    ttss.connect()
    ttss.run()


class ChatBox(RichLog):
    def __init__(self):
        super().__init__(wrap=True, highlight=True, markup=True)


class LogBox(Log):
    def __init__(self):
        super().__init__(auto_scroll=True)


class TalkyTalkyApp(App):

    CSS_PATH = "talkytalkyapp.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("q", "quit", "Quit")]

    def __init__(self):
        self.speech2text_client = Speech2TextClient()
        self.language_model_client = LanguageModelClient()
        self.action_client = ActionClient()

        self.speech2text_client.connect()
        self.language_model_client.connect()
        self.action_client.connect()

        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk = 1024

        self.pyaudio_obj = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_obj.open(
            format=self.audio_format,
            channels=self.audio_channels,
            rate=self.audio_rate, input=True,
            frames_per_buffer=self.audio_chunk)

        self.is_recording = False
        self.is_answering = False

        self.chatbox = None
        self.logbox = None

        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield ChatBox()
        yield LogBox()

    def on_ready(self) -> None:
        self.chatbox = self.query_one(ChatBox)
        self.logbox = self.query_one(LogBox)
        self.logbox.begin_capture_print()
        self.chatbox.write(
            "[blink bold green]Press SPACE to start speaking[/blink bold green]")
        self.chatbox.write(
            "[blink bold green]Press SPACE again when finish speaking[/blink bold green]")

        self.interact()

    def key_space(self) -> None:
        if not self.is_answering:
            if self.is_recording:
                self.is_recording = False
                self.logbox.write(
                    "[ Finish Recording ]")
            else:
                self.is_recording = True
                self.logbox.write_line(
                    "[ Start Recording ]")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    @work(exclusive=True, thread=True)
    def interact(self):

        frames = []
        while True:
            self.audio_stream.start_stream()
            frames.clear()

            # start recording if key is pressed
            while self.is_recording:
                data = self.audio_stream.read(self.audio_chunk)
                frames.append(data)
                # recording progress bar
                self.logbox.write('>')

            self.audio_stream.stop_stream()

            # Save the recorded audio to a WAV file
            if len(frames) > 0:
                self.is_answering = True

                wav_fp, wav_path = tempfile.mkstemp()
                wf = wave.open(wav_path, 'wb')
                wf.setnchannels(self.audio_channels)
                wf.setsampwidth(
                    self.pyaudio_obj.get_sample_size(self.audio_format))
                wf.setframerate(self.audio_rate)
                wf.writeframes(b''.join(frames))
                wf.close()

                # speech to text
                self.chatbox.write('')
                prompt = self.speech2text_client.get_text(wav_path)
                os.close(wav_fp)
                os.remove(wav_path)

                # print my prompt words
                me = '[bold red]ME  >> [/bold red]'
                self.chatbox.write(me + prompt)
                if prompt == '[EMPTY SPEECH]':
                    answer = "Sorry, I can't hear you clearly. Please try again."
                else:
                    # get answer from the prompt
                    answer = self.language_model_client.get_answer(prompt)

                her = '[bold green]BOT >> [/bold green]'
                self.chatbox.write(her + answer)
                self.chatbox.write('')

                # make reaction to the answer
                self.action_client.react_to(answer)

                self.is_answering = False

            time.sleep(0.1)

        self.audio_stream.close()
        self.pyaudio_obj.terminate()


if __name__ == "__main__":
    app_cfg = config()

    proc_action_server = Process(target=run_action_server)
    proc_action_server.daemon = True
    proc_action_server.start()

    proc_language_server = Process(target=run_language_server)
    proc_language_server.daemon = True
    proc_language_server.start()

    proc_speech2text_server = Process(target=run_speech2text_server)
    proc_speech2text_server.daemon = True
    proc_speech2text_server.start()

    proc_tts_server = Process(target=run_tts_server, args=(app_cfg.tts,))
    proc_tts_server.daemon = True
    proc_tts_server.start()

    app = TalkyTalkyApp()
    app.run()
