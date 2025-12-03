import os
from music_controller import MusicController

this_dir = os.path.dirname(os.path.abspath(__file__))

def locate_music_file(name, base_dir):
    p = os.path.join(base_dir, name)
    if os.path.exists(p):
        return os.path.abspath(p)
    target = name.lower()
    for f in os.listdir(base_dir):
        if f.lower() == target:
            return os.path.join(base_dir, f)
    base_no_ext = os.path.splitext(name)[0].lower()
    for f in os.listdir(base_dir):
        if os.path.splitext(f)[0].lower() == base_no_ext:
            return os.path.join(base_dir, f)
    return None

requested = {
    "battle": "Organization Battle.wav",
    "town": "Twilight Town.wav",
    "destiny": "Destiny Islands.wav"
}

tracks = {}
for key, fname in requested.items():
    found = locate_music_file(fname, this_dir)
    if found:
        tracks[key] = found
        print(f"Found {key}: {found}")
    else:
        print(f"Missing {key}: tried '{fname}' in {this_dir}")

controller = MusicController(tracks)
controller.list_tracks()

print("Commands: play <name>, pause, resume, stop, list, next, prev, quit")
while True:
    try:
        cmd = input("> ").strip().split(maxsplit=1)
    except (EOFError, KeyboardInterrupt):
        break
    if not cmd:
        continue
    op = cmd[0].lower()
    arg = cmd[1].strip() if len(cmd) > 1 else None
    if op == "play" and arg:
        controller.play(arg)
    elif op == "pause":
        controller.pause()
    elif op == "resume":
        controller.resume()
    elif op == "stop":
        controller.stop()
    elif op == "list":
        controller.list_tracks()
    elif op == "quit":
        controller.stop()
        break
    elif op == "next":
        controller.next_track()
    elif op == "prev":
        controller.previous_track()
    else:
        print("Unknown command.")