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

# Items database (global)
ITEMS = {
    'potion': {'heal': 100},
    'hi-potion': {'heal': 500},
    'x-potion': {'heal': 1000},
    'elixir': {'heal': 9999}
}

# Battle grid defaults
BATTLE_W = 100
BATTLE_H = 50

# --- Inventory helpers (stacked items) ---
def add_item(inventory, name, qty=1):
    for it in inventory:
        if it['name'] == name:
            it['count'] += qty
            return
    inventory.append({'name': name, 'count': qty})

def remove_item(inventory, name, qty=1):
    for i, it in enumerate(inventory):
        if it['name'] == name:
            if it['count'] > qty:
                it['count'] -= qty
            else:
                inventory.pop(i)
            return True
    return False

def inventory_slot_name(inventory, slot):
    if 0 <= slot < len(inventory):
        return inventory[slot]['name']
    return None

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


# --- Items / usage ---
def use_item(player_stats, inventory, item_name, items_db=None):
    """Apply an item effect from items_db (or global ITEMS) to player and remove one from inventory.
    Returns True if item was used, False otherwise."""
    items_db = items_db or ITEMS
    # inventory is stacked: list of {'name', 'count'}
    entry = None
    for it in inventory:
        if it['name'] == item_name:
            entry = it
            break
    if not entry:
        print("You don't have that item.")
        return False
    info = items_db.get(item_name)
    if not info:
        print(f"Unknown item: {item_name}")
        return False
    # Heal effect (respect max HP)
    if 'heal' in info:
        heal_amount = info['heal']
        prev = player_stats.get('HP', 0)
        max_hp = player_stats.get('max_hp', prev)
        new_hp = min(prev + heal_amount, max_hp)
        actual_heal = new_hp - prev
        player_stats['HP'] = new_hp
        print(f"Used {item_name}. Healed {actual_heal} HP (HP: {prev} -> {player_stats['HP']})")
    else:
        print(f"Used {item_name}.")
    # remove one instance from inventory (stacked)
    remove_item(inventory, item_name, qty=1)
    return True

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
    # legacy: not used for 2D battle rendering
    os.system("cls")
    print("=== BATTLE (info) ===")
    print(f"HP: {player_stats.get('HP')}  Exp: {player_stats.get('exp',0)}")
    print("Enemies:")
    for e in enemies:
        print(f" - {e['name']} HP:{e.get('HP')} pos:({e.get('b_x')},{e.get('b_y')})")

def render_battle_grid(player_stats, player_bpos, enemies, frame_index, player_sprite, b_w=BATTLE_W, b_h=BATTLE_H):
    """Render a blank battle grid with player and enemies placed by their battle coords."""
    os.system("cls")
    grid = [[" " for _ in range(b_w)] for _ in range(b_h)]
    # place enemies first so player can potentially overwrite
    for e in enemies:
        ex = int(e.get('b_x', 0))
        ey = int(e.get('b_y', 0))
        size_x = max(1, int(e.get('size_x', 1)))
        size_y = max(1, int(e.get('size_y', 1)))
        ch = e.get('sprite', e.get('walk', ['E']))
        if isinstance(ch, list):
            ch = ch[frame_index % len(ch)]
        else:
            ch = ch
        for oy in range(size_y):
            for ox in range(size_x):
                tx = ex + ox
                ty = ey + oy
                if 0 <= ty < b_h and 0 <= tx < b_w:
                    grid[ty][tx] = ch

    # place player
    px = int(player_bpos['x'])
    py = int(player_bpos['y'])
    player_frame = player_sprite.get('frames', [player_sprite.get('walk')])[frame_index % max(1, len(player_sprite.get('frames', [player_sprite.get('walk')]))) ]
    if 0 <= py < b_h and 0 <= px < b_w:
        grid[py][px] = player_frame

    # print grid
    print("=== BATTLE ===")
    for row in grid:
        print("".join(row))
    print(f"HP: {player_stats.get('HP')}  PlayerPos:({px},{py})")

# --- Modes ---
def field_mode(player_stats, inventory, tiles, controller, map_data):
    """Field mode: explore map, encounter battles, interact with tiles."""
    # auto-music
    if 'town' in controller.tracks and getattr(controller, "current_track", None) != 'town':
        music_play(controller, 'town')
    
    steps = player_stats.get('steps', 0)
    last_x, last_y = player_stats['x'], player_stats['y']
    render_map(map_data, last_x, last_y)  # Initial render
    
    RENDER_DELAY = 0.06  # seconds between each map render/loop
    while True:
        action = read_action()
        if action is None:
            time.sleep(RENDER_DELAY)
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
                time.sleep(RENDER_DELAY)
                if random.random() < 0.05:
                    if 'battle' in controller.tracks:
                        music_play(controller, 'battle')
                    return player_stats, inventory, tiles, "battle"
        elif isinstance(action, str) and action.startswith('use_item_'):
            # quick-use slots: use item 1/2/3
            try:
                slot = int(action.rsplit('_', 1)[-1]) - 1
                if 0 <= slot < len(inventory):
                    item_name = inventory_slot_name(inventory, slot)
                    used = use_item(player_stats, inventory, item_name, ITEMS)
                    if used:
                        render_map(map_data, player_stats['x'], player_stats['y'])
                else:
                    print("No item in that slot.")
            except Exception:
                pass
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
                # Interactive inventory: arrows to choose, Enter to use, Esc to exit
                if not inventory:
                    print("Inventory: empty"); input("Enter to continue")
                else:
                    idx = 0
                    while True:
                        os.system("cls")
                        print("=== Items ===")
                        for i, it in enumerate(inventory):
                            print(f"{'> ' if i==idx else '  '}{it}")
                        print("Enter=use, Esc=exit, arrows to move")
                        k = msvcrt.getch()
                        if k == b'\xe0':
                            k2 = msvcrt.getch()
                            if k2 == b'H': idx = (idx-1) % len(inventory)
                            elif k2 == b'P': idx = (idx+1) % len(inventory)
                        elif k == b'\r':
                            item_name = inventory[idx]
                            used = use_item(player_stats, inventory, item_name, ITEMS)
                            input("Enter to continue")
                            if used:
                                # if inventory emptied, exit
                                if not inventory:
                                    break
                                idx = min(idx, len(inventory)-1)
                        elif k == b'\x1b':
                            break
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
    # Initialize battle positions separate from field coords
    # player battle position starts near bottom-center
    b_w, b_h = BATTLE_W, BATTLE_H
    player_bpos = {'x': b_w // 2, 'y': b_h - 2}
    enemies = [{
        'name': 'Shadow',
        'HP': 30,
        'attack': 8,
        'defence': 3,
        'speed': 1,
        'b_x': min(b_w-2, player_bpos['x'] + 2),
        'b_y': player_bpos['y'],
        'size_x': 1,
        'size_y': 1,
        'walk': ['◈','◇'],   # placeholder frames
        'sprite': ['◈','◇'],
        'state': 'idle', 
        'exp': 20,
        'drop': 'potion',
        'drop_chance': 50
    }]
    # player sprites - simple frames for walk
    player_sprite = {'walk': ['⇩','↧'], 'frames':['⇩','↧']}

    if 'battle' in controller.tracks:
        music_play(controller, 'battle')


    frame = 0
    last_update = time.time()
    last_move_time = 0.0
    last_attack_time = 0.0
    MOVE_DELAY = 0.10  # seconds between moves
    ATTACK_DELAY = 0.35  # seconds between attacks
    RENDER_DELAY = 0.06  # seconds between each battle render/loop

    while True:
        now = time.time()
        # update animation frame every 0.3s
        if now - last_update > 0.3:
            frame += 1
            last_update = now

        # render 2D battle grid
        render_battle_grid(player_stats, player_bpos, enemies, frame, player_sprite, b_w=b_w, b_h=b_h)

        action = read_action()
        if action is None:
            # simulate enemies moving toward player slowly
            if last_move_time == 0.0 or now - last_move_time > MOVE_DELAY:
                for e in enemies:
                    old_x, old_y = e.get('b_x'), e.get('b_y')
                    if e.get('b_x') > player_bpos['x']: e['b_x'] -= e['speed']
                    elif e.get('b_x') < player_bpos['x']: e['b_x'] += e['speed']
                    if e.get('b_y') > player_bpos['y']: e['b_y'] -= e['speed']
                    elif e.get('b_y') < player_bpos['y']: e['b_y'] += e['speed']
                    if e.get('b_x') == player_bpos['x'] and e.get('b_y') == player_bpos['y']:
                        e['b_x'], e['b_y'] = old_x, old_y
                last_move_time = now
            # check enemy attacks
            for e in enemies:
                dist = abs(e.get('b_x')-player_bpos['x']) + abs(e.get('b_y')-player_bpos['y'])
                if dist <= 1 and random.random() < 0.15:
                    dmg = max(0, e['attack'] - player_stats.get('defence',0))
                    player_stats['HP'] -= dmg
                    print(f"{e['name']} hits you for {dmg}!"); time.sleep(0.6)
            # check end conditions
            if all(e['HP'] <= 0 for e in enemies):
                print("You won the battle!")
                for e in enemies:
                    exp_gain = e.get('exp', 0)
                    if exp_gain:
                        player_stats['exp'] = player_stats.get('exp', 0) + exp_gain
                        print(f"Earned {exp_gain} exp from {e['name']}.")
                    drop = e.get('drop')
                    if drop:
                        dc = e.get('drop_chance', 50)
                        prob = (dc / 100.0) if dc > 1 else float(dc)
                        if random.random() < prob:
                            add_item(inventory, drop, qty=1)
                            print(f"{e['name']} dropped {drop}!")
                if 'town' in controller.tracks:
                    music_play(controller, 'town')
                return player_stats, inventory, "field"
            if player_stats['HP'] <= 0:
                print("You died...")
                music_stop(controller)
                return player_stats, inventory, "end game"
            time.sleep(RENDER_DELAY)
            continue

        if action == 'pause':
            print("Battle paused. press p to resume.")
            while True:
                if read_action() == 'pause':
                    break
                time.sleep(0.02)
            continue
        if action in ('up','down','left','right'):
            # movement delay: only allow move if enough time has passed since last move
            if last_move_time == 0.0 or now - last_move_time > MOVE_DELAY:
                dx = {'left':-1,'right':1,'up':0,'down':0}[action]
                dy = {'up':-1,'down':1,'left':0,'right':0}[action]
                old_px, old_py = player_bpos['x'], player_bpos['y']
                player_bpos['x'] = max(0, min(b_w-1, player_bpos['x'] + dx))
                player_bpos['y'] = max(0, min(b_h-1, player_bpos['y'] + dy))
                # collision: if moved into enemy, revert
                collided = False
                for e in enemies:
                    if int(e.get('b_x')) == int(player_bpos['x']) and int(e.get('b_y')) == int(player_bpos['y']):
                        collided = True
                        break
                if collided:
                    player_bpos['x'], player_bpos['y'] = old_px, old_py
                last_move_time = now
            time.sleep(RENDER_DELAY)
        elif action == 'attack':
            # attack delay
            if now - last_attack_time > ATTACK_DELAY:
                # attack nearest alive enemy within range
                alive = [e for e in enemies if e['HP'] > 0]
                if alive:
                    # choose nearest by battle coordinates
                    target = min(alive, key=lambda e: abs(e.get('b_x',0)-player_bpos['x']) + abs(e.get('b_y',0)-player_bpos['y']))
                    dist = abs(target.get('b_x',0)-player_bpos['x']) + abs(target.get('b_y',0)-player_bpos['y'])
                    if dist <= 1:
                        dmg = max(0, player_stats.get('attack',10) - target.get('defence',0))
                        target['HP'] -= dmg
                        print(f"You hit {target['name']} for {dmg}!"); time.sleep(0.5)
                    else:
                        print("Enemy is too far to attack!"); time.sleep(0.4)
                last_attack_time = now
        elif isinstance(action, str) and action.startswith('use_item_'):
            # quick-use in battle
            try:
                slot = int(action.rsplit('_', 1)[-1]) - 1
                if 0 <= slot < len(inventory):
                    item_name = inventory_slot_name(inventory, slot)
                    use_item(player_stats, inventory, item_name, ITEMS)
                else:
                    print("No item in that slot.")
            except Exception:
                pass
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
    # initial player (started in middle-ish area)
    player_stats = {'x': 40, 'y': 30, 'HP': 120, 'max_hp': 120, 'attack': 12, 'defence': 5, 'Level':1, 'steps':0, 'exp':0, 'munny':0, 'items':[]}
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
            # Ensure loaded player has max_hp and cap HP to max
            p.setdefault('max_hp', p.get('HP', 120))
            if p.get('HP', 0) > p['max_hp']:
                p['HP'] = p['max_hp']
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
