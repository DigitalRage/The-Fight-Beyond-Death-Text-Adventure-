import os, winsound, msvcrt
from music_controller import MusicController
if __name__ == "__main__":
    # Define your tracks dictionary
    tracks = {
        "battle": "Organization Battle.wav",
        "town": "Twilight Town.wav",
        "destiny": "Destiny Islands.wav"
    }

    # Create the controller
    music = MusicController(tracks)

    # Example: play the "battle" track
    music.play_track("battle")