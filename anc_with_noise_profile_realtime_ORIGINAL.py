import os
import numpy as np
import soundfile as sf
import sounddevice as sd
import noisereduce as nr
import matplotlib.pyplot as plt
import queue
import threading
import sys
import time


def reduce_noise_streaming(input_source="file",
                           input_file=None,
                           output_file=None,
                           noise_profile_file="first_0.5",
                           silence_threshold=0.01,
                           min_silence_duration=0.3,
                           output_mode="file",
                           chunk_duration=0.5,
                           save_raw_audio=False,
                           visualization=False,
                           device=None,
                           duration=None):
    """
    Noise reduction with noise profile, supporting mic or file input.
    Allows streaming, file saving, or both, with ~5s acceptable delay.
    Can run indefinitely (Ctrl+C to stop) if duration=None.
    Streaming playback included for 'stream' or 'stream+file' modes.
    """

    rate = 16000  # default mic rate
    output_audio = []
    raw_audio = []
    stream_queue = queue.Queue()

    # --- Determine input ---
    if input_source == "file":
        if not input_file:
            raise ValueError("input_file must be specified when input_source='file'")
        data, rate = sf.read(input_file)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        total_samples = len(data)
        if duration is not None:
            max_samples = int(duration * rate)
            data = data[:max_samples]
            total_samples = len(data)

        # Determine noise profile
        if os.path.exists(noise_profile_file):
            noise_profile, _ = sf.read(noise_profile_file)
        elif noise_profile_file.startswith("first_") or noise_profile_file.startswith("last_"):
            part, seconds = noise_profile_file.split("_")
            seconds = float(seconds)
            sample_count = int(seconds * rate)
            if part == "first":
                noise_profile = data[:sample_count]
            else:
                noise_profile = data[-sample_count:]
        elif noise_profile_file == "adaptive":
            window_size = int(0.05 * rate)
            stride = window_size // 2
            min_samples = int(min_silence_duration * rate)
            best_start, best_length = None, 0
            i = 0
            while i < len(data) - window_size:
                window = data[i:i + window_size]
                rms = np.sqrt(np.mean(window**2))
                if rms < silence_threshold:
                    start = i
                    while i < len(data) - window_size:
                        window = data[i:i + window_size]
                        rms = np.sqrt(np.mean(window**2))
                        if rms >= silence_threshold:
                            break
                        i += stride
                    end = i
                    if end - start > best_length and (end - start) >= min_samples:
                        best_start, best_length = start, end - start
                else:
                    i += stride
            if best_start is not None:
                noise_profile = data[best_start:best_start + best_length]
            else:
                noise_profile = data[:int(chunk_duration * rate)]

        # Process chunks
        chunk_samples = int(chunk_duration * rate)
        for start in range(0, total_samples, chunk_samples):
            chunk = data[start:start + chunk_samples]
            reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced)
            raw_audio.extend(chunk)

    elif input_source == "mic":
        chunk_samples = int(chunk_duration * rate)
        print(f"[MIC] Recording{' indefinitely' if duration is None else f' for {duration}s'} ...")
        recorded_samples = 0
        noise_profile = None
        stop_flag = False

        # --- Playback thread ---
        def playback_thread():
            with sd.OutputStream(channels=1, samplerate=rate, dtype="float32") as out_stream:
                while not stop_flag or not stream_queue.empty():
                    try:
                        chunk = stream_queue.get(timeout=0.1)
                        out_stream.write(chunk.astype(np.float32))
                    except queue.Empty:
                        time.sleep(0.01)

        if output_mode in ("stream", "stream+file"):
            t_playback = threading.Thread(target=playback_thread, daemon=True)
            t_playback.start()

        def callback(indata, frames, t, status):
            nonlocal recorded_samples, noise_profile, stop_flag
            if status:
                print(status)
            chunk = indata[:frames, 0]
            raw_audio.extend(chunk)

            # Noise profile from first 0.5s
            if noise_profile is None:
                N = 0.5
                profile_samples = int(N * rate)
                if len(raw_audio) >= profile_samples:
                    noise_profile = np.array(raw_audio[:profile_samples])

            if noise_profile is not None:
                reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            else:
                reduced = chunk

            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced)

            recorded_samples += frames
            if duration is not None and recorded_samples >= int(duration * rate):
                stop_flag = True
                raise sd.CallbackStop()

        with sd.InputStream(callback=callback, channels=1, samplerate=rate,
                            blocksize=chunk_samples, dtype="float32", device=device):
            try:
                if duration is not None:
                    sd.sleep(int(duration * 1000))
                else:
                    while not stop_flag:
                        time.sleep(0.1)
            except KeyboardInterrupt:
                print("[MIC] Recording stopped by user.")
                stop_flag = True

        if output_mode in ("stream", "stream+file") and 't_playback' in locals():
            t_playback.join()

    # --- Save final output ---
    if output_mode in ("file", "stream+file") and output_file:
        sf.write(output_file, np.array(output_audio), rate)
        print(f"[FILE] Denoised audio saved to {output_file}")
        if save_raw_audio:
            raw_out_file = output_file.replace(".wav", "_raw.wav")
            sf.write(raw_out_file, np.array(raw_audio), rate)
            print(f"[FILE] Raw audio saved to {raw_out_file}")

    return stream_queue if output_mode in ("stream", "stream+file") else None





input_path = r"C:\Users\User_1\Desktop\noisy_fish.wav"
# input_path = r"D:\Git_repos\Noise_reduction_repos\DeepNoiseReducer\noisy_auido_files\Comm1.mp3"
output_path = r"D:\Git_repos\Noise_reduction_repos\DeepNoiseReducer\out_2.wav"

result = reduce_noise_streaming(input_source="mic", # "mic", "file"
                                input_file=None,  # None or Path
                                output_file=output_path,
                                noise_profile_file="first_0.5",
                                silence_threshold=0.01,
                                min_silence_duration=0.3,
                                output_mode="stream+file",
                                chunk_duration=4,
                                save_raw_audio=True,
                                visualization=False,
                                device=None,
                                duration=None)


# result = reduce_noise_streaming(input_source="file", # "mic", "file"
#                                 input_file=input_path,  # None or Path
#                                 output_file=output_path,
#                                 noise_profile_file="first_0.5",
#                                 silence_threshold=0.01,
#                                 min_silence_duration=0.3,
#                                 output_mode="stream+file",
#                                 chunk_duration=4,
#                                 save_raw_audio=True,
#                                 visualization=False,
#                                 device=None,
#                                 duration=None)