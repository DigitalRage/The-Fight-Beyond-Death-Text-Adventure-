# BB 1st Final Project, The Fight Beyond Death: Text Adventure

#SETUP
#- Import libraries: os, time, winsound, mscrt, save (My Save File), music controller (music playback)
import os, time, random, msvcrt, json
from music_controller import MusicController

SAVE_FILE = "save.json"

# === Utility: Input mapping (msvcrt) ===
def read_action():
    # Non-blocking: returns a semantic action or None
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getch()
    if key == b'\xe0':  # arrow keys
        key2 = msvcrt.getch()
        return {
            b'H': 'up',
            b'P': 'down',
            b'K': 'left',
            b'M': 'right'
        }.get(key2, None)
    mapping = {
        b'w': 'up',
        b's': 'down',
        b'a': 'left',
        b'd': 'right',
        b'p': 'pause',
        b'i': 'interact',
        b'=': 'next_track',
        b'-': 'prev_track',
        b' ': 'attack',
        b'j': 'dodge_left',
        b'l': 'dodge_right',
        b'i': 'dodge_up',
        b'k': 'dodge_down',
        b'1': 'use_item_1',
        b'2': 'use_item_2',
        b'3': 'use_item_3',
        b'm': 'open_menu'
    }
    return mapping.get(key, None)

#Music runner function
#- Input: music track name
#- Use Music Controller to play track
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

def clear_screen():
    os.system('cls') #Cleans the console screen

def mp3_player_menu(controller):
    # Display configured track keys (e.g., "battle", "town", "destiny")
    track_names = list(controller.tracks.keys())
    if not track_names:
        print("No tracks configured.")
        return

    selected = 0
    while True:
        print("\n\033c=== MP3 Player ===")
        for i, name in enumerate(track_names):
            print(f"{'> ' if i == selected else '  '}{name}")
        print("Enter=Play, Esc=Exit, Up/Down=Navigate")

        key = msvcrt.getch()
        if key == b'\xe0':
            key2 = msvcrt.getch()
            if key2 == b'H':
                selected = (selected - 1) % len(track_names)
            elif key2 == b'P':
                selected = (selected + 1) % len(track_names)
        elif key == b'\r':
            controller.play(track_names[selected])
        elif key == b'\x1b':
            print("Closing MP3 Player...")
            break

#LEVEL UP FUNCTION
#- Input: level number
#- Multiply all stats by 1.2
#- Return new stats
#- Display "Level Up!" message
def level_up(player_stats):
    for stat in ['defence', 'spirit', 'attack', 'magic', 'mana', 'HP']:
        player_stats[stat] = int(player_stats[stat] * 1.2)
    player_stats['Level'] += 1
    print("Level Up! You are now level", player_stats['Level'])
    return player_stats

#TILE SETUP FUNCTION
#- Input: tile id, x coordinate, y coordinate
#- Create a tile object with id, x, y
#- Place tile object into Tiles list
#- When map is displayed, draw each tile at its x and y coordinates
def setup_tile(tiles, tile_id, x, y):
    tile = {'id': tile_id, 'x': x, 'y': y}
    tiles.append(tile)
    return tiles

#TILE ID FUNCTION
#- Input: player position (x, y)
#- Check which tile in Tiles list matches the position
#- Return tile id
#- If no tile found then return "empty"
def get_tile_id(x, y, tiles):
    for tile in tiles:
        if tile['x'] == x and tile['y'] == y:
            return tile['id']
    return "empty"

#COLLISION FUNCTION
#- Input: desired player position (x, y)
#- Use Tile ID function to check tile at that position
#- If tile id is "wall" or "blocked" then prevent movement
#- Else allow movement
def check_collision(x, y, tiles):
    tile_id = get_tile_id(x, y, tiles)
    if tile_id in ["wall", "blocked"]:
        return False
    return True

# === START MENU ===
def start_menu():
    options = ["Start New Game", "Load Saved Game", "MP3 Player", "Quit"]
    selected = 0

    while True:
        print("\n\033c=== The Fight Beyond Death ===")
        for i, option in enumerate(options):
            print(f"{'> ' if i == selected else '  '}{option}")

        key = msvcrt.getch()
        if key == b'\xe0':  # arrow keys
            key2 = msvcrt.getch()
            if key2 == b'H':  # Up
                selected = (selected - 1) % len(options)
            elif key2 == b'P':  # Down
                selected = (selected + 1) % len(options)
        elif key == b'\r':  # Enter
            return selected

#SAVE / LOAD SYSTEM
#- Save function:
#  - Store player stats, inventory, current map, position, and track index
#  - Write data to save file
def save_game(player_stats, inventory, game_mode, tiles, controller, save_file=SAVE_FILE):
    game_data = {
        "player_stats": player_stats,
        "inventory": inventory,
        "game_mode": game_mode,
        "tiles": tiles,
        "current_track": controller.current_track
    }
    try:
        with open(save_file, "w") as file:
            json.dump(game_data, file, indent=4)
        print("Game saved successfully.")
    except Exception as error:
        print("Error saving game:", error)

#- Load function:
#  - Read data from save file
#  - Restore player stats, inventory, current map, position, and track index
#  - Resume game from saved state
def load_game(controller, save_file=SAVE_FILE):
    try:
        with open(save_file, "r") as file:
            game_data = json.load(file)
        player_stats = game_data.get("player_stats", {
            'defence': 10, 'spirit': 10, 'attack': 10, 'magic': 10,
            'mana': 50, 'HP': 100, 'EXP': 0, 'Level': 1, 'Munny': 0,
            'x': 0, 'y': 0, 'invulnerable': False
        })
        inventory = game_data.get("inventory", [])
        game_mode = game_data.get("game_mode", "field")
        tiles = game_data.get("tiles", [])
        track = game_data.get("current_track")
        if track:
            controller.play(track)
        print("Game loaded successfully.")
        return player_stats, inventory, game_mode, tiles
    except FileNotFoundError:
        print("No save file found.")
        return None, None, None, None
    except Exception as error:
        print("Error loading game:", error)
        return None, None, None, None

#ENEMY SYSTEM (LIVE ACTION)
#- Enemy object:
#  - Name, HP, Attack, Defence, Speed, Aggro range
#  - State (idle, chasing, attacking, stunned)
#  - Attack cooldown
#  - Reward: EXP amount, Munny amount, possible item drop
#- Enemy update loop runs every frame:
#  - If HP <= 0 then enemy dies and drop reward
#  - Else:
#    - If distance > aggro range then state is "idle"
#    - Else if distance <= aggro range then state is "chasing"
#    - If state is "chasing":
#      - Move toward player
#      - If close enough then state is "attacking"
#    - If state is "attacking":
#      - Play attack animation
#      - Trigger "attack window" (short time where player can dodge)
#      - If player dodge is active during window:
#        - Player avoids damage
#      - Else:
#        - Damage is enemy attack - player defence
#        - If damage < 0 then damage is 0
#        - Subtract damage from player HP
#      - Reset state to "chasing" after cooldown
#    - If enemy is hit by player:
#      - Subtract damage from enemy HP
#      - If HP > 0 then briefly set state is "stunned"
#      - After stun duration return to chasing
def compute_damage(attacker_atk, defender_def):
    dmg = attacker_atk - defender_def
    return max(dmg, 0)

def enemy_update(enemy, player_stats):
    # Setup defaults
    enemy.setdefault('cooldown', 1.0)
    enemy.setdefault('last_attack', 0.0)
    enemy.setdefault('stun_until', 0.0)
    enemy.setdefault('aggro_range', 5)
    enemy.setdefault('speed', 1)
    enemy.setdefault('defence', 0)
    enemy.setdefault('attack', enemy.get('Attack', 8))

    if enemy['HP'] <= 0:
        if enemy.get('state') != 'dead':
            enemy['state'] = 'dead'
            print(f"{enemy['name']} has died.")
        return enemy

    now = time.time()
    if now < enemy['stun_until']:
        enemy['state'] = 'stunned'
        return enemy

    # Distance
    distance = ((enemy['x'] - player_stats['x']) ** 2 + (enemy['y'] - player_stats['y']) ** 2) ** 0.5
    if distance > enemy['aggro_range']:
        enemy['state'] = 'idle'
        return enemy
    else:
        enemy['state'] = 'chasing'

    # Move
    if enemy['x'] < player_stats['x']:
        enemy['x'] += enemy['speed']
    elif enemy['x'] > player_stats['x']:
        enemy['x'] -= enemy['speed']
    if enemy['y'] < player_stats['y']:
        enemy['y'] += enemy['speed']
    elif enemy['y'] > player_stats['y']:
        enemy['y'] -= enemy['speed']

    # Recompute distance
    distance = ((enemy['x'] - player_stats['x']) ** 2 + (enemy['y'] - player_stats['y']) ** 2) ** 0.5
    if distance <= 1.0 and (now - enemy['last_attack']) >= enemy['cooldown']:
        enemy['state'] = 'attacking'
        enemy['last_attack'] = now
        print(f"{enemy['name']} is attacking!")
    return enemy

#PLAYER DODGE FUNCTION
#- Input: dodge button press
#- When pressed:
#  - Move player quickly 2 tiles in chosen direction
#  - Set "invulnerable" flag for short duration (e.g. 0.5 seconds)
#  - If enemy attack occurs during invulnerable window then no damage taken
#  - Show dodge animation
def player_dodge(player_stats, direction, tiles):
    dodge_distance = 2
    invulnerable_duration = 0.5
    dx, dy = 0, 0
    if direction == 'up':
        dy = -dodge_distance
    elif direction == 'down':
        dy = dodge_distance
    elif direction == 'left':
        dx = -dodge_distance
    elif direction == 'right':
        dx = dodge_distance
    new_x, new_y = player_stats['x'] + dx, player_stats['y'] + dy
    if check_collision(new_x, new_y, tiles):
        player_stats['x'], player_stats['y'] = new_x, new_y
    player_stats['invulnerable'] = True
    print("Player dodged!")
    time.sleep(invulnerable_duration)
    player_stats['invulnerable'] = False
    print("Player is no longer invulnerable.")
    return player_stats

#FIELD MODE
#- While player is alive and game mode is "field":
#  - If pause button is pressed then toggle Pause state
#    - While Pause state is true:
#      - Display "Game Paused"
#      - If pause button pressed again then resume game
#  - Else if movement button pressed then check collision and move player if allowed
#  - Else if interact button pressed:
#    - Use Tile ID function to check current tile
#    - If tile id is NPC then start dialogue
#    - Else if tile id is chest then open chest and add item to inventory
#    - Else if tile id is door then transition to new map
#    - Else do nothing
#  - Else if "=" is pressed:
#    - Increase Track index by 1
#    - If Track index > last track then wrap to first track
#    - Play new track (handled internally by game engine)
#  - Else if "-" is pressed:
#    - Decrease Track index by 1
#    - If Track index < 0 then wrap to last track
#    - Play new track (handled internally by game engine)
#  - Else if menu button is pressed then open menu (items, equipment, save, load, quit)
#  - Else wait for button press
#  - If random encounter is triggered then switch game mode to "battle"
#  - When entering field mode automatically start field background music
def field_mode(player_stats, inventory, tiles, controller):
    pause = False
    # Auto field music
    if 'town' in controller.tracks and controller.current_track != 'town':
        controller.play('town')

    print("Entering field mode. Move: arrows/WASD | Interact: i | Pause: p | Menu: m")
    while True:
        action = read_action()

        if action is None:
            # Random encounter check even when idle
            if random.random() < 0.002:  # slow chance while idle
                print("A random encounter!")
                if 'battle' in controller.tracks:
                    controller.play('battle')
                return player_stats, inventory, tiles, "battle"
            time.sleep(0.02)
            continue

        # Pause handling
        if action == 'pause':
            pause = not pause
            print("Game Paused." if pause else "Resuming game.")
            while pause:
                k = read_action()
                if k == 'pause':
                    pause = False
                    print("Resuming game.")
                time.sleep(0.02)
            continue

        # Movement
        if action in ('up', 'down', 'left', 'right'):
            dx, dy = 0, 0
            if action == 'up': dy = -1
            elif action == 'down': dy = 1
            elif action == 'left': dx = -1
            elif action == 'right': dx = 1
            new_x, new_y = player_stats['x'] + dx, player_stats['y'] + dy
            if check_collision(new_x, new_y, tiles):
                player_stats['x'], player_stats['y'] = new_x, new_y
            # Random encounter on movement
            if random.random() < 0.05:
                print("A battle approaches!")
                if 'battle' in controller.tracks:
                    controller.play('battle')
                return player_stats, inventory, tiles, "battle"

        # Interactions
        elif action == 'interact':
            tile_id = get_tile_id(player_stats['x'], player_stats['y'], tiles)
            if tile_id == "NPC":
                print("Starting dialogue with NPC...")
            elif tile_id == "chest":
                item = "Potion"
                inventory.append(item)
                print(f"You opened a chest! Obtained {item}.")
            elif tile_id == "door":
                print("You pass through the door to a new area...")
                # Example: teleport player or change map
            else:
                print("There's nothing to interact with here.")

        # Music control
        elif action == 'next_track':
            controller.next_track()
        elif action == 'prev_track':
            controller.prev_track()

        # Open menu
        elif action == 'open_menu':
            in_game_menu(player_stats, inventory, controller)

        time.sleep(0.02)

# In-game menu (pause, items, save, load, mp3, quit to title)
def in_game_menu(player_stats, inventory, controller):
    options = ["Resume", "Items", "Save", "Load", "MP3 Player", "Status", "Quit to Title"]
    selected = 0
    while True:
        print("\n\033c=== Menu ===")
        for i, option in enumerate(options):
            print(f"{'> ' if i == selected else '  '}{option}")
        key = msvcrt.getch()
        if key == b'\xe0':
            key2 = msvcrt.getch()
            if key2 == b'H':
                selected = (selected - 1) % len(options)
            elif key2 == b'P':
                selected = (selected + 1) % len(options)
        elif key == b'\r':
            choice = options[selected]
            if choice == "Resume":
                return
            elif choice == "Items":
                if inventory:
                    print("Inventory:", ", ".join(inventory))
                else:
                    print("Inventory is empty.")
            elif choice == "Save":
                save_game(player_stats, inventory, "field", [], controller)
            elif choice == "Load":
                p, inv, gm, tl = load_game(controller)
                if p:
                    player_stats.update(p)
                    inventory[:] = inv
                    print("Loaded game in menu.")
            elif choice == "MP3 Player":
                mp3_player_menu(controller)
            elif choice == "Status":
                print(f"HP: {player_stats['HP']} | MP: {player_stats['mana']} | ATK: {player_stats['attack']} | DEF: {player_stats['defence']} | LV: {player_stats['Level']} | EXP: {player_stats['EXP']} | Munny: {player_stats['Munny']}")
            elif choice == "Quit to Title":
                # Stop music on all channels
                controller.stop(); controller.stop1(); controller.stop2(); controller.stop3()
                # Return to title by raising a simple flag via exception pattern
                raise SystemExit("ReturnToTitle")

#BATTLE MODE
#- While player is alive and game mode is "battle":
#  - If pause button is pressed then toggle Pause state
#    - While Pause state is true:
#      - Display "Game Paused"
#      - If pause button pressed again then resume game
#  - Else if movement button pressed then move player 1 tile and show walk sprite
#  - Else if dodge button pressed then run Player Dodge Function
#  - Else if attack button pressed then hit opponent, calculate damage, show attack sprite
#  - Else if item button is pressed:
#    - If number button is pressed then use item
#    - Else if "+" is pressed then go to next item list
#    - Else if "-" is pressed then go to previous item list
#    - Else if Backspace is pressed then return to battle setup
#    - Else wait for button press
#  - For each enemy: run Enemy Update Loop
#  - If player dies:
#    - If quit button is pressed then show "Game Over" and close game
#    - Else if load save button is pressed then load last save file and return to field mode
#    - Else end game loop
#  - When entering battle mode automatically start battle background music
def battle_mode(player_stats, inventory, controller):
    # Spawn enemies
    current_enemies = [
        {
            'name': 'Shadow',
            'HP': 30,
            'attack': 10,
            'defence': 4,
            'speed': 1,
            'aggro_range': 5,
            'x': player_stats['x'] + 4,
            'y': player_stats['y'],
            'exp_reward': 25,
            'munny_reward': 5,
            'item_drop': None,
            'state': 'idle',
            'cooldown': 1.2
        }
    ]

    if 'battle' in controller.tracks:
        controller.play('battle')

    print("Entering battle. Attack: Space | Dodge: J/L/I/K | Move: WASD/arrows | Pause: p")
    last_player_attack = 0.0
    player_attack_cooldown = 0.5

    while True:
        action = read_action()

        if action is None:
            # Update enemies even when idle
            for e in current_enemies:
                enemy_update(e, player_stats)
                if e.get('state') == 'attacking':
                    if not player_stats.get('invulnerable', False):
                        dmg = compute_damage(e.get('attack', 10), player_stats.get('defence', 10))
                        if dmg > 0:
                            player_stats['HP'] -= dmg
                            print(f"{e['name']} hits you for {dmg}. HP: {player_stats['HP']}")
                    else:
                        print("You dodged the attack!")
            # Win/Loss checks
            if all(e['HP'] <= 0 for e in current_enemies):
                # Rewards
                total_exp = sum(e.get('exp_reward', 0) for e in current_enemies)
                total_munny = sum(e.get('munny_reward', 0) for e in current_enemies)
                player_stats['EXP'] += total_exp
                player_stats['Munny'] += total_munny
                print(f"Gained {total_exp} EXP and {total_munny} Munny!")
                for e in current_enemies:
                    drop = e.get('item_drop')
                    if drop:
                        inventory.append(drop)
                        print(f"Received item: {drop}")
                # Level up check
                level_threshold = player_stats['Level'] * 100
                if player_stats['EXP'] >= level_threshold:
                    level_up(player_stats)
                # Transition back to field
                if 'town' in controller.tracks:
                    controller.play('town')
                return player_stats, inventory, "field"

            if player_stats['HP'] <= 0:
                print("Game Over!")
                # Stop music channels
                controller.stop(); controller.stop1(); controller.stop2(); controller.stop3()
                return player_stats, inventory, "end game"

            time.sleep(0.02)
            continue

        # Pause
        if action == 'pause':
            print("Battle Paused. Press 'p' to resume.")
            while True:
                k = read_action()
                if k == 'pause':
                    print("Resuming battle.")
                    break
                time.sleep(0.02)
            continue

        # Movement
        if action in ('up', 'down', 'left', 'right'):
            dx, dy = 0, 0
            if action == 'up': dy = -1
            elif action == 'down': dy = 1
            elif action == 'left': dx = -1
            elif action == 'right': dx = 1
            player_stats['x'] += dx
            player_stats['y'] += dy

        # Dodge
        elif action in ('dodge_left', 'dodge_right', 'dodge_up', 'dodge_down'):
            direction = {
                'dodge_left': 'left',
                'dodge_right': 'right',
                'dodge_up': 'up',
                'dodge_down': 'down'
            }[action]
            player_stats = player_dodge(player_stats, direction, tiles=[])

        # Attack
        elif action == 'attack':
            now = time.time()
            if now - last_player_attack >= player_attack_cooldown:
                last_player_attack = now
                # Target nearest enemy
                alive = [e for e in current_enemies if e['HP'] > 0]
                if alive:
                    target = min(alive, key=lambda e: (e['x'] - player_stats['x']) ** 2 + (e['y'] - player_stats['y']) ** 2)
                    dmg = compute_damage(player_stats.get('attack', 10), target.get('defence', 0))
                    target['HP'] -= dmg
                    print(f"You strike {target['name']} for {dmg}. HP left: {max(target['HP'], 0)}")
                    # Stun briefly if still alive
                    if target['HP'] > 0:
                        target['stun_until'] = time.time() + 0.3

        # Items
        elif action in ('use_item_1', 'use_item_2', 'use_item_3'):
            idx = {'use_item_1': 0, 'use_item_2': 1, 'use_item_3': 2}[action]
            if idx < len(inventory):
                item = inventory.pop(idx)
                print(f"You used {item}.")
                # Simple effect: heal 20 if potion-like
                if item.lower() == "potion":
                    player_stats['HP'] = min(player_stats['HP'] + 20, player_stats['Level'] * 120)
                    print(f"HP healed. Current HP: {player_stats['HP']}")
            else:
                print("No item in that slot.")

        # Music control
        elif action == 'next_track':
            controller.next_track()
        elif action == 'prev_track':
            controller.prev_track()

        time.sleep(0.02)

#GAME LOOP
#- Start in field mode
#- While game is running:
#  - If mode is "field" then run field mode loop
#  - Else if mode is "battle" then run battle mode loop
#  - Else if mode is "end game" then end game
def main():
    #- Define variables:
    #  - Frame tiles
    #  - Character sprites (walk, attack, dodge in 4 directions)
    #  - Player stats (defence, spirit, attack, magic, mana, HP, EXP, Level, Munny(cash))
    #  - Game mode is "field" at start
    #  - Player alive is true
    #  - Tiles is list of tiles for map
    #  - Music tracks is in dictionary of track names and file paths
    #  - Current track is none
    #  - Track index is 0
    #  - Pause state is false

    frame_tiles = {}
    character_sprites = {'walk': {}, 'attack': {}, 'dodge': {}}
    player_stats = {
        'defence': 10, 'spirit': 10, 'attack': 10, 'magic': 10,
        'mana': 50, 'HP': 100, 'EXP': 0, 'Level': 1, 'Munny': 0,
        'x': 0, 'y': 0, 'invulnerable': False
    }
    tiles = [
        'map': '''⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⣀⢀⠀⡀⠀⣀⡀⠀⢀⠀⢀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣶⣾⣿⣶⣄⠀⠀⢈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⣀⡄⢀⡀⠀⢀⣀⠀⣠⡀⢐⣾⣿⣿⣿⣧⣀⣀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣄⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢠⡀⣄⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠾⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠪⠀⠀⣉⢿⣏⢯⡽⣹⢏⡾⣽⣿⣿⣿⣿⡇⠀⠀⠀⠀⢚⠉⢴⣻⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣵⣖⣦⣼⣎⡞⣧⢏⡷⢫⣞⣽⣿⣿⣿⣿⣟⣢⣄⣠⣤⣾⣶⣶⣿⣿⣿⣿⣿⡥⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣳⡝⣮⡝⣞⡳⣎⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣶⣿⠌⠳⠩⠟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢧⣛⡾⣿⣿⣿⣿⣿⡆⠀⠀⠀⣹⣟⡼⣳⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠏⠁⠙⢿⣿⣿⣿⣿⣶⣤⣴⣤⣿⣎⢷⣫⢿⠿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣴⣦⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⡏⡾⣧⡽⣮⢿⡼⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⣠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣀⣀⣠⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣭⣷⣿⣾⣽⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣦⣄⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢞⡭⣟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⢏⡷⣭⢻⡜⣧⢻⣜⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣝⢯⡽⡭⢯⡝⣮⢳⡝⣶⡹⣎⠷⣎⢷⢳⣎⢷⣚⢶⡹⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⡟⣮⢳⣭⢳⡝⣮⢳⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡙⠎⠲⠉⠇⢻⣜⢧⣛⢶⡹⣎⠿⣜⠯⣞⡼⣣⢟⡮⣝⡻⣿⢿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣦⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⡟⣯⣛⢧⣻⣜⡳⣎⢷⡹⣎⠷⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢯⣽⠂⠀⠀⠀⢡⡻⢮⡝⣮⢳⣭⢻⣜⡻⣼⡱⣏⢾⣱⣏⣳⡝⣮⠽⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣽⣿⣿⣿⣿⣛⢶⡹⣎⠷⣜⡳⣝⢮⡳⣭⢻⡜⣧⢻⡜⣧⢻⡜⣧⣿⣞⣷⣾⡧⢤⡤⣤⣛⢯⡳⣝⢮⡳⣎⠷⣎⣵⣳⠿⠏⣙⠭⡌⡉⠻⣼⢻⡜⡿⣿⠿⡿⢿⡿⣿⢿⡿⣿⣿⢿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⡯⣝⢮⡝⣮⢳⣭⢻⣜⡳⣝⢮⡳⣭⢳⡝⣮⢳⡝⣮⢳⡝⣾⣿⣿⣿⣿⣟⣧⢻⡴⣫⢞⡵⣫⢞⡵⣫⢻⡜⣿⡀⠀⠰⡃⠀⠀⠓⢸⣻⣷⣹⢳⣭⣛⡽⣣⢟⡼⣣⢟⣵⢺⣿⣿⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⢷⡹⢮⡝⣮⣓⠎⠳⠌⠓⡹⢎⡷⣭⢳⡝⣮⢳⡝⣮⢳⡝⣾⡹⣟⢿⣻⢻⡜⣧⢳⡝⣮⢳⡝⣮⢳⣭⢳⣿⣼⣿⣿⡀⠇⠀⠀⠀⢸⡷⣎⡗⡯⢶⡹⢶⡹⣎⢷⡹⣞⡼⣳⢾⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡿⣷⡹⢧⣛⠶⣏⠆⠀⠀⠀⢘⣯⡜⣮⢳⡝⣮⢳⡝⣮⢳⡝⣶⡹⣎⠷⣭⢳⡝⣮⢳⡝⣮⢳⡝⣮⣳⣮⣷⣮⣿⣿⡿⠁⣧⠀⠀⡆⢀⣿⣧⣛⣭⢳⡝⣧⢻⡜⣧⣛⢶⡹⣎⣿⡗⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣀⣠⣼⡟⠣⢏⢷⡭⣛⢧⡖⡤⣄⠤⣌⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⢶⡹⣎⠿⣜⢧⡻⣼⢣⣽⠶⠛⠋⢉⠀⠤⠤⠤⠤⠤⠠⠖⠃⠀⠀⠆⢸⣧⢻⡜⣮⢳⡝⣮⢳⡝⣶⡹⣎⢷⡹⢮⡝⣷⢶⣶⣆⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠠⣿⣿⣿⡿⢃⠀⠁⢌⡺⢼⡹⣞⡼⢳⣎⠿⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⣛⢧⡻⣜⡻⣜⢧⡻⣼⡟⣧⠀⠀⠀⡹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣯⣻⡜⣧⢻⡜⣧⢻⡜⣧⡝⣮⢳⡝⣧⢻⡼⣿⡿⣯⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⢯⢿⣆⡾⣦⢦⡟⢧⣛⢶⣹⢳⣎⠿⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⣛⢮⡳⣭⢳⡝⣮⢳⢧⣿⣜⣿⢶⡦⢵⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣟⢶⡹⣎⢷⡻⣜⢧⣛⢶⡹⣎⢷⡹⣎⢷⣣⢗⣿⠳⣯⢷⣶⣷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣛⢮⡳⣎⢷⡹⢶⡹⢧⣛⢮⣓⢯⣜⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣼⢣⡟⣮⢳⣭⢳⣝⢮⣛⢶⣣⢟⡽⣿⡯⠍⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⢸⣟⢮⡳⣝⢮⡳⣝⢮⡝⣮⢳⡝⣮⢳⡝⡾⠼⣭⠞⡽⣎⠿⣯⣟⡀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣷⣿⣮⢷⡹⢧⣛⢧⣛⢮⡝⡾⣜⡳⣝⢮⡳⣝⢮⡳⣝⢮⡳⣭⢳⡝⣮⢳⣎⠷⣎⢷⡹⣞⡼⣝⠾⣽⣧⢨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣯⢏⡷⣹⢎⡷⣹⢮⡝⣮⢳⡝⣮⢳⡽⣹⢻⡜⣯⢳⣭⢻⡼⣣⢟⣿⣿⣷⠤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⡟⣮⡝⣧⣛⢮⡝⣮⡝⣾⣱⢻⡜⣧⢻⡜⣧⢻⡜⣧⣻⣼⣧⡿⣼⣷⣮⡿⢼⣧⡿⣼⡵⢯⡿⠿⠏⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⢿⣯⡟⣼⢣⡟⣼⢣⡟⡼⢣⡟⣼⢣⡟⣼⢣⡟⣼⢣⣟⡲⣏⢾⡱⣏⡟⣿⣿⡅⢀⠀⠀⣀⢀⣀⣀⡀⢀⢀⣀⠀⢀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢀⠤⠠⠍⠙⢿⣷⣿⣷⣯⢞⡽⣲⣿⣷⣿⣷⡿⣜⢧⡻⣜⢧⣻⣾⠁⡤⠀⠒⠀⠀⠂⠀⠒⠂⠀⠀⠀⠀⠀⠀⠐⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢸⣿⢞⡵⣫⢞⡵⣫⡜⠁⠃⢸⣧⢻⡜⣧⢻⡜⣧⣛⢶⡹⣎⢷⡹⢮⡝⡶⣭⢿⣻⢿⣿⣿⢿⡿⣻⠿⣿⣿⣿⡇⢈⠀⠀⢸⡦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠸⡅⠀⠀⠀⣾⣿⣿⣿⣿⡮⡷⣽⣿⣿⣿⣿⣿⡜⣧⢻⡜⣧⢿⣟⠉⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⡀⠀⠁⣼⣿⢎⡷⣹⢎⡷⢣⡳⣄⣤⣧⢯⡳⣝⢮⡳⣝⢶⡹⣎⢷⡹⢮⡝⣧⢻⠵⣎⠷⣭⢞⡶⣹⢮⠽⣭⢻⣻⡻⣿⣇⡈⠂⠠⠔⠁⠀⠀⠀⠀⠀⠀⠀⠀⢠⣠⡀⣀⣰⣤⣤⣄⣤⣀⣠⣄⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⣼⠀⠀⠀⡀⠻⣿⣿⣿⡛⠉⠙⠚⣿⣿⣿⣿⣿⢞⡵⣫⢞⡵⣿⣷⢈⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢁⣶⣶⣷⣿⡿⣝⢮⡳⣝⢮⡝⣧⢻⡜⣶⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⢮⡝⣧⢻⡜⡯⣝⢮⡻⣜⡳⣞⡵⣫⢻⡜⣧⢏⡷⣳⡞⣿⣿⣿⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣏⡀
                ⠀⠀⠀⠀⠀⠀⠀⠀⣼⠄⠀⠀⠄⢼⣿⣿⣿⡇⡀⠀⠀⣿⣿⣿⣿⣿⣎⣷⣹⣾⢭⢿⡟⠉⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣿⣿⣿⣿⡻⣜⢧⡻⣜⢧⡻⣜⢧⣛⢶⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⢧⡻⣜⢧⡻⢵⣫⢞⡵⣫⢵⣎⠷⣭⢳⡝⣮⡝⡶⣭⣻⠼⠿⡟⠟⠀⠀⠀⠀⠀⣀⣠⡀⠄⡈⡉⡛⡙⢻⣳⡽⢮⡝⡾⢿⣿⡟⠂
                ⠀⠀⠀⠀⢠⣦⣷⣦⠹⡀⠀⠀⠂⢻⣿⣛⡿⣿⣷⣟⣷⡿⠋⢏⢹⣿⣿⣿⣿⣿⣽⣿⣿⢀⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⣿⣻⡿⣝⡳⣝⢮⡳⣝⢮⡳⡽⢮⡝⣮⢳⡝⣮⢳⡝⣮⢳⡝⣮⡝⣧⢻⡜⣧⣛⢧⡝⣮⢳⡝⣾⣸⠻⣜⢧⣛⢶⣹⢳⣽⣯⢤⠂⠉⡇⠀⠀⠀⠀⠰⣿⣿⣿⠠⡅⠀⠀⣡⢈⣿⣟⣧⢻⣙⢯⡿⣷⠀
                ⠀⠀⠀⠀⠸⠿⣿⠟⢸⠁⠀⠀⢇⠈⣿⠿⣽⣿⡞⣭⢟⣻⣌⡤⣞⣿⣿⣿⣿⣿⣿⣿⣿⠀⢦⢀⣀⢀⢠⠀⣀⣀⠀⠀⠀⢀⣠⢠⡤⠄⡀⠀⠀⠀⠀⠀⠀⠰⡄⠙⠛⠛⠛⠋⠛⠚⠷⡽⢮⡽⣹⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⣛⢶⡹⣎⢷⡹⢶⡹⢮⡝⣮⢳⡝⣶⢣⡟⣮⢳⡝⣮⣷⣯⣾⣧⠀⠙⠒⠾⡤⠤⠤⠦⠤⠬⡩⢥⡴⠃⠀⠀⠘⠦⠬⠉⠛⠛⢯⣷⡿⣇⠀
                ⢠⣷⣶⣦⣰⠓⠒⠒⠋⠀⠀⠀⠈⠑⠂⠀⢀⠸⣿⣜⣻⢶⣻⢿⣿⣿⣿⣿⣿⡇⣤⠩⠄⢹⣿⣶⣿⣶⣾⣿⣿⡀⡇⠀⠀⡇⣺⣾⣿⡿⢱⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠈⠉⠁⡆⣹⣷⢭⡳⣎⢷⡹⣎⢷⡹⣎⢷⡹⢮⡝⣮⢳⡝⣮⡝⣧⣛⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣽⣿⣿⣿⣿⠁⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⣾⣿⣿⣯⠀
                ⣘⣿⣿⣏⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢌⡀⠻⠾⠷⠷⠿⠺⠾⢳⠟⠻⠟⠂⡎⠀⠠⣐⢿⢿⡿⢿⣿⣿⣿⡉⠣⠤⠤⠏⢿⣿⣿⡷⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢼⣿⣾⣵⣏⢾⡱⣏⢾⡱⣏⢾⣙⢧⡻⣜⢧⣛⢶⡹⢶⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⣿⣿⣿⣿⡏⠀⠢⠤⢼⠓⠒⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⣟⣿⣿⡇⠀
                ⢻⣿⣿⡟⠺⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠁⠀⠈⠀⠉⠁⠁⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⣄⣿⣿⣿⣿⡆⠀⠀⠀⠀⠉⠉⠀⡎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⣾⣿⣿⣿⣏⢾⡱⣏⢾⡱⣏⠾⣭⢞⡵⣫⢞⡭⣞⡝⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢿⣿⣿⣿⡇⢐⠀⠀⢸⠀⠀⠀⠀⢹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⡀⢿⣿⣿⣧⠀
                ⣘⣿⣿⣷⠄⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠃⠀⠀⣠⠀⣀⠀⣀⠀⠀⠀⠀⣀⣀⡀⡀⡇⠻⡿⠿⠿⣿⡜⣧⢻⡜⣧⣛⢶⡹⣜⢧⡻⣜⢧⡻⢵⣫⢞⡵⣫⢞⡵⣫⢞⡵⣫⢞⡵⣛⠾⣿⢿⡿⣷⣈⠒⢠⠘⢀⣀⣠⠤⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡇⠘⠟⠙⠋⠀
                ⢴⣿⣿⣻⣦⣤⣽⣧⣤⣤⣅⣥⣴⣄⣨⣍⠑⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⣾⣿⣶⣾⣿⣷⣿⣿⣆⠸⠀⠀⠀⠿⣿⣷⣿⣾⡍⠀⠀⡆⢼⣿⡱⣏⢾⡱⣏⢾⡱⣏⢾⡱⣏⠾⣭⢳⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⡼⣭⢻⡜⣧⢻⡽⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⠀⠀⠀⠀⠀
                ⢹⡿⣿⣽⣿⣿⣿⣿⣿⣿⢻⣿⣿⣿⣿⣿⠄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡆⠻⠿⡿⠿⣧⣤⣀⣀⣠⣀⣄⠸⠿⠿⡿⢿⣿⣿⣿⣿⠀⠤⡤⠄⣞⠻⡻⠿⠁⠧⡀⡠⠂⣼⣿⡻⣜⢧⡻⣜⡧⠛⡜⠣⠝⢾⣹⢎⡿⣜⡳⣝⢮⡳⣝⢮⡳⡽⣞⣷⣽⣞⣧⡻⣜⢧⡟⣿⣿⡿⣻⣀⣁⠐⠀⠀⡀⠀⣀⢀⡀⠀⢀⠒⠦⠤⠤⠴⠋⠀⠀⠀⠀⠀
                ⢹⣿⣻⢖⡻⣟⢿⡻⣟⢯⡳⣎⣟⡻⡿⣿⠈⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠙⠀⠤⣿⣿⣿⣿⣿⣿⣿⡋⠆⠈⠁⠀⢸⣿⣿⣿⣿⣿⣿⣿⢬⠈⠀⠈⢳⠀⠀⠠⣾⣿⣏⡷⣹⢎⡷⣹⣷⡁⠀⠀⠀⠸⣟⢮⡳⣎⢷⡹⣎⢷⡹⣎⠷⣽⣻⣿⣿⣿⡷⣝⣮⢳⣝⡳⣎⢷⣹⢻⣝⡻⣟⠿⣟⡿⣟⣟⡿⢿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⢹⣿⡹⣎⢷⡹⣎⢷⡹⣎⢷⣹⢲⣝⡳⣿⠄⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠻⠿⠿⠟⠿⠟⠿⠏⡌⠀⠀⠈⣜⠛⠛⠛⠿⠛⠿⠟⣸⠃⠀⠀⠘⠤⠤⢄⣉⣙⣛⠙⡓⢿⣼⢳⣮⣧⣀⣀⣠⡾⣏⢾⡱⣏⢾⡱⣏⢾⡱⣏⡻⣜⢿⡻⣟⢿⡻⣜⢧⡻⣜⡳⣝⢮⣓⢯⣜⡳⣭⢻⣜⡳⣝⢾⣻⢟⡿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⣼⣯⣷⡹⢮⡝⣮⢳⡝⣮⢳⣭⢳⣎⠷⣿⠩⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢡⢸⣯⡳⣞⡼⣭⢏⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣭⢳⡝⣮⡝⡾⣜⡳⣭⢳⣎⢷⡹⣎⢧⣏⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⣸⣿⢶⡹⢧⡻⣵⢫⡞⣵⢫⡖⣯⢺⡝⣿⡄⠀⠀⣀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠤⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠒⢆⠀⡖⠂⡀⢀⣀⣰⣿⢳⣣⢟⣬⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⡜⣧⢻⣜⡳⣞⡵⣫⢵⡫⣗⢮⡳⣝⢮⣗⣮⣿⡯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⢼⣿⣧⣛⢧⣛⢶⣫⢞⡵⣫⢞⡵⣫⢿⣾⣻⡶⣶⣶⣶⣾⣷⣾⣿⣷⣷⣾⣷⣶⣾⣶⣿⣿⣶⣾⣷⣾⣷⣶⣖⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢺⣿⣿⠿⣟⡿⣟⢿⡹⢧⡻⣜⠾⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⡳⣎⢷⣣⢏⡷⣭⢳⡝⣮⢳⡝⡾⢼⣿⣯⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠸⡿⣿⣿⠾⡿⠶⠿⠾⠷⠿⢮⢷⣯⡞⡽⢧⢿⣯⣿⣿⠿⠿⠿⠛⠻⡟⠻⠻⠻⠿⠿⢻⢛⠋⠛⠻⠛⠻⠛⡋⣸⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡄⢾⣿⣏⠿⣱⡝⣮⢳⡝⣧⢻⣜⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⢧⡻⣜⡳⣝⠾⡼⣹⠶⣭⢳⡝⣮⢳⣽⡞⠋⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠁⢰⠒⠊⠐⠒⠂⠀⢀⠀⢻⣾⡝⣯⢻⣿⣿⠤⡄⠀⠉⠉⠉⠉⠀⠀⠉⠀⠉⠉⠀⠈⠁⠀⠁⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠇⣹⣿⢎⡿⣱⢻⡜⣧⢻⣜⡳⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⡹⣎⠷⣭⢳⣭⢻⡵⣋⡷⣭⢳⣝⣮⢳⣿⡏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠸⣄⣀⣀⡀⠀⠀⠈⢆⠙⠛⠛⠾⠟⠟⠻⠁⡹⠀⠀⠀⠀⠀⠀⠀⣠⠤⠤⠤⠤⠤⠤⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠒⢰⣀⣀⣠⣆⣀⡀⣤⣀⣄⡀⠐⣆⢀⣄⣀⣽⣿⣹⢺⢵⣫⢞⡵⣫⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⡷⣹⢎⣷⡹⣎⣷⠞⠋⠙⠛⣯⣿⣿⣿⣿⣿⣾⣿⣿⣿⣽⣿⣿⣾⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢳⠄⠀⠀⠀⠉⠉⠀⠈⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⢰⡧⠀⠀⠀⠀⠀⠀⠀⣵⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⢰⣿⣿⣿⣿⣿⣿⡿⣿⠿⣞⠿⡿⣿⢻⢧⡻⣝⢧⣳⢏⡾⣼⣹⣺⣕⣯⣞⣵⣫⣞⣵⣫⣞⣵⣫⣞⣵⣫⣞⣵⣫⣶⣹⣿⣿⡖⠀⠀⠠⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢺⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠠⠤⠾⠁⠀⠀⠀⠀⠀⠀⠀⠘⠒⠤⠤⣀⠀⠀⠀⠀⠀⠀⠀⠻⢄⣉⡉⠛⠻⣿⣜⡳⣭⢻⡼⣫⠷⣭⠿⣮⡳⣝⣮⣷⠟⠉⠡⠯⠥⠀⠠⠩⠉⠡⠤⠅⠤⠤⠥⠫⠤⠭⠤⠥⠤⢄⠉⠉⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢺⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⢰⣿⣮⣳⣭⣳⣝⣣⣟⣼⣛⣶⣝⣮⣽⣿⡉⢇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣩⠆⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⢀⣀⣀⣀⡼⠇⠀⠀⠀⣀⣀⡄⣄⠀⠀⠀⢀⡤⠤⠴⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠦⠀⠉⠩⣀⠭⠅⠉⠉⠀⠤⠈⠈⠉⠁⠠⠤⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠋⠉⠉⠉⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⡛⠍⢫⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⣸⠅⠀⠀⠀⠀⠀⠀⣠⣿⣿⣿⡿⠄⠀⠀⢸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣹⠂⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⡌⣀⡞⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⣽⠃⠀⠀⠀⠀⠀⠀⠈⠛⣿⡿⠟⠂⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠤⠤⠤⠤⠴⠤⠴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⣶⣶⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢮⠀⠀⠀⠀⠀⠀⠀⢈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠒⣾⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣾⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡷⠂⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠘⠶⠦⠤⣄⠀⠀⠀⠀⠀⠀⠀⢀⠤⠖⠒⠛⠀⠀⠀⠀⠀⠀⠀⠀⢠⠤⠤⠴⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣶⣶⣿⡤⠀⠀⠀⠀⠀⠊⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⣿⠉⠈⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠉⠉⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣖⡂⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢹⡇⠀⠀⠀⠀⠀⠀⢾⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣯⡂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⢀⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⢄⣀⡤⠤⡞⠁⠀⠀⣠⠶⠲⠒⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣐⣶⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠒⠛⠋⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡟⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠉⠀⣹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠘⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⣼⠀⠀⠀⠀⠀⠀⠀⣼⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠙⠓⠒⠆⢦⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠉⠑⠀⠀⠀⠀⢶⣶⣶⣷⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠀⠁⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⢼⡆⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢻⣿⡿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⢰⡤⠆⠦⠾⠁⠀⠀⣺⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠒⢶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠻⡆⠀⠀⠀⠀⠀⠀⢻⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠙⠣⠤⠴⠖⠢⠤⠴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠒⠒⠚⠒⠚⠛⠒⠒⠒⠒⠒⠛⠓⠒⠉⠉⠉⠑⠒⠈⠙⠓⠐⠘⠋⠉⠉⢱⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡞⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣇⡀⠀⠀⠀⢀⠀⠀⠀⠀⣀⣨⡧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠉⠈⠉⠉⠉⠁⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀''', 
            'map1': ''

    ]
    inventory = []
    game_mode = "field"
    player_alive = True

    # Basic demo map content (walls, chest, npc, door)
    # Keep comments; minimal content without ASCII art
    for x in range(-5, 6):
        setup_tile(tiles, "wall", x, -3)
        setup_tile(tiles, "wall", x, 3)
    for y in range(-2, 3):
        setup_tile(tiles, "wall", -6, y)
        setup_tile(tiles, "wall", 6, y)
    setup_tile(tiles, "chest", 0, 0)
    setup_tile(tiles, "NPC", 2, 0)
    setup_tile(tiles, "door", -5, 0)

    # Audio setup
    this_dir = os.path.dirname(os.path.abspath(__file__))
    requested = {
        "battle": "Organization Battle.wav",
        "town": "Twilight Town.wav",
        "destiny": "Destiny Islands.wav",
        "final1": "KH-CoM Final Battle1.wav",
        "final2": "KH-CoM Final Battle2.wav"
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

    # === START MENU ===
    try:
        choice = start_menu()
    except KeyboardInterrupt:
        print("Goodbye.")
        return

    if choice == 0:  # Start New Game
        print("Starting new game...")
    elif choice == 1:  # Load Saved Game
        p, inv, gm, tl = load_game(controller)
        if p is None:
            print("No save file found. Starting new game instead.")
        else:
            player_stats, inventory, game_mode, tiles = p, inv, gm, tl
            print("Loaded previous save file.")
    elif choice == 2:  # MP3 Player
        mp3_player_menu(controller)
    elif choice == 3:  # Quit
        print("Goodbye!")
        return

    # Command interface (optional, for debugging music and save/load)
    print("Commands: play <name>, pause, resume, stop, list, quit, next, prev, save, load, status, mp3")
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

        elif op == "play3" and arg:
            controller.play3(arg)
        elif op == "pause3":
            controller.pause3()
        elif op == "resume3":
            controller.resume3()
        elif op == "stop3":
            controller.stop3()
        elif op == "next3":
            controller.next3()
        elif op == "prev3":
            controller.prev3()

        elif op == "status":
            controller.status()
        elif op == "list":
            controller.list_tracks()
        elif op == "quit":
            controller.stop(); controller.stop1(); controller.stop2(); controller.stop3()
            break
        elif op == "save":
            save_game(player_stats, inventory, game_mode, tiles, controller)
        elif op == "load":
            p, inv, gm, tl = load_game(controller)
            if p is not None:
                player_stats, inventory, game_mode, tiles = p, inv, gm, tl
        elif op == "mp3":
            mp3_player_menu(controller)
        else:
            print("Unknown command.")

    # Main game run
    while True:
        if game_mode == "field":
            try:
                player_stats, inventory, tiles, game_mode = field_mode(player_stats, inventory, tiles, controller)
            except SystemExit as e:
                if str(e) == "ReturnToTitle":
                    print("Returning to title...")
                    return
                else:
                    raise

        elif game_mode == "battle":
            player_stats, inventory, game_mode = battle_mode(player_stats, inventory, controller)

        elif game_mode == "end game":
            print("Thank you for playing!")
            break

if __name__ == "__main__":
    main()
