from AudioTranscriber import AudioTranscriber

from MicStream import MicStream
from VertexModel import VertexModel
from google.cloud import speech

PROJECT_ID = "propane-sphinx-448317-p4"
LOCATION = "us-east1"

def main():
    # Initialize Audio Transcriber and Content Generator
    audio_transcriber = AudioTranscriber()
    vertex_model = VertexModel(PROJECT_ID, LOCATION)

    with MicStream() as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        while True:
            # Start the transcription process
            responses = audio_transcriber.client.streaming_recognize(audio_transcriber.streaming_config, requests)
            transcript = audio_transcriber.listen_for_transcriptions(responses)
            if transcript:
                vertex_model.generate_response_from_transcript(transcript)

if __name__ == "__main__":
    main()
