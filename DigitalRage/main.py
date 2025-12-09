# BB 1st Final Project, The Fight Beyond Death: Text Adventure

#SETUP
#- Import libraries: os, time, winsound, mscrt, save (My Save File), music controller (music playback)
import os
import time
import random
import msvcrt
import json
from music_controller import MusicController
from maps import map1

SAVE_FILE = "save.json"

# --- Helpers for resilient music API (work with controllers that expose play or play_track, next, next_track, etc.) ---
def _call(controller, *names, default=None):
    for n in names:
        if hasattr(controller, n):
            return getattr(controller, n)
    return default

def music_play(controller, name):
    fn = _call(controller, "play", "play_track")
    if fn:
        fn(name)

def music_pause(controller):
    fn = _call(controller, "pause")
    if fn:
        fn()

def music_resume(controller):
    fn = _call(controller, "resume")
    if fn:
        fn()

def music_stop(controller):
    fn = _call(controller, "stop")
    if fn:
        fn()

def music_next(controller):
    fn = _call(controller, "next_track", "next")
    if fn:
        fn()

def music_prev(controller):
    fn = _call(controller, "prev_track", "prev")
    if fn:
        fn()

def music_list(controller):
    fn = _call(controller, "list_tracks", "list")
    if fn:
        fn()

# --- Input (msvcrt) ---
def read_action():
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getch()
    if key == b'\xe0':  # special / arrow
        key2 = msvcrt.getch()
        return {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right'}.get(key2)
    mapping = {
        b'w': 'up', b's': 'down', b'a': 'left', b'd': 'right',
        b'p': 'pause', b'i': 'interact', b'=': 'next_track', b'-': 'prev_track',
        b' ': 'attack', b'j': 'dodge_left', b'l': 'dodge_right', b'k': 'dodge_down', b'u': 'dodge_up',
        b'1': 'use_item_1', b'2': 'use_item_2', b'3': 'use_item_3', b'm': 'open_menu'
    }
    return mapping.get(key, None)

# --- FS helpers ---
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

# --- Map / Tiles ---
def setup_tile(tiles, tile_id, x, y):
    tiles.append({'id': tile_id, 'x': x, 'y': y})
    return tiles

def get_tile_id(x, y, tiles):
    for t in tiles:
        if t['x'] == x and t['y'] == y:
            return t['id']
    return "empty"

def check_collision(x, y, tiles):
    return get_tile_id(x, y, tiles) not in ("wall", "blocked")

def render_map(map_data, player_x, player_y):
    #Render the map with player position overlaid.
    os.system("cls")
    if not map_data or len(map_data) == 0:
        print("[No map data]")
        return
    
    for row_idx, row in enumerate(map_data):
        line = ""
        for col_idx, char in enumerate(row):
            if row_idx == player_y and col_idx == player_x:
                line += "⇩"  # Player marker
            else:
                line += char
        print(line)
    print(f"\n[Player: {player_x}, {player_y}] WASD/arrows=move, i=interact, p=pause, m=menu")

# --- Save/Load ---
def save_game(player_stats, inventory, game_mode, tiles, controller, save_file=SAVE_FILE):
    data = {
        "player_stats": player_stats,
        "inventory": inventory,
        "game_mode": game_mode,
        "tiles": tiles,
        "current_track": getattr(controller, "current_track", None)
    }
    try:
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Saved.")
    except Exception as e:
        print("Save error:", e)

def load_game(controller, save_file=SAVE_FILE):
    try:
        with open(save_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        player_stats = data.get("player_stats", {})
        inventory = data.get("inventory", [])
        game_mode = data.get("game_mode", "field")
        tiles = data.get("tiles", [])
        track = data.get("current_track")
        if track:
            music_play(controller, track)
        print("Loaded.")
        return player_stats, inventory, game_mode, tiles
    except FileNotFoundError:
        print("No save file.")
        return None, None, None, None
    except Exception as e:
        print("Load error:", e)
        return None, None, None, None

# --- UI / menus ---
def mp3_player_menu(controller):
    names = list(controller.tracks.keys())
    if not names:
        print("No tracks.")
        return
    idx = 0
    while True:
        os.system("cls")
        print("=== MP3 Player ===")
        for i, n in enumerate(names):
            print(f"{'> ' if i==idx else '  '}{n}")
        print("Enter = play, Esc = exit, arrows to move")
        k = msvcrt.getch()
        if k == b'\xe0':
            k2 = msvcrt.getch()
            if k2 == b'H': idx = (idx-1) % len(names)
            elif k2 == b'P': idx = (idx+1) % len(names)
        elif k == b'\r':
            music_play(controller, names[idx])
        elif k == b'\x1b':
            break

def start_menu():
    opts = ["Start New Game", "Load Saved Game", "MP3 Player", "Quit"]
    sel = 0
    while True:
        os.system("cls")
        print("=== The Fight Beyond Death ===")
        for i,o in enumerate(opts):
            print(f"{'> ' if i==sel else '  '}{o}")
        k = msvcrt.getch()
        if k == b'\xe0':
            k2 = msvcrt.getch()
            if k2 == b'H': sel = (sel-1) % len(opts)
            elif k2 == b'P': sel = (sel+1) % len(opts)
        elif k == b'\r':
            return sel



# --- Battle / rendering frames ---
def render_battle(player_stats, enemies, frame_index, player_sprite):
    os.system("cls")
    print("=== BATTLE ===")
    # show player frame
    player_frame = player_sprite.get('frames', [player_sprite.get('walk')])[frame_index % max(1, len(player_sprite.get('frames', [player_sprite.get('walk')])))]
    print(f"Player @ ({player_stats['x']},{player_stats['y']}): {player_frame}  HP:{player_stats['HP']}")
    print()
    print("Enemies:")
    for e in enemies:
        # enemy uses walk sprite placeholder if not provided
        e_sprite = e.get('sprite', e.get('walk', player_sprite.get('walk', '◈')))
        # if sprite has frames list, show a frame, else show single char
        if isinstance(e_sprite, list):
            s = e_sprite[frame_index % len(e_sprite)]
        else:
            s = e_sprite
        print(f" - {e['name']} ({e['x']},{e['y']}): {s} HP:{e['HP']}")

# --- Modes ---
def field_mode(player_stats, inventory, tiles, controller, map_data):
    """Field mode: explore map, encounter battles, interact with tiles."""
    # auto-music
    if 'town' in controller.tracks and getattr(controller, "current_track", None) != 'town':
        music_play(controller, 'town')
    
    steps = player_stats.get('steps', 0)
    last_x, last_y = player_stats['x'], player_stats['y']
    render_map(map_data, last_x, last_y)  # Initial render
    
    while True:
        action = read_action()
        if action is None:
            time.sleep(0.03)
            continue
        if action == 'pause':
            print("Paused. press p to resume.")
            while True:
                if read_action() == 'pause':
                    print("Resumed.")
                    render_map(map_data, player_stats['x'], player_stats['y'])
                    break
                time.sleep(0.02)
            continue
        if action in ('up','down','left','right'):
            dx = {'left':-1,'right':1,'up':0,'down':0}[action]
            dy = {'up':-1,'down':1,'left':0,'right':0}[action]
            nx, ny = player_stats['x']+dx, player_stats['y']+dy
            if check_collision(nx, ny, tiles):
                player_stats['x'], player_stats['y'] = nx, ny
                steps += 1
                player_stats['steps'] = steps
                # Only render if position changed
                render_map(map_data, player_stats['x'], player_stats['y'])
                if random.random() < 0.05:
                    if 'battle' in controller.tracks:
                        music_play(controller, 'battle')
                    return player_stats, inventory, tiles, "battle"
        elif action == 'interact':
            tid = get_tile_id(player_stats['x'], player_stats['y'], tiles)
            print("Interacted with:", tid)
            time.sleep(0.6)
        elif action == 'open_menu':
            in_game_menu(player_stats, inventory, controller)
            # Re-render after menu closes
            render_map(map_data, player_stats['x'], player_stats['y'])
        elif action == 'next_track':
            music_next(controller)
        elif action == 'prev_track':
            music_prev(controller)

def in_game_menu(player_stats, inventory, controller):
    opts = ["Resume", "Items", "Save", "Load", "MP3 Player", "Status", "Quit to Title"]
    sel = 0
    while True:
        os.system("cls")
        print("=== Menu ===")
        for i,o in enumerate(opts):
            print(f"{'> ' if i==sel else '  '}{o}")
        k = msvcrt.getch()
        if k == b'\xe0':
            k2 = msvcrt.getch()
            if k2 == b'H': sel = (sel-1) % len(opts)
            elif k2 == b'P': sel = (sel+1) % len(opts)
        elif k == b'\r':
            ch = opts[sel]
            if ch == "Resume":
                return
            if ch == "Items":
                print("Inventory:", inventory or "empty"); input("Enter to continue")
            if ch == "Save":
                save_game(player_stats, inventory, "field", [], controller); input("Enter")
            if ch == "Load":
                p,inv,gm,tl = load_game(controller); input("Enter")
            if ch == "MP3 Player":
                mp3_player_menu(controller)
            if ch == "Status":
                print(player_stats); input("Enter")
            if ch == "Quit to Title":
                music_stop(controller)
                raise SystemExit("ReturnToTitle")

def battle_mode(player_stats, inventory, controller):
    # spawn a simple enemy; add walk sprite placeholder
    enemies = [{
        'name': 'Shadow',
        'HP': 30,
        'attack': 8,
        'defence': 3,
        'speed': 1,
        'x': player_stats['x'] + 2,
        'y': player_stats['y'],
        'walk': ['◈','◇'],   # placeholder frames
        'sprite': ['◈','◇'],
        'state': 'idle', 
        'exp': 20,
        'drop': 'potion'
    }]
    # player sprites - simple frames for walk
    player_sprite = {'walk': ['⇩','↧'], 'frames':['⇩','↧']}

    if 'battle' in controller.tracks:
        music_play(controller, 'battle')

    frame = 0
    last_update = time.time()
    while True:
        # update animation frame every 0.3s
        now = time.time()
        if now - last_update > 0.3:
            frame += 1
            last_update = now

        render_battle(player_stats, enemies, frame, player_sprite)

        action = read_action()
        if action is None:
            # simulate enemies moving toward player slowly
            for e in enemies:
                if e['x'] > player_stats['x']: e['x'] -= e['speed']
                elif e['x'] < player_stats['x']: e['x'] += e['speed']
                if e['y'] > player_stats['y']: e['y'] -= e['speed']
                elif e['y'] < player_stats['y']: e['y'] += e['speed']
            # check enemy attacks
            for e in enemies:
                dist = abs(e['x']-player_stats['x']) + abs(e['y']-player_stats['y'])
                if dist <= 1 and random.random() < 0.15:
                    dmg = max(0, e['attack'] - player_stats.get('defence',0))
                    player_stats['HP'] -= dmg
                    print(f"{e['name']} hits you for {dmg}!"); time.sleep(0.6)
            # check end conditions
            if all(e['HP'] <= 0 for e in enemies):
                print("You won the battle!")
                if 'town' in controller.tracks:
                    music_play(controller, 'town')
                return player_stats, inventory, "field"
            if player_stats['HP'] <= 0:
                print("You died...")
                music_stop(controller)
                return player_stats, inventory, "end game"
            time.sleep(0.08)
            continue

        if action == 'pause':
            print("Battle paused. press p to resume.")
            while True:
                if read_action() == 'pause':
                    break
                time.sleep(0.02)
            continue
        if action in ('up','down','left','right'):
            dx = {'left':-1,'right':1,'up':0,'down':0}[action]
            dy = {'up':-1,'down':1,'left':0,'right':0}[action]
            player_stats['x'] += dx; player_stats['y'] += dy
        elif action == 'attack':
            # attack nearest alive enemy
            alive = [e for e in enemies if e['HP'] > 0]
            if alive:
                target = min(alive, key=lambda e: abs(e['x']-player_stats['x'])+abs(e['y']-player_stats['y']))
                dmg = max(0, player_stats.get('attack',10) - target.get('defence',0))
                target['HP'] -= dmg
                print(f"You hit {target['name']} for {dmg}!"); time.sleep(0.5)
        elif action == 'open_menu':
            in_game_menu(player_stats, inventory, controller)
        elif action == 'next_track':
            music_next(controller)
        elif action == 'prev_track':
            music_prev(controller)

# --- Main ---
def main():
    # Use map from maps.py
    map_data = map1
    items = {
        'potion': {'heal': 100},
        'hi-potion': {'heal': 500},
        'x-potion': {'heal': 9999},
        'ether': {'mana': 50},
        'hi-ether': {'mana': 200},
        'elixir': {'heal': 9999, 'mana': 9999}
    }
    # initial player (started in middle-ish area)
    player_stats = {'x': 40, 'y': 30, 'HP': 120, 'attack': 12, 'defence': 5, 'Level':1, 'steps':0, 'exp':0, 'munny':0, 'items':[]}
    tiles = []
    # place tiles from map chars
    for y, row in enumerate(map_data):
        for x, ch in enumerate(row):
            if ch == '#':
                setup_tile(tiles, "wall", x, y)
            elif ch == 'C':
                setup_tile(tiles, "chest", x, y)
            elif ch == 'N':
                setup_tile(tiles, "NPC", x, y)
            elif ch == 'D':
                setup_tile(tiles, "door", x, y)

    # discover music files in same folder as script
    this_dir = os.path.dirname(os.path.abspath(__file__))
    requested = {
        "battle": "Organization Battle.wav",
        "town": "Twilight Town.wav",
        "destiny": "Destiny Islands.wav", 
        "final1": "KH-CoM Final Battle1.wav",
        "final2": "KH-CoM Final Battle2.wav"
    }
    tracks = {}
    for k, fname in requested.items():
        f = locate_music_file(fname, this_dir)
        if f:
            tracks[k] = f
            print(f"Found {k}: {f}")
        else:
            print(f"Missing {k}: tried {fname}")

    controller = MusicController(tracks)
    music_list(controller)

    # start menu
    choice = start_menu()
    if choice == 1:
        p, inv, gm, tl = load_game(controller)
        if p:
            player_stats.update(p)
    elif choice == 2:
        mp3_player_menu(controller)
    elif choice == 3:
        print("Goodbye."); return

    # main loop simple dispatcher
    game_mode = "field"
    inventory = []
    while True:
        if game_mode == "field":
            res = field_mode(player_stats, inventory, tiles, controller, map_data)
            if res:
                player_stats, inventory, tiles, game_mode = res
        elif game_mode == "battle":
            player_stats, inventory, game_mode = battle_mode(player_stats, inventory, controller)
        elif game_mode == "end game":
            print("Game over. Exiting.")
            break

if __name__ == "__main__":
    main()
