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
                           plot_path=None,
                           device=None,
                           duration=None,
                           adaptive_refresh_chunks=10):
    """
    Noise reduction with noise profile, supporting mic or file input.
    Allows streaming, file saving, or both, with ~5s acceptable delay.
    Can run indefinitely (Ctrl+C to stop) if duration=None.
    Streaming playback included for 'stream' or 'stream+file' modes.

    If noise_profile_file == "adaptive", the noise profile will be re-estimated
    every `adaptive_refresh_chunks`.

    If visualization=True, will plot raw audio waveform and highlight
    detected noise profile regions. If plot_path is provided, saves to file.
    """

    rate = 16000  # default mic rate
    output_audio = []
    raw_audio = []
    stream_queue = queue.Queue()

    # ------------------------
    # Helper: adaptive profile
    # ------------------------
    def estimate_noise_profile(data, rate, silence_threshold, min_silence_duration):
        """Estimate noise profile from a signal segment. Returns (profile, start, end)."""
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
            return data[best_start:best_start + best_length], best_start, best_start + best_length
        else:
            # fallback: just take first chunk
            return data[: int(chunk_duration * rate)], 0, int(chunk_duration * rate)

    # keep track of noise profile regions for plotting
    noise_regions = []

    # ------------------------
    # FILE INPUT
    # ------------------------
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

        # Initial noise profile
        if os.path.exists(noise_profile_file):
            noise_profile, _ = sf.read(noise_profile_file)
            noise_regions.append((0, len(noise_profile)))
        elif noise_profile_file.startswith("first_") or noise_profile_file.startswith("last_"):
            part, seconds = noise_profile_file.split("_")
            seconds = float(seconds)
            sample_count = int(seconds * rate)
            if part == "first":
                noise_profile = data[:sample_count]
                noise_regions.append((0, sample_count))
            else:
                noise_profile = data[-sample_count:]
                noise_regions.append((total_samples - sample_count, total_samples))
        elif noise_profile_file == "adaptive":
            noise_profile, s, e = estimate_noise_profile(data, rate, silence_threshold, min_silence_duration)
            noise_regions.append((s, e))
        else:
            raise ValueError(f"Invalid noise_profile_file value: {noise_profile_file}")

        # Process chunks
        chunk_samples = int(chunk_duration * rate)
        chunk_count = 0
        for start in range(0, total_samples, chunk_samples):
            chunk = data[start:start + chunk_samples]

            # refresh noise profile every N chunks if adaptive
            if noise_profile_file == "adaptive" and chunk_count % adaptive_refresh_chunks == 0:
                noise_profile, s, e = estimate_noise_profile(chunk, rate, silence_threshold, min_silence_duration)
                noise_regions.append((start + s, start + e))

            reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced)
            raw_audio.extend(chunk)
            chunk_count += 1
            time.sleep(chunk_duration)

        # ✅ Visualization after processing
        if visualization:
            times = np.linspace(0, len(data) / rate, num=len(data))
            fig, ax = plt.subplots(figsize=(16, 4))
            ax.plot(times, data, label="Original Audio", alpha=0.6)
            for s, e in noise_regions:
                ax.axvspan(s / rate, e / rate, color="red", alpha=0.3, label="Noise Profile")
                avg_amp = np.mean(np.abs(data[s:e]))
                mid_t = (s + e) / (2 * rate)
                ax.text(mid_t, 0.8 * np.max(data), f"Avg={avg_amp:.4f}",
                        ha="center", va="bottom", fontsize=9,
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"))
            ax.set_title("Audio Signal with Detected Noise Profile")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())
            plt.tight_layout()
            if plot_path:
                plt.savefig(plot_path)
                print(f"[PLOT] Saved plot to {plot_path}")
                plt.close()
            else:
                plt.show()

    # ------------------------
    # MIC INPUT
    # ------------------------
    elif input_source == "mic":
        chunk_samples = int(chunk_duration * rate)
        print(f"[MIC] Recording{' indefinitely' if duration is None else f' for {duration}s'} ...")
        recorded_samples = 0
        noise_profile = None
        stop_flag = False
        chunk_count = 0

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
            nonlocal recorded_samples, noise_profile, stop_flag, chunk_count
            if status:
                print(status)
            chunk = indata[:frames, 0]
            raw_audio.extend(chunk)

            # initialize noise profile once
            if noise_profile is None:
                N = 0.5
                profile_samples = int(N * rate)
                if len(raw_audio) >= profile_samples:
                    noise_profile = np.array(raw_audio[:profile_samples])
                    noise_regions.append((0, profile_samples))

            # refresh adaptive profile every N chunks
            if noise_profile_file == "adaptive" and chunk_count % adaptive_refresh_chunks == 0 and len(raw_audio) > 0:
                noise_profile, s, e = estimate_noise_profile(np.array(raw_audio), rate, silence_threshold, min_silence_duration)
                noise_regions.append((s, e))
                print("[MIC] Adaptive noise profile updated.")

            if noise_profile is not None:
                reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            else:
                reduced = chunk

            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced)

            recorded_samples += frames
            chunk_count += 1
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

        # ✅ Visualization after mic recording
        if visualization and len(raw_audio) > 0:
            times = np.linspace(0, len(raw_audio) / rate, num=len(raw_audio))
            fig, ax = plt.subplots(figsize=(16, 4))
            ax.plot(times, raw_audio, label="Original Audio", alpha=0.6)

            # Define 4 cyclic heights on positive Y axis
            heights = [0.25, 0.5, 0.75, 1.0]  
            height_idx = 0  

            for s, e in noise_regions:
                ax.axvspan(s / rate, e / rate, color="red", alpha=0.3, label="Noise Profile")
                avg_amp = np.mean(np.abs(raw_audio[s:e]))
                mid_t = (s + e) / (2 * rate)

                # pick a cyclic height
                h_factor = heights[height_idx % len(heights)]
                height_idx += 1

                ax.text(mid_t, h_factor * np.max(raw_audio), f"Avg={avg_amp:.4f}",
                        ha="center", va="bottom", fontsize=9,
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"))

            ax.set_title("Audio Signal with Detected Noise Profile (Mic)")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())
            plt.tight_layout()

            if plot_path:
                plt.savefig(plot_path)
                print(f"[PLOT] Saved plot to {plot_path}")
                plt.close()
            else:
                plt.show()


    else:
        raise ValueError("input_source must be 'file' or 'mic'")

    # --- Save final output ---
    if output_mode in ("file", "stream+file") and output_file:
        sf.write(output_file, np.array(output_audio), rate)
        print(f"[FILE] Denoised audio saved to {output_file}")
        if save_raw_audio:
            raw_out_file = output_file.replace(".wav", "_raw.wav")
            sf.write(raw_out_file, np.array(raw_audio), rate)
            print(f"[FILE] Raw audio saved to {raw_out_file}")

    return stream_queue if output_mode in ("stream", "stream+file") else None



output_path = r"D:\Git_repos\ANC_with_noise_profiling\out_1.wav"
input_path = r"C:\Users\User_1\Desktop\noisy_fish.wav"
plot_path = r"D:\Git_repos\ANC_with_noise_profiling\out_1_plot.png"


result = reduce_noise_streaming(input_source="mic", # "mic", "file"
                                input_file=None,  # None or Path
                                output_file=output_path,
                                # noise_profile_file="first_0.5",
                                noise_profile_file="adaptive",
                                silence_threshold=0.01,
                                min_silence_duration=0.1,
                                output_mode="stream+file",
                                chunk_duration=2,
                                save_raw_audio=True,
                                visualization=True,
                                plot_path=plot_path,
                                device=None,
                                duration=None,
                                adaptive_refresh_chunks=4)


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