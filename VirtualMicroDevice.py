import struct
import pyaudio
import librosa
import threading
import numpy as np
from pedalboard import Pedalboard, Reverb


class VirtualMicroDevice:
    def __init__(
        self,
        input_device_index,
        output_device_index,
        second_output_device_index,
        background_audio_file=None,
        sample_rate=44100,
    ):
        # basic audio device parameters
        self.sample_rate = sample_rate
        self.chunk_size = sample_rate

        # initialize device indices
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.second_output_device_index = second_output_device_index

        # initialize audio devices
        self.audio_input = None
        self.audio_output_1 = None
        self.audio_output_2 = None

        # translation settings
        self.second_output_device_enabled = False

        self.translate_sound_to_first_device_flag = False
        self.translate_sound_to_second_device_flag = False

        # audio effects
        self.noise_threshold = 0

        self.reverb_enabled = False
        self.audio_reverb_enabled = False
        self.reverb_room_size = 0.25
        self.reverb_pedalboard = Pedalboard([Reverb(room_size=self.reverb_room_size)])

        # settings for background audio
        self.play_audio_on_first_device_flag = False
        self.play_audio_on_second_device_flag = False

        self.background_audio_volume = 0
        self.background_audio_position = 0

        self.current_loop_iteration = 0
        self.total_iterations = 1

        self.background_audio = None
        if background_audio_file:
            self.load_background_audio(background_audio_file)

        # the main thread
        self.is_running = False
        self.thread = None

    # ----------------------------------------------------------------
    def set_input_device_index(self, index):
        self.input_device_index = index

    def set_output_device_index(self, index):
        self.output_device_index = index

    def set_second_output_device_index(self, index):
        self.second_output_device_index = index

    def set_second_output_device_enabled(self, flag):
        self.second_output_device_enabled = flag

    # ----------------------------------------------------------------
    def set_translate_sound_to_first_device_flag(self, flag):
        self.translate_sound_to_first_device_flag = flag

    def set_translate_sound_to_second_device_flag(self, flag):
        self.translate_sound_to_second_device_flag = flag

    def set_noise_threshold(self, threshold):
        threshold = max(0, threshold)
        threshold = min(threshold, 3000)
        self.noise_threshold = threshold

    def set_reverb_enabled(self, flag):
        self.reverb_enabled = flag

    def set_audio_reverb_enabled(self, flag):
        self.audio_reverb_enabled = flag

    def set_reverb_room_size(self, room_size):
        room_size = max(0, room_size)
        room_size = min(room_size, 1)
        self.reverb_room_size = room_size
        self.reverb_pedalboard = Pedalboard([Reverb(room_size=self.reverb_room_size)])

    # ----------------------------------------------------------------
    def load_background_audio(self, file_path):
        audio_data, _ = librosa.load(file_path, sr=self.sample_rate, mono=True)
        self.background_audio = np.array(audio_data, dtype=np.float32)

        self.current_loop_iteration = 0
        self.total_iterations = len(self.background_audio) // self.chunk_size

    def set_play_audio_on_first_device_flag(self, flag):
        self.play_audio_on_first_device_flag = flag

    def set_play_audio_on_second_device_flag(self, flag):
        self.play_audio_on_second_device_flag = flag

    def set_background_audio_volume(self, volume):
        volume = max(0, volume)
        volume = min(volume, 3.0)
        self.background_audio_volume = volume

    def set_background_audio_position(self, position):
        position = max(0, position)
        position = min(position, 100)
        self.background_audio_position = position

        if self.background_audio is not None:
            self.current_loop_iteration = int(
                self.total_iterations * (self.background_audio_position / 100)
            )

    def get_background_audio_position(self):
        if self.background_audio is not None:
            return (self.current_loop_iteration / self.total_iterations) * 100
        else:
            return 0

    # ----------------------------------------------------------------
    def reduce_noise(self, data, noise_gate_threshold):
        reduced_noise_data = np.where(np.abs(data) <= noise_gate_threshold, 0, data)
        return reduced_noise_data

    def increment_audio_position(self):
        self.current_loop_iteration = (
            self.current_loop_iteration + 1
        ) % self.total_iterations

    def get_normalized_audio_data(self, data, background_audio):
        # Get current audio position
        loop_length = len(background_audio)
        current_pos = self.chunk_size * self.current_loop_iteration % loop_length

        # Normalize background audio data
        audio_koeff = np.max(np.abs(background_audio))
        background_audio_normalized = self.background_audio / audio_koeff

        background_audio_data = np.zeros(len(data))
        for i in range(len(data)):
            background_audio_data[i] = background_audio_normalized[
                current_pos % loop_length
            ]
            current_pos += 1

        # Change background audio volume
        background_audio_data *= self.background_audio_volume

        return background_audio_data

    def process_audio_for_device_1(self, data):
        # Convert binary data to numpy array of floats
        data = np.array(struct.unpack(f"{len(data)//2}h", data), dtype=np.float32)

        processed_data: np.ndarray
        if not self.translate_sound_to_first_device_flag:
            processed_data = np.zeros_like(data)
        else:
            # Reduce noise
            processed_data = self.reduce_noise(data, self.noise_threshold)

            # Add reverberation effect
            if self.reverb_enabled:
                processed_data = self.reverb_pedalboard(
                    processed_data, self.sample_rate, reset=False
                )

        # Add background audio
        if self.play_audio_on_first_device_flag:
            if self.background_audio is not None:
                default_audio_volume = 8000
                audio_data = self.get_normalized_audio_data(
                    processed_data, self.background_audio
                )
                audio_data *= default_audio_volume

                if self.audio_reverb_enabled:
                    audio_data = self.reverb_pedalboard(
                        audio_data, self.sample_rate, reset=False
                    )

                processed_data += audio_data

        # Convert back to binary data
        processed_data = struct.pack(
            f"{len(processed_data)}h", *np.array(processed_data, dtype=np.int16)
        )

        return processed_data

    def process_audio_for_device_2(self, data):
        # Convert binary data to numpy array of floats
        data = np.array(struct.unpack(f"{len(data)//2}h", data), dtype=np.float32)

        processed_data: np.ndarray
        if not self.translate_sound_to_second_device_flag:
            processed_data = np.zeros_like(data)
        else:
            # Reduce noise
            processed_data = self.reduce_noise(data, self.noise_threshold)

            # Add reverberation effect
            if self.reverb_enabled:
                processed_data = self.reverb_pedalboard(
                    processed_data, self.sample_rate, reset=False
                )

        # Add background audio
        if self.play_audio_on_second_device_flag:
            if self.background_audio is not None:
                default_audio_volume = 8000
                audio_data = self.get_normalized_audio_data(
                    processed_data, self.background_audio
                )
                audio_data *= default_audio_volume

                if self.audio_reverb_enabled:
                    audio_data = self.reverb_pedalboard(
                        audio_data, self.sample_rate, reset=False
                    )

                processed_data += audio_data

        # Convert back to binary data
        processed_data = struct.pack(
            f"{len(processed_data)}h", *np.array(processed_data, dtype=np.int16)
        )

        return processed_data

    # ----------------------------------------------------------------
    def run(self):
        self._start_input()
        self._start_output_1()

        if self.second_output_device_enabled:
            self._start_output_2()

        self.is_running = True

        while self.is_running:
            data = self.audio_input.read(self.chunk_size)

            try:
                processed_data_1 = self.process_audio_for_device_1(data)
                self.audio_output_1.write(processed_data_1)
            except:
                pass

            if self.second_output_device_enabled:
                try:
                    processed_data_2 = self.process_audio_for_device_2(data)
                    self.audio_output_2.write(processed_data_2)
                except:
                    pass

            if self.play_audio_on_first_device_flag or (
                self.play_audio_on_second_device_flag
                and self.second_output_device_enabled
            ):
                # Update current audio position
                self.increment_audio_position()

        self._stop_input()
        self._stop_output_1()

        if self.second_output_device_enabled:
            self._stop_output_2()

    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.thread.join()

    # ----------------------------------------------------------------
    def _start_input(self):
        self.audio_input = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk_size,
        )

    def _start_output_1(self):
        self.audio_output_1 = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.output_device_index,
            frames_per_buffer=self.chunk_size,
        )

    def _start_output_2(self):
        self.audio_output_2 = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.second_output_device_index,
            frames_per_buffer=self.chunk_size,
        )

    def _stop_input(self):
        self.audio_input.stop_stream()
        self.audio_input.close()

    def _stop_output_1(self):
        self.audio_output_1.stop_stream()
        self.audio_output_1.close()

    def _stop_output_2(self):
        self.audio_output_2.stop_stream()
        self.audio_output_2.close()
