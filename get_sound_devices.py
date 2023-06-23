import pyaudio

p = pyaudio.PyAudio()

file = open("sound devices.txt", "w")

# Print input devices
file.writelines(["Input devices:\n"])
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        device_info = f"{i}: {info['name']}\n"
        file.writelines([device_info])

# Print output devices
file.writelines(["\nOutput devices:\n"])
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxOutputChannels"] > 0:
        device_info = f"{i}: {info['name']}\n"
        file.writelines([device_info])

p.terminate()
