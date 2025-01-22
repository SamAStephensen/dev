import sys
import logging
import queue
import pyaudio
import os


class MicStream:
    """Opens a recording stream as an empty_buffer yielding the audio chunks."""

    def __init__(self, rate: int, chunk: int) -> None:
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

        # Ensure the 'logs' directory exists
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)  # Create the directory if it doesn't exist

        # Initialize a logger for this instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler(os.path.join(log_dir, "audio_stream.log"))
        handler.setLevel(logging.DEBUG)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(handler)

        self.logger.info("MicStream initialized.")

    def __enter__(self):
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

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Fill the buffer with audio data."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def empty_buffer(self):
        """Generates audio chunks from the stream."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                self.logger.info("Stream closed, no more data.")
                return

            data = [chunk]

            # Adding additional chunks, if available
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()
        self.logger.info("Audio stream closed.")
