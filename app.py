import os
import time
import wave
import tempfile
import argparse
from multiprocessing import Process

import pyaudio
import keyboard
from termcolor import colored

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

    print(colored("======== Application Configuration ========", 'green'))
    print(f"Text-to-Speech Engine: {args.tts}")
    print(colored("======== Application Configuration End ========", 'green'))
    return args


def run_action_server():
    acts = ActionServer()
    acts.connect()
    acts.run()


def run_language_server():
    lms = LanguageModelServer()
    lms.connect()
    lms.run()


def run_speech2text_server():
    s2ts = Speech2TextServer()
    s2ts.connect()
    s2ts.run()


def run_tts_server(tts_engine):
    if tts_engine == "pyttsx3":
        ttss = Pyttsx3Server()
    elif tts_engine == "edge-tts":
        ttss = EdgettsServer()
    else:
        ttss = Pyttsx3Server()
    ttss.connect()
    ttss.run()


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

    interact()
