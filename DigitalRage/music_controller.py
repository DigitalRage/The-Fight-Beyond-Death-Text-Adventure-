# music_controller.py
import os
import subprocess
import time
import shutil

class MusicController:
    # --- Basic Checks ---
    def __init__(self, tracks):
        self.tracks = {name: os.path.abspath(path) for name, path in (tracks or {}).items()}
        self.track_names = list(self.tracks.keys())

        # main channel
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        self._ps_proc = None

        # channel 1
        self.current_track1 = None
        self.current_path1 = None
        self.is_paused1 = False
        self._ps_proc1 = None

        # channel 2
        self.current_track2 = None
        self.current_path2 = None
        self.is_paused2 = False
        self._ps_proc2 = None


        
        # channel 3
        self.current_track3 = None
        self.current_path3 = None
        self.is_paused3 = False
        self._ps_proc3 = None


        self._powershell = shutil.which("powershell") or shutil.which("powershell.exe")

    def _is_wav(self, path):
        return isinstance(path, str) and path.lower().endswith('.wav')

    def _find_by_basename(self, basename):
        for i in (os.path.dirname(__file__), os.getcwd()):
            try:
                for item in os.listdir(i):
                    if item.lower() == basename.lower():
                        return os.path.join(i, item)
            except Exception:
                continue
        return None

    def _stop_proc(self, proc_attr):
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
        if not self.current_track:
            print("Nothing is playing.")
            return
        self._stop_proc("_ps_proc")
        self.is_paused = True
        print("Paused main channel.")

    def resume(self):
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
        self._stop_proc("_ps_proc")
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        print("Stopped main channel.")

    def next_track(self):
        if not self.track_names or self.current_track not in self.track_names:
            print("No current track to advance from.")
            return
        idx = self.track_names.index(self.current_track)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play(next_name)

    def prev_track(self):
        if not self.track_names or self.current_track not in self.track_names:
            print("No current track to go back from.")
            return
        idx = self.track_names.index(self.current_track)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play(prev_name)

    # --- Channel 1 ---
    def play1(self, name):
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
        if not self.current_track1:
            print("Nothing is playing on channel 1.")
            return
        self._stop_proc("_ps_proc1")
        self.is_paused1 = True
        print("Paused channel 1.")

    def resume1(self):
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
        self._stop_proc("_ps_proc1")
        self.current_track1 = None
        self.current_path1 = None
        self.is_paused1 = False
        print("Stopped channel 1.")

    def next1(self):
        if not self.track_names or self.current_track1 not in self.track_names:
            print("No current track on channel 1 to advance from.")
            return
        idx = self.track_names.index(self.current_track1)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play1(next_name)

    def prev1(self):
        if not self.track_names or self.current_track1 not in self.track_names:
            print("No current track on channel 1 to go back from.")
            return
        idx = self.track_names.index(self.current_track1)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play1(prev_name)

    # --- Channel 2 ---
    def play2(self, name):
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
        if not self.current_track2:
            print("Nothing is playing on channel 2.")
            return
        self._stop_proc("_ps_proc2")
        self.is_paused2 = True
        print("Paused channel 2.")

    def resume2(self):
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
        self._stop_proc("_ps_proc2")
        self.current_track2 = None
        self.current_path2 = None
        self.is_paused2 = False
        print("Stopped channel 2.")

    def next2(self):
        if not self.track_names or self.current_track2 not in self.track_names:
            print("No current track on channel 2 to advance from.")
            return
        idx = self.track_names.index(self.current_track2)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play2(next_name)

    def prev2(self):
        if not self.track_names or self.current_track2 not in self.track_names:
            print("No current track on channel 2 to go back from.")
            return
        idx = self.track_names.index(self.current_track2)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play2(prev_name)



    # --- Channel 3 ---
    def play3(self, name):
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
        if not self.current_track3:
            print("Nothing is playing on channel 3.")
            return
        self._stop_proc("_ps_proc3")
        self.is_paused3 = True
        print("Paused channel 3.")

    def resume3(self):
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
        self._stop_proc("_ps_proc3")
        self.current_track3 = None
        self.current_path3 = None
        self.is_paused3 = False
        print("Stopped channel 3.")

    def next3(self):
        if not self.track_names or self.current_track3 not in self.track_names:
            print("No current track on channel 3 to advance from.")
            return
        idx = self.track_names.index(self.current_track3)
        next_name = self.track_names[(idx + 1) % len(self.track_names)]
        self.play3(next_name)

    def prev3(self):
        if not self.track_names or self.current_track3 not in self.track_names:
            print("No current track on channel 3 to go back from.")
            return
        idx = self.track_names.index(self.current_track3)
        prev_name = self.track_names[(idx - 1) % len(self.track_names)]
        self.play3(prev_name)


    # --- Utility Methods ---
    def list_tracks(self):
        if not self.track_names:
            print("No tracks configured.")
            return
        for i, name in enumerate(self.track_names, start=1):
            print(f"{i}. {name} -> {self.tracks.get(name)}")
            
    def status(self):
        print("=== Channel Status ===")
        print(f"Main: {self.current_track or 'stopped'}{' (paused)' if self.is_paused else ''}")
        print(f"Channel1: {self.current_track1 or 'stopped'}{' (paused)' if self.is_paused1 else ''}")
        print(f"Channel2: {self.current_track2 or 'stopped'}{' (paused)' if self.is_paused2 else ''}")
        print(f"Channel3: {self.current_track3 or 'stopped'}{' (paused)' if self.is_paused3 else ''}")

    def stop_all(self):
        #Stop playback on all channels.
        self.stop()
        self.stop1()
        self.stop2()
        self.stop3()
        print("Stopped all channels.")

    def get_track_index(self):
        #Return index of current track in track_names, or None if not playing.
        if self.current_track and self.current_track in self.track_names:
            return self.track_names.index(self.current_track)
        return None

    def set_track_by_index(self, index):
        #Play track by index if valid.
        if 0 <= index < len(self.track_names):
            name = self.track_names[index]
            self.play(name)
        else:
            print("Invalid track index.")
