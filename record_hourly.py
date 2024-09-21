import pyaudio
import wave
import os
from datetime import datetime
from pytz import timezone

# Directory to save recordings
OUTPUT_DIR = os.path.expanduser("~/recordings/raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Recording parameters
FORMAT = pyaudio.paFloat32  # Higher precision format for better quality
RATE = 96000  # Higher sample rate for better frequency response
CHUNK = 1024  # Smaller chunk size for more frequent updates and potentially lower latency
RECORD_SECONDS = 3600  # 1 hour
CHANNELS = 2  # Stereo recording for better spatial information

def record_audio():
    # Get the current time in PST
    pst = timezone('America/Los_Angeles')
    timestamp = datetime.now(pst).strftime('%Y-%m-%d_%H-%M-%S')
    output_file = os.path.join(OUTPUT_DIR, f"recording_{timestamp}.wav")

    audio = pyaudio.PyAudio()

    # Check the default input device for the number of channels
    device_info = audio.get_default_input_device_info()
    max_input_channels = device_info['maxInputChannels']
    channels = min(1, max_input_channels)  # Use mono recording to save memory

    # Open the audio stream
    stream = audio.open(format=FORMAT, channels=channels,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print(f"Recording started: {output_file}")

    # Open the WAV file for writing
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        # Record for the specified number of seconds
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            wf.writeframes(data)
            del data  # Explicitly delete the data to free up memory

    print("Recording finished")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

def continuous_recording():
    while True:
        record_audio()

if __name__ == "__main__":
    continuous_recording()
