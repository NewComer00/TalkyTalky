import os
import sys
import time
import wave
import random
import readline
import tempfile
import argparse
import threading
from statistics import mean
from typing import Optional
from multiprocessing import Process

import pyaudio
import keyboard
from termcolor import colored
from textual import on, work
from textual.validation import Length
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.widgets import Input, RichLog, LoadingIndicator, Button, Sparkline
from textual.containers import Horizontal

from service.base import ServerBase
from service.action import ActionServer, ActionClient
from service.language_model import LanguageModelServer, LanguageModelClient
from service.speech2text import Speech2TextServer, Speech2TextClient
from service.text2speech import EdgettsServer, Pyttsx3Server


def config():
    parser = argparse.ArgumentParser(description="Talky Talky Chatbot App")

    parser.add_argument(
        "--tui",
        action="store_true",
        dest="tui",
        help="Start the App in TUI mode",
    )

    parser.add_argument(
        "--user-input",
        default="voice",
        choices=["voice", "keyboard"],
        dest="user_input",
        help="Select the way to interact with the chatbot \
                (valid values: voice, keyboard)",
    )

    parser.add_argument(
        "--noecho-server-log",
        action="store_true",
        dest="noecho_server_log",
        help="Do not print the stdout of servers to terminal",
    )

    parser.add_argument(
        "--tts.engine",
        default="pyttsx3",
        choices=["pyttsx3", "edge-tts"],
        dest="tts_engine",
        help="Select the text-to-speech engine \
                (valid values: pyttsx3, edge-tts)",
    )

    parser.add_argument(
        "--stt.model-dir",
        default="model/speech_to_text/",
        dest="stt_model_dir",
        help="The directory to store the speech-to-text models",
    )

    parser.add_argument(
        "--lm.model-dir",
        default="model/language_model/",
        dest="lm_model_dir",
        help="The directory to store the language models",
    )

    args = parser.parse_args()

    print(colored("======== Application Configuration ========", 'green'))
    for argname, argvalue in vars(args).items():
        print(colored(f"{argname}:\t\t{argvalue}", 'green'))
    return args


def run_server(ServerClass: ServerBase,
               log_redirect_to: Optional[str],
               **kwargs):
    if log_redirect_to == "stdout":
        sys.stdout = sys.__stdout__
    elif log_redirect_to is None:
        sys.stdout = None
    else:
        sys.stdout = sys.__stdout__

    server = ServerClass(**kwargs)
    server.connect()
    server.run()


def start_server_process(ServerClass: ServerBase,
                         log_redirect_to,
                         **kwargs):
    proc_server = Process(
        target=run_server,
        args=[ServerClass, log_redirect_to],
        kwargs=kwargs
    )
    proc_server.daemon = True
    proc_server.start()
    return proc_server


def start_services(app_cfg):
    log_redirect_to = \
        None if app_cfg.noecho_server_log else "stdout"

    start_server_process(
        ActionServer, log_redirect_to,
    )

    start_server_process(
        LanguageModelServer, log_redirect_to,
        model_dir=app_cfg.lm_model_dir
    )

    start_server_process(
        Speech2TextServer, log_redirect_to,
        model_dir=app_cfg.stt_model_dir
    )

    if app_cfg.tts_engine == "pyttsx3":
        TtsServerClass = Pyttsx3Server
    elif app_cfg.tts_engine == "edge-tts":
        TtsServerClass = EdgettsServer
    else:
        TtsServerClass = EdgettsServer
    start_server_process(
        TtsServerClass, log_redirect_to,
    )


class TalkyTalkyCLI:
    def __init__(self, app_cfg):
        self.app_cfg = app_cfg
        start_services(self.app_cfg)

    def run(self):
        if self.app_cfg.user_input == "voice":
            self.voice_interact()
        elif self.app_cfg.user_input == "keyboard":
            self.keyboard_interact()

    def keyboard_interact(self):
        language_model_client = LanguageModelClient()
        action_client = ActionClient()

        language_model_client.connect()
        action_client.connect()

        print(colored("======== Type to Chat! ========", 'green'))
        while True:
            me = 'ME  >> '
            prompt = input(colored(me, 'red'))
            if len(prompt) > 0:
                # get answer from the prompt
                answer = language_model_client.get_answer(prompt)

                her = 'BOT >> '
                print(colored(her, 'green'), answer)
                print('')

                # make reaction to the answer
                action_client.react_to(answer)

    def voice_interact(self):
        speech2text_client = Speech2TextClient()
        language_model_client = LanguageModelClient()
        action_client = ActionClient()

        speech2text_client.connect()
        language_model_client.connect()
        action_client.connect()

        # Constants for audio settings
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        CHUNK = 1024

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print(colored("======== Holding SPACE KEY to Record ========", 'green'))
        frames = []
        while True:
            stream.start_stream()
            frames.clear()

            # start recording if key is pressed
            while keyboard.is_pressed('space'):
                data = stream.read(CHUNK)
                frames.append(data)
                # recording progress bar
                print(colored('>', 'blue'), end='', flush=True)

            stream.stop_stream()

            # Save the recorded audio to a WAV file
            if len(frames) > 0:
                wav_fp, wav_path = tempfile.mkstemp()
                wf = wave.open(wav_path, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                # speech to text
                print('')
                prompt = speech2text_client.get_text(wav_path)
                os.close(wav_fp)
                os.remove(wav_path)

                # print my prompt words
                me = 'ME  >> '
                print(colored(me, 'red'), prompt)
                if prompt == '[EMPTY SPEECH]':
                    answer = "Sorry, I can't hear you clearly. Please try again."
                else:
                    # get answer from the prompt
                    answer = language_model_client.get_answer(prompt)

                her = 'BOT >> '
                print(colored(her, 'green'), answer)
                print('')

                # make reaction to the answer
                action_client.react_to(answer)

            time.sleep(0.1)

        stream.close()
        audio.terminate()


class TalkyTalkyTUI(App):
    CSS = '''
Screen {
    layout: vertical;
    layers: below above;
    align: center middle;
}

RichLog {
    layer: below;
    height: 0.7fr;
    border: round darkgreen;
    background: green 10%;
    margin: 1;
}

RichLog:focus {
    border: round green;
    background: green 15%;
}

Input {
    layer: below;
    height: 0.2fr;
    border: round darkblue;
    background: blue 10%;
    margin: 1;
}

Input:focus {
    border: round blue;
    background: blue 15%;
}

Button {
    layer: below;
    height: 0.1fr;
    width: 1fr;
    margin: 2;
    min-height: 1;
}

#start_record {
    display: block;
}

#stop_record {
    display: none;
}

LoadingIndicator {
    layer: above;
    height: 10%;
    width: 30%;
    margin: 2;
    padding: 1;
    min-height: 3;
    display: none;
    content-align: center middle;
}

#processing_chat {
    color: $accent;
    border: $accent round;
}

#processing_record {
    color: $warning;
    border: $warning round;
}

Sparkline {
    layer: above;
    height: 10%;
    width: 30%;
    margin: 2;
    padding: 1;
    min-height: 3;
    display: none;
    border: $warning round;
    content-align: center middle;
}

Sparkline > .sparkline--max-color {
    color: $error;
}

Sparkline > .sparkline--min-color {
    color: $warning;
}
'''

    def __init__(self, app_cfg):
        self.app_cfg = app_cfg
        start_services(self.app_cfg)

        self.speech2text_client = Speech2TextClient()
        self.language_model_client = LanguageModelClient()
        self.action_client = ActionClient()

        self.speech2text_client.connect()
        self.language_model_client.connect()
        self.action_client.connect()

        self.mutex_on_submit = threading.Lock()

        self.is_recording = False
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 2
        self.fs = 44100
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.sample_format,
                                      channels=self.channels,
                                      rate=self.fs,
                                      frames_per_buffer=self.chunk,
                                      input=True)
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield RichLog(wrap=True, highlight=True, markup=True)
        yield Input(placeholder="Write your prompt here. Press ENTER to send.",
                    validate_on=["changed", "submitted"],
                    validators=[Length(minimum=1, failure_description="Your prompt must not be empty.")]).focus()
        yield Button(label="SPEECH TO TEXT", id="start_record")
        yield Button(label="FINISH SPEAKING", id="stop_record", variant='warning')
        yield LoadingIndicator(id="processing_chat")
        yield LoadingIndicator(id="processing_record")
        yield Sparkline(data=[], summary_function=mean)

    @on(Input.Submitted)
    @work(exclusive=True, thread=True)
    def submit_prompt(self, event: Input.Submitted) -> None:
        if self.mutex_on_submit.acquire(blocking=False):
            if event.validation_result.is_valid:
                loading_box = self.query_one("#processing_chat")
                loading_box.display = True
                chat_box = self.query_one(RichLog)

                me = '[bold red]ME  >> [/bold red]'
                her = '[bold green]BOT >> [/bold green]'
                prompt = event.value
                chat_box.write(me + prompt)
                self.query_one(Input).value = ''

                answer = self.language_model_client.get_answer(prompt)
                chat_box.write(her + answer)

                loading_box.display = False
                self.action_client.react_to(answer)

            self.mutex_on_submit.release()

    @on(Button.Pressed, "#start_record")
    @work(exclusive=True, thread=True)
    async def start_record(self):
        if not self.is_recording:
            self.is_recording = True
            self.query_one("#start_record").display = False
            self.query_one("#stop_record").display = True

            frames = []
            sparkline = self.query_one(Sparkline)
            self.stream.start_stream()
            sparkline.display = True
            while self.is_recording:
                data = self.stream.read(self.chunk)
                frames.append(data)
                sparkline.data = data
            self.stream.stop_stream()
            sparkline.display = False

            input_box = self.query_one(Input)
            loading_box = self.query_one("#processing_record")
            loading_box.display = True
            if len(frames) > 0:
                wav_fp, wav_path = tempfile.mkstemp()
                wf = wave.open(wav_path, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.sample_format))
                wf.setframerate(self.fs)
                wf.writeframes(b''.join(frames))
                wf.close()

                # speech to text
                print('')
                prompt = self.speech2text_client.get_text(wav_path)
                input_box.value = prompt
                os.close(wav_fp)
                os.remove(wav_path)

            loading_box.display = False
            self.query_one("#stop_record").display = False
            self.query_one("#start_record").display = True
            input_box.focus()

            await input_box.action_submit()

    @on(Button.Pressed, "#stop_record")
    def stop_record(self):
        if self.is_recording:
            self.is_recording = False


if __name__ == "__main__":
    app_cfg = config()
    if app_cfg.tui:
        app = TalkyTalkyTUI(app_cfg)
    else:
        app = TalkyTalkyCLI(app_cfg)
    app.run()
