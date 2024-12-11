#!/usr/bin/env python3

import pyaudio
import numpy as np
import sounddevice as sd

# Constants
THRESHOLD_NOISE = -60  # dB threshold for noise detection
THRESHOLD_DBFS_TO_DBU = -18  # Assuming 0 dBu = -18 dBFS
MAX_ALLOWED_DBU = 4  # +4 dBu max level
SAMPLING_RATE = 44100
CHUNK_SIZE = 1024

# ANSI escape codes for colored output
GREEN = "\033[92m"
ORANGE = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def list_audio_devices():
    """List all available audio devices."""
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    devices = []
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        devices.append(device_info)
    p.terminate()
    return devices

def detect_usb_mixer(devices):
    """Detect connected USB mixer, including Yamaha MG166CX-USB."""
    for device in devices:
        if "USB" in device['name']:
            return device
    return None

def analyze_audio_callback(indata, frames, time, status):
    """Callback function for real-time audio monitoring."""
    if status:
        print(f"Audio Status Error: {status}")

    # Convert raw audio data to decibels
    audio_data = np.linalg.norm(indata)  # RMS value
    dBFS = 20 * np.log10(audio_data + 1e-10)  # dBFS calculation to avoid log(0)
    dBu = dBFS + THRESHOLD_DBFS_TO_DBU  # Convert dBFS to dBu

    # Determine output color and message
    if dBu == 0:
        print(f"{GREEN}Signal OK: {dBu:.2f} dBu{RESET}")
    elif 0 < dBu <= MAX_ALLOWED_DBU:
        print(f"{ORANGE}Signal Slightly Too Loud: {dBu:.2f} dBu{RESET}")
    elif dBu > MAX_ALLOWED_DBU:
        print(f"{RED}Signal Too Loud: {dBu:.2f} dBu{RESET}")
    else:
        print(f"Signal Level: {dBu:.2f} dBu")

    # Check for noise/humming
    if dBu < THRESHOLD_NOISE:
        print(f"{ORANGE}⚠️ Noise or humming detected!{RESET}")

def measure_gain(indata):
    """Measure gain for each channel in real-time."""
    rms_values = np.sqrt(np.mean(np.square(indata), axis=0))  # RMS per channel
    gains_dbfs = 20 * np.log10(rms_values + 1e-10)  # Gain in dBFS
    gains_dbu = gains_dbfs + THRESHOLD_DBFS_TO_DBU  # Convert dBFS to dBu
    return gains_dbu

def main():
    print("Available audio devices:")
    print(sd.query_devices())  # Use sounddevice to list devices

    print("\nDetecting audio devices using PyAudio...")
    devices = list_audio_devices()
    mixer = detect_usb_mixer(devices)

    if mixer:
        print(f"\nDetected Mixer: {mixer['name']}")
        channels = mixer['maxInputChannels']
        if channels > 2:
            print("Mode: Stereo")
        elif channels == 1:
            print("Mode: Mono")
        else:
            print("Mode: No mode")

        print("Starting real-time audio analysis...")
        with sd.InputStream(
            device=mixer['index'],
            channels=channels,
            samplerate=SAMPLING_RATE,
            callback=analyze_audio_callback,
            blocksize=CHUNK_SIZE,
        ):
            print("Monitoring audio... Press Ctrl+C to stop.")
            while True:
                pass
    else:
        print("No USB mixer detected.")

if __name__ == "__main__":
    main()

