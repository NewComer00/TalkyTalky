import pyttsx3
from faster_whisper import WhisperModel
import keyboard
import wave
import pyaudio
import socket
from termcolor import colored

# Define server settings
HOST = '127.0.0.1'  # Server's IP address
PORT = 12345       # Port the server is listening on

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
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("======== Connecting to GPT4ALL Backend ========")
    # Connect to the server
    client_socket.connect((HOST, PORT))
    print("======== Successfully Connected to GPT4ALL Backend ========")

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
            client_socket.send(prompt.encode('utf-8'))

            # print my prompt words
            me = 'ME  >> '
            if len(prompt) > 0:
                print(colored(me, 'red'), prompt)
            else:
                print(colored(me, 'red'), '[EMPTY SPEECH]')

            # Receive a response from the server
            answer = client_socket.recv(1024).decode('utf-8').strip()
            her = 'BOT >> '
            print(colored(her, 'green'), answer)
            pyttsx3.speak(answer)
            print('')

    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()
