# music_controller.py
import os
import subprocess
import time
import shutil

class MusicController:
    # --- Basic checks and setup ---
    def __init__(self, tracks):
        # 1) If tracks is None, use empty dict. Otherwise, convert all given paths to absolute paths.
        # 2) Store a list of track names for navigation (next/prev).
        # 3) Initialize state for the main channel: current track, file path, paused flag, and PS process.
        # 4) Initialize state for three additional channels (1, 2, 3) similarly.
        # 5) Locate the PowerShell executable so we can use SoundPlayer to loop WAV files.
        self.tracks = {name: os.path.abspath(path) for name, path in (tracks or {}).items()}
        self.track_names = list(self.tracks.keys())

        # main channel state
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        self._ps_proc = None

        # channel 1 state
        self.current_track1 = None
        self.current_path1 = None
        self.is_paused1 = False
        self._ps_proc1 = None

        # channel 2 state
        self.current_track2 = None
        self.current_path2 = None
        self.is_paused2 = False
        self._ps_proc2 = None

        # channel 3 state
        self.current_track3 = None
        self.current_path3 = None
        self.is_paused3 = False
        self._ps_proc3 = None

        self._powershell = shutil.which("powershell") or shutil.which("powershell.exe")

    def _is_wav(self, path):
        # 1) Confirm the input is a string.
        # 2) Check that the file extension ends with .wav (case-insensitive).
        return isinstance(path, str) and path.lower().endswith('.wav')

    def _find_by_basename(self, basename):
        # 1) Search two places: the directory of this script and the current working directory.
        # 2) For each directory: list files and compare each item's lowercase name with the requested basename.
        # 3) If matched, return the full path to the file.
        # 4) If not found anywhere, return None.
        for i in (os.path.dirname(__file__), os.getcwd()):
            try:
                for item in os.listdir(i):
                    if item.lower() == basename.lower():
                        return os.path.join(i, item)
            except Exception:
                continue
        return None

    def _stop_proc(self, proc_attr):
        # 1) Read the subprocess stored under the given attribute name (e.g., "_ps_proc2").
        # 2) If there is an active process:
        #    a) Ask it to terminate.
        #    b) Wait briefly to let it exit.
        #    c) If it still hasn't exited, force kill it.
        # 3) Regardless of success or failure, set the attribute to None so state is consistent.
        proc = getattr(self, proc_attr)
        if proc:
            try:
                proc.terminate()
                time.sleep(0.05)
                if proc.poll() is None:
                    proc.kill()
            except Exception as e:
                print(f"Stop failed for {proc_attr}: {e}")
            setattr(self, proc_attr, None)

    def _launch_ps_loop(self, path, slot):
        # 1) Ensure PowerShell is available; if not, inform the user and return None.
        # 2) Escape single quotes in the path to avoid breaking the PS command.
        # 3) Build a PowerShell command that:
        #    a) Creates a System.Media.SoundPlayer for the WAV file.
        #    b) Loads the file.
        #    c) Starts looping playback.
        #    d) Sleeps "forever" to keep the process alive while audio loops.
        # 4) Start PowerShell hidden with no profile, capture stdout/stderr.
        # 5) On success, return the process; on error, print and return None.
        if not self._powershell:
            print("PowerShell not found.")
            return None
        safe = path.replace("'", "''")
        ps_script = f"& {{ $p = New-Object System.Media.SoundPlayer '{safe}'; $p.Load(); $p.PlayLooping(); Start-Sleep -Seconds 999999 }}"
        try:
            proc = subprocess.Popen(
                [self._powershell, "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"PowerShell loop started for channel {slot}: {path}")
            return proc
        except Exception as e:
            print(f"PowerShell start failed for channel {slot}: {e}")
            return None

    # --- Main channel ---
    def play(self, name):
        # 1) Confirm the requested track name exists in the configuration.
        # 2) Get the configured path for this track.
        # 3) If the path doesn't exist:
        #    a) Try to find the file by searching for the same basename in known directories.
        #    b) If found, update the config path to the resolved absolute path.
        #    c) If not found, inform the user and abort.
        # 4) Ensure the file is a WAV; if not, inform the user and abort.
        # 5) Stop any existing main-channel playback process to avoid overlap.
        # 6) Launch a new PowerShell looping process for the resolved path.
        # 7) If launch succeeds, update current track state and mark as playing (not paused).
        if name not in self.tracks:
            print(f"Track '{name}' not configured.")
            return
        path = self.tracks[name]
        if not os.path.exists(path):
            alt = self._find_by_basename(os.path.basename(path))
            if alt:
                path = os.path.abspath(alt)
                self.tracks[name] = path
                print(f"Resolved '{name}' -> {path}")
            else:
                print(f"File not found for '{name}': {path}")
                return
        if not self._is_wav(path):
            print("Only WAV supported:", path)
            return
        self._stop_proc("_ps_proc")
        proc = self._launch_ps_loop(path, "main")
        if proc:
            self._ps_proc = proc
            self.current_track = name
            self.current_path = path
            self.is_paused = False
            print(f"Playing track: {name}")

    def pause(self):
        # 1) If nothing is currently playing on the main channel, inform the user and exit.
        # 2) Stop the current main-channel process.
        # 3) Set the paused flag so resume knows it can restart the same track.
        if not self.current_track:
            print("Nothing is playing.")
            return
        self._stop_proc("_ps_proc")
        self.is_paused = True
        print("Paused main channel.")

    def resume(self):
        # 1) Ensure there is a track to resume and that the channel is paused.
        # 2) Ensure the path still exists; if not, inform the user and abort.
        # 3) Reset paused flag and call play() with the current track to relaunch looping playback.
        # 4) Inform the user that the main channel was resumed.
        if not self.current_track or not self.is_paused:
            print("Nothing to resume.")
            return
        if not self.current_path or not os.path.exists(self.current_path):
            print("Cannot resume: file missing.")
            return
        self.is_paused = False
        self.play(self.current_track)
        print("Resumed main channel.")

    def stop(self):
        # 1) Stop any active main-channel playback process.
        # 2) Clear the current track and path.
        # 3) Reset paused flag to False.
        # 4) Inform the user.
        self._stop_proc("_ps_proc")
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        print("Stopped main channel.")

    def next_track(self):
        # 1) Ensure there is a current track and the list of tracks is available.
        # 2) Find the index of the current track within the track list.
        # 3) Compute the next index with wrap-around using modulo.
        # 4) Play the next track by name.
        if not self.track_names or self.current_track not in self.track_names:
            print("No current track to advance from.")
            return
        idx = self.track_names.index(self.current_track)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play(next_name)

    def prev_track(self):
        # 1) Ensure there is a current track and the list of tracks is available.
        # 2) Find the index of the current track within the track list.
        # 3) Compute the previous index with wrap-around using modulo.
        # 4) Play the previous track by name.
        if not self.track_names or self.current_track not in self.track_names:
            print("No current track to go back from.")
            return
        idx = self.track_names.index(self.current_track)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play(prev_name)

    # --- Channel 1 ---
    def play1(self, name):
        # 1) Validate track name exists in the configuration.
        # 2) Ensure the file exists at the configured path.
        # 3) Ensure the file is a WAV.
        # 4) Stop any existing channel-1 process.
        # 5) Launch a new PowerShell looping process for channel 1.
        # 6) Update channel-1 state and inform the user.
        if name not in self.tracks:
            print(f"Track '{name}' not configured.")
            return
        path = self.tracks[name]
        if not os.path.exists(path):
            print(f"File not found for '{name}': {path}")
            return
        if not self._is_wav(path):
            print("Only WAV supported:", path)
            return
        self._stop_proc("_ps_proc1")
        proc = self._launch_ps_loop(path, "1")
        if proc:
            self._ps_proc1 = proc
            self.current_track1 = name
            self.current_path1 = path
            self.is_paused1 = False
            print(f"Playing track1: {name}")

    def pause1(self):
        # 1) If channel 1 isn't currently playing, inform the user and exit.
        # 2) Stop the channel-1 process.
        # 3) Mark channel 1 as paused.
        if not self.current_track1:
            print("Nothing is playing on channel 1.")
            return
        self._stop_proc("_ps_proc1")
        self.is_paused1 = True
        print("Paused channel 1.")

    def resume1(self):
        # 1) Confirm channel 1 has a track and is paused.
        # 2) Confirm the stored path exists.
        # 3) Clear the paused flag and restart playback of the same track.
        # 4) Inform the user.
        if not self.current_track1 or not self.is_paused1:
            print("Nothing to resume on channel 1.")
            return
        if not self.current_path1 or not os.path.exists(self.current_path1):
            print("Cannot resume channel 1: file missing.")
            return
        self.is_paused1 = False
        self.play1(self.current_track1)
        print("Resumed channel 1.")

    def stop1(self):
        # 1) Stop any active channel-1 process.
        # 2) Clear channel-1 current track and path.
        # 3) Reset paused flag and inform the user.
        self._stop_proc("_ps_proc1")
        self.current_track1 = None
        self.current_path1 = None
        self.is_paused1 = False
        print("Stopped channel 1.")

    def next1(self):
        # 1) Ensure channel 1 has a current track within the configured list.
        # 2) Compute the next track index (wrap-around).
        # 3) Play the next track on channel 1.
        if not self.track_names or self.current_track1 not in self.track_names:
            print("No current track on channel 1 to advance from.")
            return
        idx = self.track_names.index(self.current_track1)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play1(next_name)

    def prev1(self):
        # 1) Ensure channel 1 has a current track within the configured list.
        # 2) Compute the previous track index (wrap-around).
        # 3) Play the previous track on channel 1.
        if not self.track_names or self.current_track1 not in self.track_names:
            print("No current track on channel 1 to go back from.")
            return
        idx = self.track_names.index(self.current_track1)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play1(prev_name)

    # --- Channel 2 ---
    def play2(self, name):
        # 1) Validate track name exists.
        # 2) Ensure file exists and is WAV.
        # 3) Stop any existing channel-2 process.
        # 4) Launch looping playback for channel 2.
        # 5) Save channel-2 state and inform the user.
        if name not in self.tracks:
            print(f"Track '{name}' not configured.")
            return
        path = self.tracks[name]
        if not os.path.exists(path):
            print(f"File not found for '{name}': {path}")
            return
        if not self._is_wav(path):
            print("Only WAV supported:", path)
            return
        self._stop_proc("_ps_proc2")
        proc = self._launch_ps_loop(path, "2")
        if proc:
            self._ps_proc2 = proc
            self.current_track2 = name
            self.current_path2 = path
            self.is_paused2 = False
            print(f"Playing track2: {name}")

    def pause2(self):
        # 1) Confirm channel 2 is playing.
        # 2) Stop the process.
        # 3) Mark channel 2 as paused.
        if not self.current_track2:
            print("Nothing is playing on channel 2.")
            return
        self._stop_proc("_ps_proc2")
        self.is_paused2 = True
        print("Paused channel 2.")

    def resume2(self):
        # 1) Confirm a paused track exists for channel 2.
        # 2) Confirm the file path exists.
        # 3) Clear paused flag and restart the same track.
        # 4) Inform the user.
        if not self.current_track2 or not self.is_paused2:
            print("Nothing to resume on channel 2.")
            return
        if not self.current_path2 or not os.path.exists(self.current_path2):
            print("Cannot resume channel 2: file missing.")
            return
        self.is_paused2 = False
        self.play2(self.current_track2)
        print("Resumed channel 2.")

    def stop2(self):
        # 1) Stop active channel-2 process if any.
        # 2) Clear channel-2 state and inform the user.
        self._stop_proc("_ps_proc2")
        self.current_track2 = None
        self.current_path2 = None
        self.is_paused2 = False
        print("Stopped channel 2.")

    def next2(self):
        # 1) Confirm there is a current track for channel 2.
        # 2) Move to the next track by index with wrap-around.
        # 3) Play the next track.
        if not self.track_names or self.current_track2 not in self.track_names:
            print("No current track on channel 2 to advance from.")
            return
        idx = self.track_names.index(self.current_track2)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play2(next_name)

    def prev2(self):
        # 1) Confirm there is a current track for channel 2.
        # 2) Move to the previous track by index with wrap-around.
        # 3) Play the previous track.
        if not self.track_names or self.current_track2 not in self.track_names:
            print("No current track on channel 2 to go back from.")
            return
        idx = self.track_names.index(self.current_track2)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play2(prev_name)

    # --- Channel 3 ---
    def play3(self, name):
        # 1) Validate track name exists.
        # 2) Ensure file exists and is WAV.
        # 3) Stop any existing channel-3 process.
        # 4) Launch looping playback for channel 3.
        # 5) Save channel-3 state and inform the user.
        if name not in self.tracks:
            print(f"Track '{name}' not configured.")
            return
        path = self.tracks[name]
        if not os.path.exists(path):
            print(f"File not found for '{name}': {path}")
            return
        if not self._is_wav(path):
            print("Only WAV supported:", path)
            return
        self._stop_proc("_ps_proc3")
        proc = self._launch_ps_loop(path, "3")
        if proc:
            self._ps_proc3 = proc
            self.current_track3 = name
            self.current_path3 = path
            self.is_paused3 = False
            print(f"Playing track3: {name}")

    def pause3(self):
        # 1) Confirm channel 3 is playing.
        # 2) Stop process and mark paused.
        if not self.current_track3:
            print("Nothing is playing on channel 3.")
            return
        self._stop_proc("_ps_proc3")
        self.is_paused3 = True
        print("Paused channel 3.")

    def resume3(self):
        # 1) Confirm a paused track exists for channel 3.
        # 2) Confirm the file path exists.
        # 3) Clear paused flag and restart the same track.
        # 4) Inform the user.
        if not self.current_track3 or not self.is_paused3:
            print("Nothing to resume on channel 3.")
            return
        if not self.current_path3 or not os.path.exists(self.current_path3):
            print("Cannot resume channel 3: file missing.")
            return
        self.is_paused3 = False
        self.play3(self.current_track3)
        print("Resumed channel 3.")

    def stop3(self):
        # 1) Stop active channel-3 process if any.
        # 2) Clear channel-3 state and inform the user.
        self._stop_proc("_ps_proc3")
        self.current_track3 = None
        self.current_path3 = None
        self.is_paused3 = False
        print("Stopped channel 3.")

    def next3(self):
        # 1) Confirm there is a current track for channel 3.
        # 2) Move to the next track with wrap-around.
        # 3) Play the next track.
        if not self.track_names or self.current_track3 not in self.track_names:
            print("No current track on channel 3 to advance from.")
            return
        idx = self.track_names.index(self.current_track3)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play3(next_name)

    def prev3(self):
        # 1) Confirm there is a current track for channel 3.
        # 2) Move to the previous track with wrap-around.
        # 3) Play the previous track.
        if not self.track_names or self.current_track3 not in self.track_names:
            print("No current track on channel 3 to go back from.")
            return
        idx = self.track_names.index(self.current_track3)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play3(prev_name)

    # --- Utility methods ---
    def list_tracks(self):
        # 1) If no tracks are configured, inform the user and exit.
        # 2) Otherwise, loop through track names with an index and print name -> path for each.
        if not self.track_names:
            print("No tracks configured.")
            return
        for i, name in enumerate(self.track_names, start=1):
            print(f"{i}. {name} -> {self.tracks.get(name)}")

    def status(self):
        # 1) Print a header for readability.
        # 2) For each channel (main, 1, 2, 3), print:
        #    a) the current track name or 'stopped'
        #    b) append ' (paused)' if the channel is paused
        print("=== Channel Status ===")
        print(f"Main: {self.current_track or 'stopped'}{' (paused)' if self.is_paused else ''}")
        print(f"Channel1: {self.current_track1 or 'stopped'}{' (paused)' if self.is_paused1 else ''}")
        print(f"Channel2: {self.current_track2 or 'stopped'}{' (paused)' if self.is_paused2 else ''}")
        print(f"Channel3: {self.current_track3 or 'stopped'}{' (paused)' if self.is_paused3 else ''}")

    def stop_all(self):
        # 1) Call stop() for each channel (main, 1, 2, 3).
        # 2) Inform the user that all channels were stopped.
        self.stop()
        self.stop1()
        self.stop2()
        self.stop3()
        print("Stopped all channels.")

    def get_track_index(self):
        # 1) If a current track exists and is in the track list, return its index.
        # 2) Otherwise, return None to indicate no active index.
        if self.current_track and self.current_track in self.track_names:
            return self.track_names.index(self.current_track)
        return None

    def set_track_by_index(self, index):
        # 1) Check that index is within valid range (0 to len-1).
        # 2) If valid, get the track name at that index and play it on the main channel.
        # 3) If invalid, inform the user.
        if 0 <= index < len(self.track_names):
            name = self.track_names[index]
            self.play(name)
        else:
            print("Invalid track index.")
