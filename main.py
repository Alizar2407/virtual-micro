import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from VirtualMicroDevice import VirtualMicroDevice


class VirtualMicroGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.master = master

        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.input_device_index = tk.StringVar(value="1")  # Microphone
        self.output_device_1_index = tk.StringVar(value="6")  # Cable input
        self.output_device_2_index = tk.StringVar(value="5")  # Headphones

        self.second_output_device_enabled = tk.BooleanVar(value=False)

        self.translate_sound_to_first_device_flag = tk.BooleanVar(value=True)
        self.translate_sound_to_second_device_flag = tk.BooleanVar(value=False)

        # Noise gate
        self.noise_threshold = tk.IntVar(value=0)

        # Reverberation
        self.reverb_enabled = tk.BooleanVar(value=False)
        self.audio_reverb_enabled = tk.BooleanVar(value=False)
        self.reverb_room_size = tk.DoubleVar(value=0.25)

        self.background_audio_file = tk.StringVar(value="File is not selected")
        self.play_audio_on_first_device_flag = tk.BooleanVar(value=False)
        self.play_audio_on_second_device_flag = tk.BooleanVar(value=False)
        self.audio_volume = tk.DoubleVar(value=0.7)
        self.audio_position = tk.IntVar(value=0)

        self.device = VirtualMicroDevice(
            background_audio_file=None,
            input_device_index=self.input_device_index,
            output_device_index=self.output_device_1_index,
            second_output_device_index=self.output_device_2_index,
        )

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self._create_widgets()
        self.update_settings()
        self.set_styles()

        self.grid(sticky="nsew")

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)

        self._create_device_index_section()
        self._create_effects_section()
        self._create_background_audio_section()
        self._create_start_stop_section()

    # ----------------------------------------------------------------
    def _create_device_index_section(self):
        section = tk.Frame(self, borderwidth=2, relief="groove", padx=10, pady=10)
        section.grid(row=0, column=0, sticky="ew")

        section.rowconfigure(0, weight=1)
        section.rowconfigure(1, weight=1)

        section.columnconfigure(1, weight=1)

        self.devices_label = tk.Label(section, text="Devices")
        self.devices_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Label(section, text="Input device:").grid(row=1, column=0)
        tk.Label(section, text="1st output device:").grid(row=2, column=0)

        self.enable_second_output_device_checkbutton = tk.Checkbutton(
            section,
            text="2nd output device:",
            variable=self.second_output_device_enabled,
            command=self.update_settings,
        )
        self.enable_second_output_device_checkbutton.grid(row=3, column=0)

        self.input_device_entry = tk.Entry(
            section, textvariable=self.input_device_index
        )
        self.input_device_entry.grid(row=1, column=1, sticky="e")

        self.output_device_entry_1 = tk.Entry(
            section, textvariable=self.output_device_1_index
        )
        self.output_device_entry_1.grid(row=2, column=1, sticky="e")

        self.output_device_entry_2 = tk.Entry(
            section, textvariable=self.output_device_2_index, state="disabled"
        )
        self.output_device_entry_2.grid(row=3, column=1, sticky="e")

    # ----------------------------------------------------------------
    def _create_effects_section(self):
        section = tk.Frame(self, borderwidth=2, relief="groove", padx=10, pady=10)
        section.grid(row=1, column=0, sticky="ew")

        section.rowconfigure(0, weight=1)
        section.rowconfigure(1, weight=1)

        section.columnconfigure(1, weight=1)

        self.audio_effects_label = tk.Label(section, text="Audio effects")
        self.audio_effects_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.translate_sound_to_first_device_checkbutton = tk.Checkbutton(
            section,
            text="Translate to 1st device",
            variable=self.translate_sound_to_first_device_flag,
            command=self.update_settings,
        )
        self.translate_sound_to_first_device_checkbutton.grid(
            row=1, column=0, sticky="w"
        )

        self.translate_sound_to_second_device_checkbutton = tk.Checkbutton(
            section,
            text="Translate to 2nd device",
            variable=self.translate_sound_to_second_device_flag,
            command=self.update_settings,
            state="disabled",
        )
        self.translate_sound_to_second_device_checkbutton.grid(
            row=1, column=1, sticky="e"
        )

        # Noise gate
        self.noise_threshold_scale = tk.Scale(
            section,
            from_=0,
            to=3000,
            orient="horizontal",
            label="Noise threshold",
            variable=self.noise_threshold,
            resolution=1,
            command=self.update_noise_threshold,
        )
        self.noise_threshold_scale.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.device.set_noise_threshold(self.noise_threshold.get())

        # Reverberation
        tk.Checkbutton(
            section,
            text="Reverberation",
            variable=self.reverb_enabled,
            command=self.update_settings,
        ).grid(row=3, column=0, sticky="w")

        tk.Checkbutton(
            section,
            text="Apply to audio file",
            variable=self.audio_reverb_enabled,
            command=self.update_settings,
        ).grid(row=3, column=1, sticky="e")

        self.reverb_room_size_scale = tk.Scale(
            section,
            from_=0,
            to=1,
            orient="horizontal",
            label="Room size",
            variable=self.reverb_room_size,
            resolution=0.01,
            command=self.update_reverb_room_size,
        )
        self.reverb_room_size_scale.grid(row=4, column=0, columnspan=2, sticky="ew")

    # ----------------------------------------------------------------
    def _create_background_audio_section(self):
        section = tk.Frame(self, borderwidth=2, relief="groove", padx=10, pady=10)
        section.grid(row=2, column=0, sticky="ew")

        section.rowconfigure(0, weight=1)
        section.rowconfigure(1, weight=1)
        section.rowconfigure(2, weight=1)
        section.rowconfigure(3, weight=1)

        section.columnconfigure(1, weight=1)

        self.audio_file_label = tk.Label(section, text="Audio file")
        self.audio_file_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Button(section, text="Select File", command=self.select_audio_file).grid(
            row=1, column=0, sticky="w"
        )
        tk.Label(section, textvariable=self.background_audio_file).grid(
            row=1, column=1, sticky="e"
        )

        self.play_audio_on_first_device_checkbutton = tk.Checkbutton(
            section,
            text="Playback on 1st device",
            variable=self.play_audio_on_first_device_flag,
            command=self.update_settings,
        )
        self.play_audio_on_first_device_checkbutton.grid(row=2, column=0, sticky="w")

        self.play_audio_on_second_device_checkbutton = tk.Checkbutton(
            section,
            text="Playback on 2nd device",
            variable=self.play_audio_on_second_device_flag,
            command=self.update_settings,
            state="disabled",
        )
        self.play_audio_on_second_device_checkbutton.grid(row=2, column=1, sticky="e")

        self.audio_volume_scale = tk.Scale(
            section,
            from_=0.0,
            to=3.0,
            orient="horizontal",
            label="Audio volume",
            variable=self.audio_volume,
            resolution=0.1,
            command=self.update_audio_volume,
        )
        self.audio_volume_scale.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.audio_position_scale = tk.Scale(
            section,
            from_=0,
            to=100,
            orient="horizontal",
            label="Audio position, %",
            variable=self.audio_position,
            resolution=1,
        )
        self.audio_position_scale.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.audio_position_scale.bind("<B1-Motion>", self.update_audio_position)

        self._update_audio_position_scale()

        self.device.set_background_audio_volume(self.audio_volume.get())
        self.device.set_background_audio_position(self.audio_position.get())

    # ----------------------------------------------------------------
    def _create_start_stop_section(self):
        section = tk.Frame(self, borderwidth=2, relief="groove", padx=10, pady=10)
        section.grid(row=3, column=0, sticky="ew")

        section.rowconfigure(0, weight=1)

        section.columnconfigure(1, weight=1)

        self.start_button = tk.Button(
            section, text="Start", command=self._start_device, width=20
        )
        self.start_button.grid(row=0, column=0, sticky="w")

        self.stop_button = tk.Button(
            section, text="Stop", command=self._stop_device, state="disabled", width=20
        )
        self.stop_button.grid(row=0, column=1, sticky="e")

    # ----------------------------------------------------------------
    def update_settings(self):
        self.device.set_second_output_device_enabled(
            self.second_output_device_enabled.get()
        )
        self.device.set_reverb_enabled(self.reverb_enabled.get())
        self.device.set_audio_reverb_enabled(self.audio_reverb_enabled.get())

        self.device.set_translate_sound_to_first_device_flag(
            self.translate_sound_to_first_device_flag.get()
        )
        self.device.set_translate_sound_to_second_device_flag(
            self.translate_sound_to_second_device_flag.get()
        )

        self.device.set_play_audio_on_first_device_flag(
            self.play_audio_on_first_device_flag.get()
        )
        self.device.set_play_audio_on_second_device_flag(
            self.play_audio_on_second_device_flag.get()
        )

        if self.second_output_device_enabled.get():
            if not self.device.is_running:
                self.output_device_entry_2["state"] = "normal"

            self.translate_sound_to_second_device_checkbutton["state"] = "normal"
            self.play_audio_on_second_device_checkbutton["state"] = "normal"
        else:
            self.output_device_entry_2["state"] = "disabled"

            self.translate_sound_to_second_device_checkbutton["state"] = "disabled"
            self.translate_sound_to_second_device_flag.set(value=False)

            self.play_audio_on_second_device_checkbutton["state"] = "disabled"
            self.play_audio_on_second_device_flag.set(value=False)

    def update_noise_threshold(self, threshold):
        self.device.set_noise_threshold(int(threshold))

    def update_reverb_room_size(self, room_size):
        self.device.set_reverb_room_size(float(room_size))

    def select_audio_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.background_audio_file.set(file_path)
            self.device.load_background_audio(file_path)

    def update_audio_volume(self, value):
        self.device.set_background_audio_volume(float(value))

    def update_audio_position(self, event):
        position = self.audio_position_scale.get()
        self.device.set_background_audio_position(int(position))

    def _update_audio_position_scale(self):
        current_position = self.device.get_background_audio_position()

        self.audio_position_scale.set(current_position)

        self.master.after(100, self._update_audio_position_scale)

    # ----------------------------------------------------------------
    def set_styles(self):
        root.resizable(True, False)
        root.wm_minsize(600, root.winfo_reqheight())

        for child in self.winfo_children():
            self.apply_margins(child)
            self.set_colors(child)
            self.set_fonts(child)

    def apply_margins(self, widget, padx=5, pady=5):
        if isinstance(widget, tk.Frame):
            for child in widget.winfo_children():
                self.apply_margins(child, padx, pady)
        else:
            widget.grid_configure(padx=padx, pady=pady)

    def set_colors(self, widget, bg_color="#303030", fg_color="#00A36C"):
        if isinstance(widget, tk.Frame):
            for child in widget.winfo_children():
                widget.configure(bg=bg_color)
                self.set_colors(child, bg_color, fg_color)
        else:
            try:
                widget.configure(bg=bg_color)
                widget.configure(fg=fg_color)
            except:
                pass

    def set_fonts(self, widget, family="Sitka Small"):
        if widget in [
            self.devices_label,
            self.audio_effects_label,
            self.audio_file_label,
        ]:
            widget.configure(font=(family, 16))
        else:
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    self.set_fonts(child)

            elif isinstance(widget, tk.Label):
                widget.configure(font=(family, 12))

            elif isinstance(widget, tk.Button):
                widget.configure(font=(family, 12))

            elif isinstance(widget, tk.Scale):
                widget.configure(font=(family, 12))

            elif isinstance(widget, tk.Checkbutton):
                widget.configure(font=(family, 12))

    # ----------------------------------------------------------------
    def _start_device(self):
        if self.device.is_running:
            messagebox.showwarning("Error", "Device is already running!")
            return

        try:
            input_index = int(self.input_device_index.get())
            output_1_index = int(self.output_device_1_index.get())
            output_2_index = int(self.output_device_2_index.get())

        except ValueError:
            messagebox.showwarning("Error", "Invalid device index!")
            return

        self.device.set_input_device_index(input_index)
        self.device.set_output_device_index(output_1_index)
        self.device.set_second_output_device_index(output_2_index)

        self.device.start()

        # Enable stop button and disable start button
        self.start_button["state"] = "disabled"
        self.stop_button["state"] = "normal"

        # Disable the input and output device index Entry widgets
        self.input_device_entry["state"] = "disabled"
        self.output_device_entry_1["state"] = "disabled"
        self.output_device_entry_2["state"] = "disabled"
        self.enable_second_output_device_checkbutton["state"] = "disabled"

    def _stop_device(self):
        if not self.device.is_running:
            messagebox.showwarning("Error", "Device is not running!")
            return

        self.device.stop()

        # Enable start button and disable stop button
        self.start_button["state"] = "normal"
        self.stop_button["state"] = "disabled"

        # Enable the input and output device index Entry widgets
        self.input_device_entry["state"] = "normal"
        self.output_device_entry_1["state"] = "normal"
        self.output_device_entry_2["state"] = "normal"
        self.enable_second_output_device_checkbutton["state"] = "normal"

    def _on_closing(self):
        if self.device.is_running:
            self._stop_device()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Virtual Micro Device")

    app = VirtualMicroGUI(master=root)

    root.mainloop()
