import queue
import pyaudio
from google.cloud import speech
from google.cloud import language_v1
import vertexai
from vertexai.preview.language_models import TextGenerationModel

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Google Cloud setup
PROJECT_ID = "propane-sphinx-448317-p4"
LOCATION = "us-east1"  # Vertex AI location
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize Vertex AI Text Generation model
generation_model = TextGenerationModel.from_pretrained("text-bison@001")

# Microphone Stream Class
class MicrophoneStream:
    """Opens a recording stream as a generator yielding audio chunks."""
    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Fill the buffer with audio data."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Generate audio chunks from the buffer."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

# Speech-to-Text streaming
def transcribe_streaming():
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream() as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in audio_generator
        )
        responses = client.streaming_recognize(config=streaming_config, requests=requests)
        process_responses(responses)

# Process responses from Speech-to-Text
def process_responses(responses):
    """Processes the responses from the Speech-to-Text API."""
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        if result.is_final:
            print(f"Transcript: {transcript}")
            if is_question(transcript):
                generate_response(transcript)

# Detect if the text is a question or ask
def is_question(text):
    """Simple heuristic to detect questions or asks."""
    question_keywords = ["what", "why", "how", "when", "who", "can", "could", "would", "is", "are", "do", "does"]
    return any(word in text.lower() for word in question_keywords) or text.strip().endswith("?")

# Generate response using Vertex AI
def generate_response(prompt):
    """Generates a response using Vertex AI Text Generation Model."""
    print("Generating response...")
    response = generation_model.predict(
        prompt,
        max_output_tokens=200,
        temperature=0.7,
    )
    print(f"Response: {response.text}")

# Main function
if __name__ == "__main__":
    print("Listening for questions or requests...")
    transcribe_streaming()
