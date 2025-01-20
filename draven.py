import queue
import pyaudio
from google.cloud import speech
from google.cloud import language_v1
import vertexai
from vertexai.preview.language_models import TextGenerationModel
import micstream

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Google Cloud setup
PROJECT_ID = "propane-sphinx-448317-p4"
LOCATION = "us-east1"  # Vertex AI location
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize Vertex AI Text Generation model
generation_model = TextGenerationModel.from_pretrained("text-bison@001")

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
