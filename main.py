import pyaudio
import wave
import threading
import keyboard
from faster_whisper import WhisperModel


model_size = "tiny.en"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# Constants for audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILE = 'audio.wav'

# Global variables
recording = False

def record_audio():
    global recording
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    while recording:
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio to a WAV file
    wf = wave.open(OUTPUT_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def process_audio():
    segments, _ = model.transcribe(OUTPUT_FILE)
    segments = list(segments)
    print(segments)

def main():
    global recording

    while True:
        if keyboard.is_pressed('space') and not recording:
            print("Recording started...")
            recording = True
            # Start recording thread
            recording_thread = threading.Thread(target=record_audio)
            recording_thread.start()
        elif not keyboard.is_pressed('space') and recording:
            print("Recording stopped.")
            recording = False
            recording_thread.join()  # Wait for the recording thread to finish
            process_audio()  # Call the audio processing function

if __name__ == "__main__":
    main()

