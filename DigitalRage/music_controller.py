# BB 1st music library implementation
import winsound
import msvcrt

class MusicController:
    def __init__(self, tracks):
        self.tracks = tracks
        self.track_names = list(tracks.keys())
        self.current_track = None

    def play_track(self, name):
        self.current_track = name
        winsound.PlaySound(self.tracks[name],
                           winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        print(f"Playing {self.current_track}...")

    def pause(self):
        winsound.PlaySound(None, winsound.SND_PURGE)
        print("Playback paused.")

    def stop(self):
        winsound.PlaySound(None, winsound.SND_PURGE)
        print("Playback stopped. Goodbye!")

    def track_mode(self):
        print("Track mode: press = for next, - for previous, Backspace to exit")
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                try:
                    char = key.decode('utf-8')
                except UnicodeDecodeError:
                    char = ''

                if char == '=':  # next track
                    self._next_track()
                elif char == '-':  # previous track
                    self._prev_track()
                elif key == b'\x08':  # Backspace
                    print("Exiting track mode.")
                    break

    def _next_track(self):
        if self.current_track:
            idx = self.track_names.index(self.current_track)
            new_idx = (idx + 1) % len(self.track_names)
            self.play_track(self.track_names[new_idx])
        else:
            self.play_track(self.track_names[0])

    def _prev_track(self):
        if self.current_track:
            idx = self.track_names.index(self.current_track)
            new_idx = (idx - 1) % len(self.track_names)
            self.play_track(self.track_names[new_idx])
        else:
            self.play_track(self.track_names[0])
