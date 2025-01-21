import time
import sys
from google.cloud import speech

# Constants
RATE = 16000  # Sample rate (16kHz)
LANGUAGE_CODE = "en-US"
SILENCE_THRESHOLD = 2  # in seconds, define how long to wait before finalizing after silence

class AudioTranscriber:
    """Handles the audio transcription using Google Cloud Speech API."""

    def __init__(self, language_code: str = LANGUAGE_CODE, silence_threshold=SILENCE_THRESHOLD):
        self.language_code = language_code
        self.client = speech.SpeechClient()
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=self.language_code,
            ),
            interim_results=True
        )
        self.last_speech_time = time.time()  # Time when last speech was detected
        self.silence_threshold = silence_threshold  # Silence threshold in seconds
        self.finalized_transcript = ""  # Store final transcript

    def listen_for_transcriptions(self, responses) -> str:
        """Processes streaming responses and returns the final transcription."""
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            overwrite_chars = " " * (num_chars_printed - len(transcript))

            # Update the last speech time whenever speech is detected
            if result.is_final:
                self.last_speech_time = time.time()

            # If the transcript is not final, continue to print interim results
            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")
                sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                print(f"Final Transcript Detected: {transcript + overwrite_chars}")
                num_chars_printed = 0

                # Store the final transcript if it's not empty
                self.finalized_transcript = transcript.strip() if transcript.strip() else None

                # Once a final transcript is detected, we check for silence or speaker change
                if self._detect_silence_or_speaker_change():
                    return self.finalized_transcript  # Return final transcript

        return ""

    def _detect_silence_or_speaker_change(self) -> bool:
        """Detects if silence or a speaker change has occurred based on the silence threshold."""
        current_time = time.time()
        time_since_last_speech = current_time - self.last_speech_time

        # Check if silence has exceeded the threshold, signaling a possible pause or speaker change
        if time_since_last_speech > self.silence_threshold:
            print("Silence or speaker change detected, finalizing transcript...")
            return True  # Return True when silence or speaker change is detected

        return False
