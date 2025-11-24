
import numpy as np
import sounddevice as sd

import sounddevice as sd
print(sd.query_devices())

# 1. Force the 'default' device (which routes to Pulse -> Bluetooth)
# We don't use the index anymore, we use the string name.

sr = 44100
t = np.linspace(0, 1, sr)
tone = 0.3 * np.sin(2 * np.pi * 440 * t)

# 2. Play
try:
    sd.play(tone, sr)
    sd.wait()
    print("Success!")
except Exception as e:
    print(f"Error: {e}")