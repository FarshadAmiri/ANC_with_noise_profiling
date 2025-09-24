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


def anc(input_source="mic",
        input_path=None,
        output_mode="stream+file",
        output_path=None,
        noise_profile_mode="adaptive",
        noise_amp_threshold=0.025,
        min_noise_duration=0.2,
        chunk_duration=2.5,
        save_raw_audio=False,
        visualization=False,
        plot_path=None,
        device=None,
        duration=None,
        adaptive_refresh_chunks=4):
    """
    Noise reduction (streaming/file) using a noise profile.

    Main features:
    ---------------
    - Input sources:
        * input_source="file" → process from a .wav file (input_path should be provided)
        * input_source="mic"  → process from microphone (real-time)

    - Output modes:
        * output_mode="file"        → save denoised audio only
        * output_mode="stream"      → play denoised audio in real-time
        * output_mode="stream+file" → both play and save denoised audio

    - Noise profile selection (noise_profile_mode):
        * "first_X" → use first X seconds of audio as noise profile
        * "last_X"  → use last X seconds
        * "adaptive" → adaptively update noise profile every
                    `adaptive_refresh_chunks` chunks
            - Chooses the *latest valid silence region*
            - If no valid region is found, keeps the previous profile
            (logs this event)

    - Silence detection:
        * Based on RMS amplitude compared to `noise_amp_threshold`
        * Minimum silence duration = `min_noise_duration` (in seconds)

    - Duration control:
        * If duration=N (seconds), recording/processing stops after N seconds
        * If duration=None, continues until stopped manually (Ctrl+C)

    - Chunking:
        * The audio is processed in chunks of length `chunk_duration` seconds
        * Smaller chunks → lower latency, but less stable noise profiling
        * Larger chunks → smoother noise profiling, but higher latency
        * Typical values: 0.25s – 1s for streaming; up to a few seconds for offline
        
    - Visualization (optional):
        * Plots the waveform of raw audio
        * Highlights noise profile regions in red
        * Adds text labels with average amplitude of each noise profile region
        * Cycles label heights across 4 Y-positions for readability
        * If `plot_path` is given, saves figure instead of showing interactively

    - File saving:
        * If output_mode includes "file", saves denoised audio to `output_path`
        * If save_raw_audio=True, also saves raw input audio as `<output_file_name>_raw.wav`

    """

    # Normalize "both" alias
    if output_mode == "both":
        output_mode = "stream+file"

    # Default microphone samplerate (used when input_source == "mic" and no file sets rate)
    DEFAULT_MIC_SR = 48000

    # Output buffers
    output_audio = []     # processed audio samples
    raw_audio = []        # raw samples (mono)
    stream_queue = queue.Queue()
    noise_regions = []    # list of (start_sample, end_sample) regions used as noise profile

    # Keep current noise profile (None until established)
    noise_profile = None

    # helper: find latest valid silence region or fallback
    def estimate_noise_profile(data, rate, noise_amp_threshold, min_noise_duration, latest=False):
        """
        Scan `data` and return (profile_array, start_idx, end_idx).
        If latest=True choose the latest valid silence region (highest start idx).
        If none found, return (None, None, None).
        """
        if data is None or len(data) == 0:
            return None, None, None

        window_size = max(1, int(0.05 * rate))   # 50ms windows
        stride = max(1, window_size // 2)
        min_samples = max(1, int(min_noise_duration * rate))

        best_start = None
        best_len = 0

        i = 0
        while i <= len(data) - window_size:
            window = data[i:i + window_size]
            rms = float(np.sqrt(np.mean(window ** 2)))
            if rms < noise_amp_threshold:
                start = i
                # advance until window energy rises above threshold
                while i <= len(data) - window_size:
                    window2 = data[i:i + window_size]
                    rms2 = float(np.sqrt(np.mean(window2 ** 2)))
                    if rms2 >= noise_amp_threshold:
                        break
                    i += stride
                end = i
                length = end - start
                if length >= min_samples:
                    if latest:
                        # choose latest occurrence (overwrite)
                        best_start, best_len = start, length
                    else:
                        # choose longest
                        if length > best_len:
                            best_start, best_len = start, length
            else:
                i += stride

        if best_start is not None:
            prof = data[best_start: best_start + best_len].astype(np.float32)
            return prof, best_start, best_start + best_len

        # no valid region found
        return None, None, None

    # ------- FILE mode -------
    if input_source == "file":
        if not input_path:
            raise ValueError("input_path must be specified when input_source='file'")

        data, rate = sf.read(input_path, dtype='float32')
        # convert to mono if needed
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        total_samples = len(data)

        # apply duration limit if requested
        if duration is not None:
            max_samples = int(duration * rate)
            data = data[:max_samples]
            total_samples = len(data)

        # initial noise profile selection
        if os.path.exists(noise_profile_mode):
            prof, _ = sf.read(noise_profile_mode, dtype='float32')
            noise_profile = prof if prof.ndim == 1 else np.mean(prof, axis=1).astype(np.float32)
            noise_regions.append((0, len(noise_profile)))
            print("[INIT] noise profile loaded from file")
        elif noise_profile_mode.startswith("first_") or noise_profile_mode.startswith("last_"):
            try:
                part, sec = noise_profile_mode.split("_")
                sec = float(sec)
            except Exception:
                raise ValueError("Invalid first_/last_ noise_profile_mode format")
            sample_count = int(sec * rate)
            if part == "first":
                noise_profile = data[:sample_count].astype(np.float32)
                noise_regions.append((0, sample_count))
            else:
                noise_profile = data[-sample_count:].astype(np.float32)
                noise_regions.append((total_samples - sample_count, total_samples))
            print(f"[INIT] noise profile taken from '{noise_profile_mode}'")
        elif noise_profile_mode == "adaptive":
            prof, s, e = estimate_noise_profile(data, rate, noise_amp_threshold, min_noise_duration, latest=True)
            if prof is not None:
                noise_profile = prof
                noise_regions.append((s, e))
                print(f"[INIT] adaptive profile found in file at {s}:{e}")
            else:
                print("[INIT] adaptive requested but no valid profile found in whole file -> will wait for refresh (keep None)")
        else:
            raise ValueError("Invalid noise_profile_mode value")

        # Process file in chunks, keeping recent_chunks window
        chunk_samples = int(chunk_duration * rate)
        recent_chunks = []
        chunk_count = 0

        for start in range(0, total_samples, chunk_samples):
            chunk = data[start: start + chunk_samples].astype(np.float32)
            raw_audio.extend(chunk.tolist())

            # update recent window
            recent_chunks.append(chunk.copy())
            if len(recent_chunks) > adaptive_refresh_chunks:
                recent_chunks.pop(0)
            recent_audio = np.concatenate(recent_chunks) if len(recent_chunks) > 0 else np.array([])

            # Attempt adaptive refresh every adaptive_refresh_chunks
            if noise_profile_mode == "adaptive" and (chunk_count % adaptive_refresh_chunks == 0):
                if len(recent_audio) > 0:
                    prof, s_rel, e_rel = estimate_noise_profile(recent_audio, rate, noise_amp_threshold, min_noise_duration, latest=True)
                    if prof is not None:
                        # verify prof meets silence threshold (safety)
                        prof_rms = float(np.sqrt(np.mean(prof ** 2)))
                        if prof_rms < noise_amp_threshold:
                            # compute global indices:
                            recent_len = len(recent_audio)
                            # global start of recent_audio:
                            global_start = start - (recent_len - len(chunk))
                            global_s = global_start + s_rel
                            global_e = global_start + e_rel
                            # clamp
                            global_s = max(0, int(global_s))
                            global_e = min(total_samples, int(global_e))
                            noise_profile = prof
                            noise_regions.append((global_s, global_e))
                            print(f"[REFRESH] adaptive updated from file recent window -> global {global_s}:{global_e} (rms={prof_rms:.6f})")
                        else:
                            print(f"[REFRESH] candidate found but RMS {prof_rms:.6f} >= noise_amp_threshold {noise_amp_threshold:.6f} -> keep old profile")
                    else:
                        print("[REFRESH] no candidate profile in recent chunks -> keep old profile")
                else:
                    print("[REFRESH] recent window empty -> skip")

            # denoise chunk (if profile exists)
            if noise_profile is not None:
                reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            else:
                reduced = chunk

            # stream and/or append to file buffer
            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced.tolist())

            chunk_count += 1
            # simulate chunk-duration processing latency (keep behavior same as before)
            time.sleep(chunk_duration)

        # Visualization for file mode
        if visualization:
            times = np.linspace(0, len(data) / rate, num=len(data))
            fig, ax = plt.subplots(figsize=(16, 4))
            ax.plot(times, data, label="Original Audio", alpha=0.6)

            heights = [0.25, 0.5, 0.75, 1.0]
            height_idx = 0
            data_max = np.max(np.abs(data)) if len(data) > 0 else 1.0

            for (s, e) in noise_regions:
                s = max(0, int(s))
                e = min(len(data), int(e))
                if s >= e:
                    continue
                ax.axvspan(s / rate, e / rate, color="red", alpha=0.3, label="Noise Profile")
                avg_amp = float(np.mean(np.abs(data[s:e])))
                mid_t = (s + e) / (2 * rate)
                h_factor = heights[height_idx % len(heights)]
                height_idx += 1
                ax.text(mid_t, h_factor * data_max, f"Avg={avg_amp:.4f}",
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

    # ------- MIC mode -------
    elif input_source == "mic":
        # use a practical mic rate
        rate = DEFAULT_MIC_SR
        chunk_samples = int(chunk_duration * rate)

        print(f"[MIC] Recording {'indefinitely' if duration is None else f'for {duration}s'} at {rate}Hz, chunk={chunk_duration}s ...")

        # playback thread (consume stream_queue)
        stop_flag = False

        def playback_thread():
            with sd.OutputStream(samplerate=rate, channels=1, dtype='float32') as out_stream:
                while not stop_flag or not stream_queue.empty():
                    try:
                        c = stream_queue.get(timeout=0.1)
                        # c should be numpy array float32
                        out_stream.write(np.asarray(c, dtype=np.float32))
                    except queue.Empty:
                        time.sleep(0.01)

        if output_mode in ("stream", "stream+file"):
            playback_t = threading.Thread(target=playback_thread, daemon=True)
            playback_t.start()

        recorded_samples = 0
        chunk_count = 0
        recent_chunks = []

        def mic_callback(indata, frames, tinfo, status):
            nonlocal recorded_samples, noise_profile, chunk_count, recent_chunks, stop_flag
            if status:
                print("[MIC STATUS]", status)
            # take first channel
            chunk = indata[:, 0].astype(np.float32)
            # append raw audio
            raw_audio.extend(chunk.tolist())

            # update recent_chunks rolling buffer
            recent_chunks.append(chunk.copy())
            if len(recent_chunks) > adaptive_refresh_chunks:
                recent_chunks.pop(0)
            recent_audio = np.concatenate(recent_chunks) if len(recent_chunks) > 0 else np.array([])

            # initialize noise profile from first_{N} if requested and profile is still None
            if noise_profile is None and isinstance(noise_profile_mode, str) and noise_profile_mode.startswith("first_"):
                try:
                    _, sec = noise_profile_mode.split("_")
                    prof_len_s = float(sec)
                except Exception:
                    prof_len_s = 0.5
                prof_samples = int(prof_len_s * rate)
                if len(raw_audio) >= prof_samples:
                    noise_profile = np.array(raw_audio[:prof_samples], dtype=np.float32)
                    noise_regions.append((0, prof_samples))
                    print(f"[INIT] noise profile initialized from first_{prof_len_s}s")

            # If noise_profile_mode == "adaptive", attempt refresh every adaptive_refresh_chunks
            if noise_profile_mode == "adaptive" and (chunk_count % adaptive_refresh_chunks == 0):
                if len(recent_audio) > 0:
                    prof, s_rel, e_rel = estimate_noise_profile(recent_audio, rate, noise_amp_threshold, min_noise_duration, latest=True)
                    if prof is not None:
                        prof_rms = float(np.sqrt(np.mean(prof ** 2)))
                        if prof_rms < noise_amp_threshold:
                            # compute global start index of recent_audio:
                            start_idx = recorded_samples  # start of current chunk in global samples
                            recent_len = len(recent_audio)
                            global_start = start_idx - (recent_len - len(chunk))
                            global_s = max(0, int(global_start + s_rel))
                            global_e = max(0, int(global_start + e_rel))
                            noise_profile = prof
                            noise_regions.append((global_s, global_e))
                            print(f"[REFRESH] adaptive profile updated (mic) -> global {global_s}:{global_e} (rms={prof_rms:.6f})")
                        else:
                            print(f"[REFRESH] candidate found in recent_audio but RMS {prof_rms:.6f} >= noise_amp_threshold {noise_amp_threshold:.6f} -> keep old profile")
                    else:
                        print("[REFRESH] no candidate profile found in recent chunks -> keep old profile")

            # denoise current chunk if we have a profile
            if noise_profile is not None:
                reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile, sr=rate)
            else:
                reduced = chunk

            # stream/playback
            if output_mode in ("stream", "stream+file"):
                stream_queue.put(reduced)

            # accumulate for file saving
            if output_mode in ("file", "stream+file"):
                output_audio.extend(reduced.tolist())

            recorded_samples += len(chunk)
            chunk_count += 1

            # stop condition requested
            if duration is not None and recorded_samples >= int(duration * rate):
                # signal main to stop by raising CallbackStop
                raise sd.CallbackStop()

        # open stream
        try:
            with sd.InputStream(samplerate=rate, channels=1, blocksize=chunk_samples, dtype='float32',
                                device=device, callback=mic_callback):
                # block for duration or until KeyboardInterrupt
                if duration is not None:
                    sd.sleep(int(duration * 1000))
                else:
                    # allow ctrl+c to stop
                    try:
                        while True:
                            time.sleep(0.1)
                    except KeyboardInterrupt:
                        print("[MIC] stopped by user (KeyboardInterrupt)")
        except Exception as e:
            print("[ERROR] microphone input stream error:", e)

        # ensure playback thread finishes
        stop_flag = True
        if output_mode in ("stream", "stream+file") and 'playback_t' in locals():
            playback_t.join(timeout=1.0)

        # Visualization for mic mode
        if visualization and len(raw_audio) > 0:
            data_arr = np.asarray(raw_audio, dtype=np.float32)
            times = np.linspace(0, len(data_arr) / rate, num=len(data_arr))
            fig, ax = plt.subplots(figsize=(16, 4))
            ax.plot(times, data_arr, label="Original Audio", alpha=0.6)

            heights = [0.25, 0.5, 0.75, 1.0]
            height_idx = 0
            data_max = np.max(np.abs(data_arr)) if data_arr.size > 0 else 1.0

            for (s, e) in noise_regions:
                s = max(0, int(s)); e = min(len(data_arr), int(e))
                if s >= e:
                    continue
                ax.axvspan(s / rate, e / rate, color="red", alpha=0.3, label="Noise Profile")
                avg_amp = float(np.mean(np.abs(data_arr[s:e])))
                mid_t = (s + e) / (2 * rate)
                h_factor = heights[height_idx % len(heights)]
                height_idx += 1
                ax.text(mid_t, h_factor * data_max, f"Avg={avg_amp:.4f}",
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

    # ---- Save files ----
    if output_mode in ("file", "stream+file") and output_path:
        # make sure output_audio is a numpy array
        if len(output_audio) > 0:
            out_arr = np.asarray(output_audio, dtype=np.float32)
            sf.write(output_path, out_arr, rate)
            print(f"[FILE] Denoised audio saved to {output_path}")
        else:
            print("[FILE] No processed audio to save.")

    if save_raw_audio and output_path:
        raw_out = output_path.replace(".wav", "_raw.wav")
        if len(raw_audio) > 0:
            sf.write(raw_out, np.asarray(raw_audio, dtype=np.float32), rate)
            print(f"[FILE] Raw audio saved to {raw_out}")
        else:
            print("[FILE] No raw audio to save.")

    # return the queue for streaming consumption if requested
    return stream_queue if output_mode in ("stream", "stream+file") else None



output_path = r"D:\Git_repos\ANC_with_noise_profiling\out_1.wav"
input_path = r"C:\Users\User_1\Desktop\noisy_fish.wav"
plot_path = r"D:\Git_repos\ANC_with_noise_profiling\out_1_plot.png"


result = anc(input_source="mic", # "mic", "file"
            input_path=None,  # None or Path
            output_path=output_path,
            # noise_profile_mode="first_0.5",
            noise_profile_mode="adaptive",
            noise_amp_threshold=0.025,
            min_noise_duration=0.1,
            output_mode="stream+file",
            chunk_duration=2.5,
            save_raw_audio=True,
            visualization=True,
            plot_path=plot_path,
            device=None,
            duration=None,
            adaptive_refresh_chunks=4)