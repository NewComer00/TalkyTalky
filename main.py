from faster_whisper import WhisperModel
import keyboard
import wave
import pyaudio
import socket
from termcolor import colored

# Define server settings
LLM_HOST = '127.0.0.1'  # Server's IP address
LLM_PORT = 12345       # Port the server is listening on

ACTOR_HOST = '127.0.0.1'
ACTOR_PORT = 12346

# Constants for audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILE = 'audio.wav'

print("======== Loading Whisper Model ========")
model_size = "base.en"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


def speech_to_text(wav_file):
    segments, _ = model.transcribe(wav_file)
    segments = list(segments)
    speech_text = ''.join([seg.text for seg in segments])
    return speech_text


def main():
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
    while True:
        stream.start_stream()
        frames = []

        # start recording if key is pressed
        while keyboard.is_pressed('space'):
            data = stream.read(CHUNK)
            frames.append(data)
            # recording progress bar
            print(colored('>', 'blue'), end='', flush=True)

        stream.stop_stream()

        # Save the recorded audio to a WAV file
        if len(frames) > 0:
            wf = wave.open(OUTPUT_FILE, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            # speech to text
            print('')  # newline for the progress bar
            prompt = speech_to_text(OUTPUT_FILE).strip()
            # Send a message to the server
            llm_backend.send(prompt.encode('utf-8'))

            # print my prompt words
            me = 'ME  >> '
            if len(prompt) > 0:
                print(colored(me, 'red'), prompt)
            else:
                print(colored(me, 'red'), '[EMPTY SPEECH]')

            # Receive a response from the server
            answer = llm_backend.recv(1024).decode('utf-8').strip()

            her = 'BOT >> '
            print(colored(her, 'green'), answer)
            print('')

            # Send the answer to the actor backend
            actor_backend.send(answer.encode('utf-8'))

    stream.close()
    audio.terminate()


if __name__ == "__main__":
    main()
