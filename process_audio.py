import os
import wave
import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.signal import medfilt
from pydub import AudioSegment
import noisereduce as nr

# Recording directories
RECORDINGS_DIR = os.path.expanduser("~/recordings/raw")
PROCESSED_DIR = os.path.expanduser("~/recordings/denoised")

def process_audio_file(input_file, output_file):
    # Read the raw recording and apply audio processing
    rate, data = wavfile.read(input_file)

    # Determine number of channels
    channels = 2 if data.ndim == 2 else 1

    # Apply a median filter to remove clicks
    # Ensure kernel_size is odd and smaller than the data size
    kernel_size = min(3, len(data) - 1)
    if kernel_size % 2 == 0:
        kernel_size -= 1
    filtered_data = medfilt(data, kernel_size=kernel_size)

    # Convert the filtered data to an AudioSegment
    audio = AudioSegment(
        filtered_data.tobytes(),
        frame_rate=rate,
        sample_width=filtered_data.dtype.itemsize,
        channels=channels
    )

    # Export the filtered audio back to a numpy array
    filtered_data = np.array(audio.get_array_of_samples())

    print(f"Clicking sounds removed from {input_file}")

    # Convert to numpy array
    audio_data = filtered_data

    # If the audio is stereo, reshape it
    if channels == 2:
        audio_data = audio_data.reshape(-1, 2)

    # Convert to float32 for processing
    audio_float = audio_data.astype(np.float32) / 32768.0
    # Apply noise reduction using vectorized operations for faster processing
    chunk_size = 10_000  # Increased chunk size for better performance
    reduced_noise = np.zeros_like(audio_float)
    for i in range(0, len(audio_float), chunk_size):
        chunk = audio_float[i:i+chunk_size]
        reduced_chunk = nr.reduce_noise(y=chunk, sr=rate, n_std_thresh_stationary=1.5)
        reduced_noise[i:i+len(reduced_chunk)] = reduced_chunk

    # Optional: Use multiprocessing for parallel processing
    # import multiprocessing as mp
    # def process_chunk(chunk):
    #     return nr.reduce_noise(y=chunk, sr=rate, n_std_thresh_stationary=1.5)
    # with mp.Pool(processes=mp.cpu_count()) as pool:
    #     chunks = [audio_float[i:i+chunk_size] for i in range(0, len(audio_float), chunk_size)]
    #     reduced_chunks = pool.map(process_chunk, chunks)
    # reduced_noise = np.concatenate(reduced_chunks)

    # Apply a high-pass filter to remove low-frequency noise
    sos = signal.butter(10, 100, 'hp', fs=rate, output='sos')
    filtered_audio = signal.sosfilt(sos, reduced_noise)

    # Apply dynamic range compression
    threshold = 0.1
    ratio = 4.0
    compressed_audio = np.where(
        np.abs(filtered_audio) > threshold,
        threshold + (np.abs(filtered_audio) - threshold) / ratio * np.sign(filtered_audio),
        filtered_audio
    )

    # Normalize the audio
    max_val = np.max(np.abs(compressed_audio))
    normalized_audio = compressed_audio / max_val

    # Convert back to int16
    final_audio = np.int16(normalized_audio * 32767)

    # Save the processed recording as a new WAV file
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)  # Preserve original channels
        wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
        wf.setframerate(rate)
        wf.writeframes(final_audio.flatten().tobytes())

    print(f"Processed audio saved as {output_file}")

def process_recordings():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    for filename in os.listdir(RECORDINGS_DIR):
        if filename.endswith(".wav"):
            input_file = os.path.join(RECORDINGS_DIR, filename)
            output_file = os.path.join(PROCESSED_DIR, f"processed_{filename}")

            if not os.path.exists(output_file):
                print(f"Processing {filename}...")
                process_audio_file(input_file, output_file)
            else:
                print(f"Processed version of {filename} already exists. Skipping.")

if __name__ == "__main__":
    process_recordings()
