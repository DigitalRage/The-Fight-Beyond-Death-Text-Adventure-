# BB 1st Final Project, The Fight Beyond Death: Text Adventure

#SETUP
#- Import libraries: os, time, winsound, mscrt, save (My Save File), music controller (music playback)
import os, time, msvcrt, json
from music_controller import MusicController

SAVE_FILE = "save.json"

def save_game():
    game_data = {
        "player_stats": player_stats,
        "inventory": inventory,
        "game_mode": game_mode,
        "tiles": tiles,
        "current_track": controller.current_track
    }
    try:
        with open(SAVE_FILE, "w") as file:
            json.dump(game_data, file, indent=4)
        print("Game saved successfully.")
    except Exception as error:
        print("Error saving game:", error)


def load_game():
    global player_stats, inventory, game_mode, tiles
    try:
        with open(SAVE_FILE, "r") as file:
            game_data = json.load(file)
        player_stats = game_data.get("player_stats", player_stats)
        inventory = game_data.get("inventory", [])
        game_mode = game_data.get("game_mode", "field")
        tiles = game_data.get("tiles", [])
        track = game_data.get("current_track")
        if track:
            controller.play(track)
        print("Game loaded successfully.")
    except FileNotFoundError:
        print("No save file found.")
    except Exception as error:
        print("Error loading game:", error)


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

def mp3_player_menu():
    track_names = list(tracks.keys())
    selected = 0

    while True:
        print("\n=== MP3 Player ===")
        for i, name in enumerate(track_names):
            if i == selected:
                print(f"> {name}")
            else:
                print(f"  {name}")
        print("Press Enter to play, Esc to exit MP3 Player.")

        key = msvcrt.getch()

        if key == b'\xe0':  # arrow keys
            key2 = msvcrt.getch()
            if key2 == b'H':  # Up
                selected = (selected - 1) % len(track_names)
            elif key2 == b'P':  # Down
                selected = (selected + 1) % len(track_names)
        elif key == b'\r':  # Enter
            controller.play(track_names[selected])
        elif key == b'\x1b':  # Esc key
            print("Closing MP3 Player...")
            break


#LEVEL UP FUNCTION
#- Input: level number
#- Multiply all stats by 1.2
#- Return new stats
#- Display "Level Up!" message
def level_up(level):
    player_stats['defence'] = int(player_stats['defence'] * 1.2)
    player_stats['spirit'] = int(player_stats['spirit'] * 1.2)
    player_stats['attack'] = int(player_stats['attack'] * 1.2)
    player_stats['magic'] = int(player_stats['magic'] * 1.2)
    player_stats['mana'] = int(player_stats['mana'] * 1.2)
    player_stats['HP'] = int(player_stats['HP'] * 1.2)
    player_stats['Level'] += 1
    print("Level Up! You are now level", player_stats['Level'])
    return player_stats
#TILE SETUP FUNCTION
#- Input: tile id, x coordinate, y coordinate
#- Create a tile object with id, x, y
#- Place tile object into Tiles list
#- When map is displayed, draw each tile at its x and y coordinates

def setup_tile(tile_id, x, y):
    tile = {'id': tile_id, 'x': x, 'y': y}
    tiles.append(tile)

#TILE ID FUNCTION
#- Input: player position (x, y)
#- Check which tile in Tiles list matches the position
#- Return tile id
#- If no tile found then return "empty"

def get_tile_id(x, y):
    for tile in tiles:
        if tile['x'] == x and tile['y'] == y:
            return tile['id']
    return "empty"

#COLLISION FUNCTION
#- Input: desired player position (x, y)
#- Use Tile ID function to check tile at that position
#- If tile id is "wall" or "blocked" then prevent movement
#- Else allow movement

def check_collision(x, y):
    tile_id = get_tile_id(x, y)
    if tile_id in ["wall", "blocked"]:
        return False
    return True

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
game_mode = "field"
player_alive = True
tiles = []
inventory = []
pause_state = False

# === START MENU ===

def start_menu():
    options = ["Start New Game", "Load Saved Game", "MP3 Player", "Quit"]
    selected = 0

    while True:
        print("\n=== The Fight Beyond Death ===")
        for i, option in enumerate(options):
            if i == selected:
                print(f"> {option}")  # highlight selected
            else:
                print(f"  {option}")

        key = msvcrt.getch()

        if key == b'\xe0':  # arrow keys
            key2 = msvcrt.getch()
            if key2 == b'H':  # Up
                selected = (selected - 1) % len(options)
            elif key2 == b'P':  # Down
                selected = (selected + 1) % len(options)
        elif key == b'\r':  # Enter
            return selected

choice = start_menu()

choice = start_menu()

if choice == 0:  # Start New Game
    print("Starting new game...")
    # reset stats, inventory, etc.
elif choice == 1:  # Load Saved Game
    try:
        load_game()
        print("Loaded previous save file.")
    except FileNotFoundError:
        print("No save file found. Starting new game instead.")
elif choice == 2:  # MP3 Player
    print("Opening MP3 Player...")
    mp3_player_menu()
elif choice == 3:  # Quit
    print("Goodbye!")
    exit()



this_dir = os.path.dirname(os.path.abspath(__file__))

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

print("Commands: play <name>, pause, resume, stop, list, quit, next, prev, save, load")
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
        save_game()          # auto-save on quit
        controller.stop()
        break
    elif op == "next":
        controller.next_track()
    elif op == "prev":
        controller.prev_track()
    elif op == "save":
        save_game()
    elif op == "load":
        load_game()
    else:
        print("Unknown command.")

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

while game_mode == "field" and player_alive:
    if pause_state:
        print("Game Paused. Press pause button again to resume.")
        while pause_state:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'p':  # assuming 'p' is the pause button
                    pause_state = False
                    print("Resuming game.")
    else:
        if msvcrt.kbhit():
            key = msvcrt.getch()

            # Movement keys
            if key == b'\xe0':  # arrow keys prefix
                key2 = msvcrt.getch()  # get the actual arrow key
                if key == b'w' or key2 == b'H':  # move up
                    new_x, new_y = player_stats['x'], player_stats['y'] - 1
                    if check_collision(new_x, new_y):
                        player_stats['y'] -= 1
                elif key == b's' or key2 == b'P':  # move down
                    new_x, new_y = player_stats['x'], player_stats['y'] + 1
                    if check_collision(new_x, new_y):
                        player_stats['y'] += 1
                elif key == b'a' or key2 == b'K':  # move left
                    new_x, new_y = player_stats['x'] - 1, player_stats['y']
                    if check_collision(new_x, new_y):
                        player_stats['x'] -= 1
                elif key == b'd' or key2 == b'M':  # move right
                    new_x, new_y = player_stats['x'] + 1, player_stats['y']
                    if check_collision(new_x, new_y):
                        player_stats['x'] += 1

            # Interaction key
            elif key == b'i':
                tile_id = get_tile_id(player_stats['x'], player_stats['y'])
                if tile_id == "NPC":
                    print("Starting dialogue with NPC...")
                elif tile_id == "chest":
                    print("Opening chest and adding item to inventory...")
                elif tile_id == "door":
                    print("Transitioning to new map...")

            # Music switching keys
            elif key == b'=':  # next track
                controller.next_track()
            elif key == b'-':  # previous track
                controller.prev_track()

                    
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

def enemy_update(enemy, player):
    if enemy['HP'] <= 0:
        print(f"{enemy['name']} has died.")
        # Drop rewards here
    else:
        distance = ((enemy['x'] - player['x']) ** 2 + (enemy['y'] - player['y']) ** 2) ** 0.5
        if distance > enemy['aggro_range']:
            enemy['state'] = 'idle'
        else:
            enemy['state'] = 'chasing'

        if enemy['state'] == 'chasing':
            # Move toward player
            if enemy['x'] < player['x']:
                enemy['x'] += enemy['speed']
            elif enemy['x'] > player['x']:
                enemy['x'] -= enemy['speed']
            if enemy['y'] < player['y']:
                enemy['y'] += enemy['speed']
            elif enemy['y'] > player['y']:
                enemy['y'] -= enemy['speed']

            if distance <= 1:  # Assuming 1 unit is close enough to attack
                enemy['state'] = 'attacking'

        if enemy['state'] == 'attacking':
            print(f"{enemy['name']} is attacking!")
            # Handle attack logic here
            # Reset to chasing after cooldown

#PLAYER DODGE FUNCTION
#- Input: dodge button press
#- When pressed:
#  - Move player quickly 2 tiles in chosen direction
#  - Set "invulnerable" flag for short duration (e.g. 0.5 seconds)
#  - If enemy attack occurs during invulnerable window then no damage taken
#  - Show dodge animation

def player_dodge(direction):
    dodge_distance = 2
    invulnerable_duration = 0.5
    if direction == 'up':
        player_stats['y'] -= dodge_distance
    elif direction == 'down':
        player_stats['y'] += dodge_distance
    elif direction == 'left':
        player_stats['x'] -= dodge_distance
    elif direction == 'right':
        player_stats['x'] += dodge_distance
    player_stats['invulnerable'] = True
    print("Player dodged!")
    time.sleep(invulnerable_duration)
    player_stats['invulnerable'] = False
    print("Player is no longer invulnerable.")

#BATTLE LOOP
#- Maintain list of active enemies
#- For each frame in battle mode:
#  - Player input: move, attack, dodge, item
#  - For each enemy in list:
#    - Run Enemy Update Loop
#    - Check collisions with player
#  - If all enemies HP <= 0 then battle ends
#  - If player HP <= 0 then game over



#REWARD / EXP SYSTEM
#- When enemy dies:
#  - Add EXP to player total
#  - Add Munny to player inventory
#  - If enemy has item drop:
#    - Add item to player inventory
#- After battle:
#  - Check if player EXP >= level threshold
#  - If yes then call Level Up Function
#
#SAVE / LOAD SYSTEM
#- Save function:
#  - Store player stats, inventory, current map, position, and track index
#  - Write data to save file
#- Load function:
#  - Read data from save file
#  - Restore player stats, inventory, current map, position, and track index
#  - Resume game from saved state
#- Menu option:
#  - "Save" calls Save function
#  - "Load" calls Load function
#
#UI SYSTEM (HP/MP BARS)
#- Player UI:
#  - Display HP bar above player sprite
#  - Display MP bar below HP bar
#  - Update bars every frame based on current values
#- Enemy UI:
#  - Display HP bar above each enemy sprite
#  - Update bar every frame based on enemy HP
#- Pause overlay:
#  - When pause state is true, show "Game Paused" overlay
#  - Hide overlay when pause state is false
#
#CAMERA / VIEWPORT SYSTEM
#- Camera follows player position
#- Field mode:
#  - Center camera on player
#  - Scroll map as player moves
#- Battle mode:
#  - Center camera on battle arena
#  - Keep all enemies and player visible
#
#BATTLE TRANSITION SYSTEM
#- When random encounter triggered:
#  - Fade out field screen
#  - Load battle arena
#  - Fade in battle screen
#  - Play battle background music
#- When battle ends:
#  - Fade out battle screen
#  - Load field map at player position
#  - Fade in field screen
#  - Resume field background music
# Build absolute paths to all files

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
#
#GAME LOOP
#- Start in field mode
#- While game is running:
#  - If mode is "field" then run field mode loop
#  - Else if mode is "battle" then run battle mode loop
#  - Else if mode is "end game" then end game