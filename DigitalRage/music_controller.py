#music_controller.py
import os
import winsound
import subprocess
import time

class MusicController:
    def __init__(self, tracks):
        # tracks: dict name->path (abs or relative). store absolute paths.
        self.tracks = {name: os.path.abspath(path) for name, path in (tracks or {}).items()}
        self.track_names = list(self.tracks.keys())
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        self._ps_proc = None

    def _is_wav(self, path):
        return isinstance(path, str) and path.lower().endswith('.wav')

    def _find_by_basename(self, basename):
        # search script dir and cwd (case-insensitive)
        for i in (os.path.dirname(__file__), os.getcwd()):
            try:
                for item in os.listdir(i):
                    if item.lower() == basename.lower():
                        return os.path.join(i, item)
            except Exception:
                continue
        return None

    def _stop_ps(self):
        if self._ps_proc:
            try:
                self._ps_proc.terminate()
                time.sleep(0.05)
                if self._ps_proc.poll() is None:
                    self._ps_proc.kill()
            except Exception:
                pass
            self._ps_proc = None

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
            print("Only WAV playback supported by this controller:", path)
            return

        # stop any current playback
        self.stop()

        # try winsound async loop
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            self.current_track = name
            self.current_path = path
            self.is_paused = False
            print(f"Playing (winsound) {name}")
            return
        except Exception as stuff:
            print("winsound failed:", stuff)

        # fallback: PowerShell SoundPlayer loop
        try:
            safe = path.replace("'", "''")
            ps_cmd = f"$p=New-Object System.Media.SoundPlayer '{safe}'; $p.PlayLooping(); Start-Sleep -Seconds 999999"
            self._ps_proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.current_track = name
            self.current_path = path
            self.is_paused = False
            print(f"Playing (powershell) {name}")
        except Exception as stuff:
            print("PowerShell fallback failed:", stuff)

    def pause(self):
        if not self.current_track:
            print("Nothing is playing.")
            return
        # implement pause as stop but remember state for resume
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self._stop_ps()
        self.is_paused = True
        print("Paused.")

    def resume(self):
        if not self.current_track or not self.is_paused:
            print("Nothing to resume.")
            return
        if not self.current_path or not os.path.exists(self.current_path):
            print("Cannot resume: file missing.")
            return
        self.is_paused = False
        self.play(self.current_track)
        print("Resumed.")

    def stop(self):
        # stop all playback
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self._stop_ps()
        self.current_track = None
        self.current_path = None
        self.is_paused = False
        print("Stopped.")

    def list_tracks(self):
        if not self.track_names:
            print("No tracks configured.")
            return
        for i, name in enumerate(self.track_names, start=1):
            print(f"{i}. {name} -> {self.tracks.get(name)}")

    
    def next_track(self):
        if not self.track_names:
            print("No tracks configured.")
            return
        if self.current_track not in self.track_names:
            print("No current track to advance from.")
            return
        current_index = self.track_names.index(self.current_track)
        next_index = (current_index + 1) % len(self.track_names)
        next_name = self.track_names[next_index]
        self.play(next_name)

    def prev_track(self):
        if not self.track_names:
            print("No tracks configured.")
            return
        if self.current_track not in self.track_names:
            print("No current track to go back from.")
            return
        current_index = self.track_names.index(self.current_track)
        prev_index = (current_index - 1) % len(self.track_names)
        prev_name = self.track_names[prev_index]
        self.play(prev_name)
