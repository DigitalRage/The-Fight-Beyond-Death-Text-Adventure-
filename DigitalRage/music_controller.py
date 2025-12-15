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

    def _is_supported(self, path):
        # 1) Confirm the input is a string.
        # 2) Check for supported audio extensions: .wav and .mp3 (case-insensitive).
        if not isinstance(path, str):
            return False
        lower = path.lower()
        return lower.endswith('.wav') or lower.endswith('.mp3')

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
        # If WAV: continue using System.Media.SoundPlayer for looping
        if path.lower().endswith('.wav'):
            ps_script = f"& {{ $p = New-Object System.Media.SoundPlayer '{safe}'; $p.Load(); $p.PlayLooping(); Start-Sleep -Seconds 999999 }}"
        else:
            # For MP3 and other supported formats, use WPF MediaPlayer.
            # Attach MediaEnded event to loop automatically.
            # Note: we use doubled braces to escape literal braces in f-strings
            ps_script = (
                "& { Add-Type -AssemblyName presentationCore; $mm = New-Object System.Windows.Media.MediaPlayer; "
                f"$uri = New-Object System.Uri('{safe}'); $mm.Open($uri); $mm.add_MediaEnded({{ $mm.Position = [TimeSpan]::Zero; $mm.Play() }}); $mm.Play(); "
                "while ($true) { Start-Sleep -Seconds 10 } }"
            )
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

    # --- Generic slot helpers (reduce duplication across channels) ---
    def _slot_attrs(self, slot):
        # Return attribute names for given slot identifier ('main' or '1'/'2'/'3')
        if slot == 'main':
            return {
                'proc_attr': '_ps_proc', 'track_attr': 'current_track', 'path_attr': 'current_path', 'paused_attr': 'is_paused'
            }
        else:
            return {
                'proc_attr': f"_ps_proc{slot}", 'track_attr': f"current_track{slot}", 'path_attr': f"current_path{slot}", 'paused_attr': f"is_paused{slot}"
            }

    def _play_slot(self, slot, name):
        attrs = self._slot_attrs(slot)
        track_attr = attrs['track_attr']
        path_attr = attrs['path_attr']
        proc_attr = attrs['proc_attr']
        paused_attr = attrs['paused_attr']

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
        if not self._is_supported(path):
            print("Only WAV/MP3 supported:", path)
            return
        # stop existing
        self._stop_proc(proc_attr)
        proc = self._launch_ps_loop(path, slot)
        if proc:
            setattr(self, proc_attr, proc)
            setattr(self, track_attr, name)
            setattr(self, path_attr, path)
            setattr(self, paused_attr, False)
            print(f"Playing track: {name}")

    def _stop_slot(self, slot):
        attrs = self._slot_attrs(slot)
        proc_attr = attrs['proc_attr']
        track_attr = attrs['track_attr']
        path_attr = attrs['path_attr']
        paused_attr = attrs['paused_attr']
        self._stop_proc(proc_attr)
        setattr(self, track_attr, None)
        setattr(self, path_attr, None)
        setattr(self, paused_attr, False)
        print(f"Stopped channel {slot}.")

    def _pause_slot(self, slot):
        attrs = self._slot_attrs(slot)
        track_attr = attrs['track_attr']
        paused_attr = attrs['paused_attr']
        if not getattr(self, track_attr):
            print(f"Nothing is playing on channel {slot}.")
            return
        self._stop_proc(attrs['proc_attr'])
        setattr(self, paused_attr, True)
        print(f"Paused channel {slot}.")

    def _resume_slot(self, slot):
        attrs = self._slot_attrs(slot)
        track_attr = attrs['track_attr']
        paused_attr = attrs['paused_attr']
        path_attr = attrs['path_attr']
        if not getattr(self, track_attr) or not getattr(self, paused_attr):
            print(f"Nothing to resume on channel {slot}.")
            return
        if not getattr(self, path_attr) or not os.path.exists(getattr(self, path_attr)):
            print(f"Cannot resume channel {slot}: file missing.")
            return
        setattr(self, paused_attr, False)
        self._play_slot(slot, getattr(self, track_attr))

    def _next_slot(self, slot):
        attrs = self._slot_attrs(slot)
        track_attr = attrs['track_attr']
        cur = getattr(self, track_attr)
        if not self.track_names or cur not in self.track_names:
            print(f"No current track on channel {slot} to advance from.")
            return
        idx = self.track_names.index(cur)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self._play_slot(slot, next_name)

    def _prev_slot(self, slot):
        attrs = self._slot_attrs(slot)
        track_attr = attrs['track_attr']
        cur = getattr(self, track_attr)
        if not self.track_names or cur not in self.track_names:
            print(f"No current track on channel {slot} to go back from.")
            return
        idx = self.track_names.index(cur)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self._play_slot(slot, prev_name)

    # --- Main channel ---
    def play(self, name):
        self._play_slot('main', name)

    def pause(self):
        self._pause_slot('main')

    def resume(self):
        self._resume_slot('main')

    def stop(self):
        self._stop_slot('main')

    def next_track(self):
        self._next_slot('main')

    def prev_track(self):
        self._prev_slot('main')

    # --- Channel 1 ---
    def play1(self, name):
        self._play_slot('1', name)

    def pause1(self):
        self._pause_slot('1')

    def resume1(self):
        self._resume_slot('1')

    def stop1(self):
        self._stop_slot('1')

    def next1(self):
        self._next_slot('1')

    def prev1(self):
        self._prev_slot('1')

    # --- Channel 2 ---
    def play2(self, name):
        self._play_slot('2', name)

    def pause2(self):
        self._pause_slot('2')

    def resume2(self):
        self._resume_slot('2')

    def stop2(self):
        self._stop_slot('2')

    def next2(self):
        self._next_slot('2')

    def prev2(self):
        self._prev_slot('2')

    # --- Channel 3 ---
    def play3(self, name):
        self._play_slot('3', name)

    def pause3(self):
        self._pause_slot('3')

    def resume3(self):
        self._resume_slot('3')

    def stop3(self):
        self._stop_slot('3')

    def next3(self):
        self._next_slot('3')

    def prev3(self):
        self._prev_slot('3')

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
