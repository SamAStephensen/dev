import whisper
import sounddevice as sd
import numpy as np
import queue
import threading
import torch
from time import time
from transformers import pipeline

# Load Whisper whisperer with CUDA support if available
device = "cuda" if torch.cuda.is_available() else "cpu"
whisperer = whisper.load_model("base", device=device)

# Load the model for text correction
corrector = pipeline("text2text-generation", model="t5-small")

# Audio settings
samplerate = 16000  # Required sample rate for Whisper
channels = 1  # Mono audio
blocksize = int(samplerate * 2)  # Process 2 seconds of audio
overlap = int(samplerate * 1)  # 1 second overlap for smoother transcription

# Audio queue to accumulate data
audio_queue = queue.Queue()
audio_buffer = np.array([], dtype=np.float32)

# Phrase buffer for assembling final transcription
phrase_buffer = []

# Audio callback
def audio_callback(indata, frames, time, status):
    """Capture microphone input and add it to the audio queue."""
    if status:
        print(f"Status: {status}")
    audio_queue.put(indata.copy())

# Real-time transcription processing
def process_audio():
    global audio_buffer, phrase_buffer
    last_transcription_time = time()

    while True:
        audio_data = audio_queue.get()
        audio_buffer = np.concatenate((audio_buffer, audio_data.flatten()))

        # Process audio when the buffer reaches the required size
        if len(audio_buffer) >= blocksize:
            # Extract and process the chunk
            audio_chunk = audio_buffer[:blocksize]
            audio_buffer = audio_buffer[blocksize - overlap:]  # Retain overlap for smooth transitions
            audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))  # Normalize

            # Transcribe the audio
            print("Transcribing...")
            result = whisperer.transcribe(audio_chunk, fp16=False, language="en")
            transcription = result["text"].strip()

            # Handle phrase assembly
            if transcription:
                phrase_buffer.append(transcription)
                print(f"Partial Transcription: {' '.join(phrase_buffer)}")

            # Clear the phrase buffer after intervals
            if time() - last_transcription_time > 5:  # Adjust as needed
                ft = ' '.join(phrase_buffer)
                print("Transcription: " +ft)
                result = corrector(ft, max_length=100, num_return_sequences=1)
                print('Corrected: ' + result[0]['generated_text'])
                phrase_buffer = []
                last_transcription_time = time()


# Start listening and processing
def start_listening():
    threading.Thread(target=process_audio, daemon=True).start()
    with sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=channels, dtype="float32"):
        print("Listening... Press Ctrl+C to stop.")
        while True:
            sd.sleep(1000)

if __name__ == "__main__":
    start_listening()
