import sys
import logging
import queue
from google.cloud import speech
import pyaudio
from google.cloud import aiplatform
from google.auth.credentials import AnonymousCredentials
import base64
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part, SafetySetting, Tool
from vertexai.preview.generative_models import grounding

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
LANGUAGE_CODE = "en-US"
LOCATION = "us-east1"
PROJECT_ID = "propane-sphinx-448317-p4" 

# Create model
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}
safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]
tools = [
    Tool.from_google_search_retrieval(
        google_search_retrieval=grounding.GoogleSearchRetrieval()
    ),
]
vertexai.init(project="propane-sphinx-448317-p4", location="us-east1")
model = GenerativeModel(
    "gemini-1.5-pro-002",
    tools=tools,
)

# Audio stream class
class MicStream:
    """Opens a recording stream as an empty_buffer yielding the audio chunks."""

    def __init__(self: object, rate: int, chunk: int) -> None:
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

        # Initialize a logger for this instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)


        handler = logging.FileHandler("logs/audio_stream.log")
        handler.setLevel(logging.DEBUG)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(handler)

        self.logger.info("MicStream initialized.")

    def __enter__(self: object) -> object:
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # After every chunk of audio is captured, PyAudio invokes the stream_callback function
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        self.logger.info("Audio stream opened.")
        return self

    def _fill_buffer(self: object, in_data: object, frame_count: int, time_info: object, status_flags: object) -> object:
        """Fill the buffer with audio data."""
        self._buff.put(in_data)
        self.logger.debug(f"Added chunk of size {len(in_data)} to buffer.")
        return None, pyaudio.paContinue

    def empty_buffer(self: object) -> object:
        """Generates audio chunks from the stream."""
        while not self.closed:
            self.logger.info("Waiting for the first chunk...")
            chunk = self._buff.get()
            if chunk is None:
                self.logger.info("Stream closed, no more data.")
                return

            self.logger.debug(f"Received first chunk: {len(chunk)} bytes")
            data = [chunk]

            # Adding additional chunks, if available
            self.logger.info("Checking for additional chunks...")
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        self.logger.info("Stream closed, no more data.")
                        return
                    data.append(chunk)
                    self.logger.debug(f"Received additional chunk: {len(chunk)} bytes")
                except queue.Empty:
                    self.logger.info("No more chunks available, moving to next iteration.")
                    break

            # After gathering chunks, yield the combined data
            self.logger.info(f"Yielding a total of {len(b''.join(data))} bytes of audio data.")
            yield b"".join(data)

    def __exit__(self: object, type: object, value: object, traceback: object) -> None:
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()
        self.logger.info("Audio stream closed.")


def generate(transcript):
    responses = model.generate_content(
        [transcript],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    for response in responses:
        if not response.candidates or not response.candidates[0].content.parts:
            continue
        print(response.text, end="")



def listen_print_loop(responses: object) -> str:
    """Process streaming responses and print the transcriptions, submitting each phrase to the generate function."""
    num_chars_printed = 0
    final_transcript = ""
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            print(f"Final Transcript Detected: {transcript + overwrite_chars}")
            num_chars_printed = 0

            # Check if the transcript is not empty or too short
            if transcript.strip():  # Only pass non-empty transcriptions
                generate(transcript)  # Just pass the current phrase to generate function
            else:
                print("Skipping empty or noise-only transcription.")
    
    return final_transcript



def main() -> None:
    """Transcribe speech and get responses from Vertex AI."""
    language_code = "en-US"  # Language code

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicStream(RATE, CHUNK) as stream:
        audio_empty_buffer = stream.empty_buffer()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_empty_buffer
        )

        print("Starting to listen and transcribe...")
        responses = client.streaming_recognize(streaming_config, requests)

        # Get the final transcription from the server responses
        final_transcript = listen_print_loop(responses)
        print(f"Final Transcription: {final_transcript}")

if __name__ == "__main__":
    main()
