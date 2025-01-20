import queue
import wave
import pyaudio

class micstream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate=16000, chunk=1024, log_audio=False, log_file="output.wav", silence_threshold=1000):
        """
        Initialize the micstream.
        
        :param rate: The sample rate of the audio stream.
        :param chunk: The size of each audio chunk.
        :param log_audio: Boolean flag to save audio to a file.
        :param log_file: File path to save the audio log if enabled.
        :param silence_threshold: Threshold for detecting silence.
        """
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self.log_audio = log_audio
        self.log_file = log_file
        self.silence_threshold = silence_threshold
        self._wf = None  # Wave file handle for logging

    def __enter__(self):
        try:
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

            # Open file for logging if enabled
            if self.log_audio:
                self._wf = wave.open(self.log_file, "wb")
                self._wf.setnchannels(1)
                self._wf.setsampwidth(self._audio_interface.get_sample_size(pyaudio.paInt16))
                self._wf.setframerate(self._rate)
        except Exception as e:
            print(f"Error initializing audio stream: {e}")
            self.closed = True
            raise e
        return self

    def __exit__(self, type, value, traceback):
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        if self._audio_interface:
            self._audio_interface.terminate()
        self.closed = True
        self._buff.put(None)

        # Close the audio log file
        if self._wf:
            self._wf.close()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Fill the buffer with audio data."""
        self._buff.put(in_data)
        
        # Write audio data to log file if enabled
        if self.log_audio and self._wf:
            self._wf.writeframes(in_data)
        
        return None, pyaudio.paContinue

    def generator(self):
        """Generates audio chunks from the stream."""
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
            audio_data = b"".join(data)

            # Optionally detect silence
            if self.silence_threshold and self._is_silent(audio_data):
                continue  # Skip silent chunks
            
            yield audio_data

    def _is_silent(self, audio_data):
        """Check if the audio data is silent."""
        # Interpret audio data as integers and calculate the max amplitude
        audio_array = wave.struct.unpack("%dh" % (len(audio_data) // 2), audio_data)
        max_amplitude = max(abs(sample) for sample in audio_array)
        return max_amplitude < self.silence_threshold
