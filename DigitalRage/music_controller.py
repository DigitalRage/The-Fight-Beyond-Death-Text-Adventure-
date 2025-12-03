import winsound
import msvcrt
import os

class MusicController:
    def __init__(self, tracks):
        # tracks: dict name->absolute-or-relative-path
        self.tracks = {k: os.path.abspath(v) for k, v in tracks.items()}
        self.track_names = list(self.tracks.keys())
        self.current_track = None
        self.current_path = None
        self.is_paused = False

    def _is_wav(self, path):
        return path.lower().endswith('.wav')

    def play_track(self, name):
        if name not in self.tracks:
            print(f"Track '{name}' not found.")
            return
        path = self.tracks[name]
        if not os.path.exists(path):
            print(f"File '{path}' does not exist.")
            return
        if not self._is_wav(path):
            print(f"winsound supports WAV only. File not played: {path}")
            return

        self.current_track = name
        self.current_path = path
        self.is_paused = False
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        print(f"Playing {self.current_track} -> {path}")

    def pause(self):
        if self.current_track and not self.is_paused:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.is_paused = True
            print("Playback paused.")
        else:
            print("No track is currently playing to pause.")

    def resume(self):
        if self.current_track and self.is_paused:
            if self.current_path and os.path.exists(self.current_path):
                winsound.PlaySound(self.current_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                self.is_paused = False
                print(f"Resumed {self.current_track}.")
            else:
                print("Cannot resume: file missing.")
        else:
            print("Nothing to resume.")

    def stop(self):
        if self.current_track:
            winsound.PlaySound(None, winsound.SND_PURGE)
            print("Playback stopped.")
            self.current_track = None
            self.current_path = None
            self.is_paused = False
        else:
            print("No track is currently playing.")

    def list_tracks(self):
        for i, name in enumerate(self.track_names):
            print(f"{i+1}. {name} -> {self.tracks[name]}")

    def track_mode(self):
        print("Track mode: '=' next, '-' prev, 'p' pause, 'r' resume, 's' stop, Backspace to exit")
        if not self.track_names:
            print("No tracks available.")
            return
        if self.current_track is None:
            self.play_track(self.track_names[0])
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                try:
                    ch = key.decode('utf-8')
                except Exception:
                    ch = ''
                if ch == '=':
                    self._next_track()
                elif ch == '-':
                    self._prev_track()
                elif ch.lower() == 'p':
                    self.pause()
                elif ch.lower() == 'r':
                    self.resume()
                elif ch.lower() == 's':
                    self.stop()
                elif key == b'\x08':  # Backspace
                    print("Exiting track mode.")
                    break

    def _next_track(self):
        if not self.track_names:
            return
        if self.current_track and self.current_track in self.track_names:
            idx = self.track_names.index(self.current_track)
            new_idx = (idx + 1) % len(self.track_names)
        else:
            new_idx = 0
        self.play_track(self.track_names[new_idx])

    def _prev_track(self):
        if not self.track_names:
            return
        if self.current_track and self.current_track in self.track_names:
            idx = self.track_names.index(self.current_track)
            new_idx = (idx - 1) % len(self.track_names)
        else:
            new_idx = 0
        self.play_track(self.track_names[new_idx])