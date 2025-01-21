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