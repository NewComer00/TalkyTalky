import os
import time
import wave
import socket
import tempfile
import pyaudio
import keyboard
from termcolor import colored

# Define server settings
S2T_HOST = '127.0.0.1'
S2T_PORT = 12344

LLM_HOST = '127.0.0.1'
LLM_PORT = 12345

ACTOR_HOST = '127.0.0.1'
ACTOR_PORT = 12346

# Constants for audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024


def main():
    s2t_backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("======== Connecting to S2T Backend ========")
    s2t_backend.connect((S2T_HOST, S2T_PORT))
    print("======== Successfully Connected to S2T Backend ========")

    llm_backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("======== Connecting to LLM Backend ========")
    llm_backend.connect((LLM_HOST, LLM_PORT))
    print("======== Successfully Connected to LLM Backend ========")

    actor_backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("======== Connecting to ACTOR Backend ========")
    actor_backend.connect((ACTOR_HOST, ACTOR_PORT))
    print("======== Successfully Connected to ACTOR Backend ========")

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
            print('')  # newline for the progress bar
            s2t_backend.send(wav_path.encode('utf-8'))
            prompt = s2t_backend.recv(1024).decode('utf-8').strip()
            os.close(wav_fp)
            os.remove(wav_path)

            llm_backend.send(prompt.encode('utf-8'))

            # print my prompt words
            me = 'ME  >> '
            if len(prompt) > 0:
                print(colored(me, 'red'), prompt)
            else:
                print(colored(me, 'red'), '[EMPTY SPEECH]')
                continue

            # Receive a response from the server
            answer = llm_backend.recv(1024).decode('utf-8').strip()

            her = 'BOT >> '
            print(colored(her, 'green'), answer)
            print('')

            # Send the answer to the actor backend
            actor_backend.send(answer.encode('utf-8'))

        time.sleep(0.1)

    stream.close()
    audio.terminate()


if __name__ == "__main__":
    main()
