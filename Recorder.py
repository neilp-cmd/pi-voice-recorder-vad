import sounddevice as sd
import numpy as np
import wave
import time
import os
import subprocess
from datetime import datetime

# === CONFIG ===
THRESHOLD = 500          # adjust if too sensitive / not enough
SILENCE_TIMEOUT = 2      # stop after 2 seconds of silence
SAMPLE_RATE = 16000
CHUNK = 1024
CHANNELS = 1
RECORDINGS_DIR = "recordings"
REMOTE_NAME = "gdrive"   # rclone remote name, optional

os.makedirs(RECORDINGS_DIR, exist_ok=True)

def rms(data):
    return np.sqrt(np.mean(np.square(data)))

def record_audio():
    print("Listening for voice...")
    while True:
        audio = sd.rec(CHUNK, SAMPLE_RATE, CHANNELS, dtype='int16')
        sd.wait()
        if rms(audio) > THRESHOLD:
            print("Voice detected! Recording...")
            break

    frames = [audio]
    silent_chunks = 0

    while True:
        audio = sd.rec(CHUNK, SAMPLE_RATE, CHANNELS, dtype='int16')
        sd.wait()
        frames.append(audio)
        if rms(audio) < THRESHOLD:
            silent_chunks += 1
        else:
            silent_chunks = 0
        if silent_chunks > SILENCE_TIMEOUT * SAMPLE_RATE / CHUNK:
            print("Silence detected. Stopping.")
            break

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{RECORDINGS_DIR}/rec_{timestamp}.wav"
    wf = wave.open(fname, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(f.tobytes() for f in frames))
    wf.close()
    print(f"Saved: {fname}")
    return fname

def upload(fname):
    try:
        subprocess.run(["rclone", "copy", fname, f"{REMOTE_NAME}:voice-recordings"], check=True)
        print(f"Uploaded {fname}")
    except Exception as e:
        print("Upload failed:", e)

def main():
    while True:
        try:
            f = record_audio()
            upload(f)
        except Exception as e:
            print("Error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
