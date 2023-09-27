import os
import sys
import time
import wave
import tempfile
import argparse
from typing import Optional
from multiprocessing import Process

import pyaudio
import keyboard
from termcolor import colored

from service.base import ServerBase
from service.action import ActionServer, ActionClient
from service.language_model import LanguageModelServer, LanguageModelClient
from service.speech2text import Speech2TextServer, Speech2TextClient
from service.text2speech import EdgettsServer, Pyttsx3Server


def config():
    parser = argparse.ArgumentParser(description="Talky Talky Chatbot App")

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
        "--stt.model_dir",
        default="model/speech_to_text/",
        dest="stt_model_dir",
        help="The directory to store the speech-to-text models",
    )

    parser.add_argument(
        "--lm.model_dir",
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


def interact():
    speech2text_client = Speech2TextClient()
    language_model_client = LanguageModelClient()
    action_client = ActionClient()

    speech2text_client.connect()
    language_model_client.connect()
    action_client.connect()

    # Constants for audio settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
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


if __name__ == "__main__":
    app_cfg = config()
    log_redirect_to = \
        None if app_cfg.noecho_server_log else "stdout"

    proc_action_server = start_server_process(
        ActionServer, log_redirect_to,
    )

    proc_language_server = start_server_process(
        LanguageModelServer, log_redirect_to,
        model_dir=app_cfg.lm_model_dir
    )

    proc_speech2text_server = start_server_process(
        Speech2TextServer, log_redirect_to,
        model_dir=app_cfg.stt_model_dir
    )

    if app_cfg.tts_engine == "pyttsx3":
        TtsServerClass = Pyttsx3Server
    elif app_cfg.tts_engine == "edge-tts":
        TtsServerClass = EdgettsServer
    else:
        TtsServerClass = EdgettsServer
    proc_tts_server = start_server_process(
        TtsServerClass, log_redirect_to,
    )

    interact()
