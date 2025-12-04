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

print("Commands:")
print("  play <name>, pause, resume, stop, next, prev, status")
print("  play1 <name>, pause1, resume1, stop1, next1, prev1")
print("  play2 <name>, pause2, resume2, stop2, next2, prev2")
print("  list, status, quit")

def status():
    print("=== Channel Status ===")
    print(f"Main:    {controller.current_track or 'stopped'}"
          f"{' (paused)' if controller.is_paused else ''}")
    print(f"Channel1:{controller.current_track1 or 'stopped'}"
          f"{' (paused)' if controller.is_paused1 else ''}")
    print(f"Channel2:{controller.current_track2 or 'stopped'}"
          f"{' (paused)' if controller.is_paused2 else ''}")

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
    elif op == "next":
        controller.next_track()
    elif op == "prev":
        controller.prev_track()

    elif op == "play1" and arg:
        controller.play1(arg)
    elif op == "pause1":
        controller.pause1()
    elif op == "resume1":
        controller.resume1()
    elif op == "stop1":
        controller.stop1()
    elif op == "next1":
        controller.next1()
    elif op == "prev1":
        controller.prev1()

    elif op == "play2" and arg:
        controller.play2(arg)
    elif op == "pause2":
        controller.pause2()
    elif op == "resume2":
        controller.resume2()
    elif op == "stop2":
        controller.stop2()
    elif op == "next2":
        controller.next2()
    elif op == "prev2":
        controller.prev2()

    elif op == "status": 
        controller.status()
    elif op == "list":
        controller.list_tracks()
    elif op == "status":
        controller.status()
    elif op == "quit":
        controller.stop()
        controller.stop1()
        controller.stop2()
        break
    else:
        print("Unknown command.")