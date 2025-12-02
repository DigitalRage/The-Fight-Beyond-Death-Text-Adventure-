# BB 1st Final Project, The Fight Beyond Death: Text Adventure

#SETUP
#- Import libraries: os, time, winsound, mscrt, save (My Save File)
import os, time, winsound, msvcrt, json

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
player_stats = {'defence': 10, 'spirit': 10, 'attack': 10, 'magic': 10, 'mana': 50, 'HP': 100, 'EXP': 0, 'Level': 1, 'Munny': 0}
game_mode = "field"
player_alive = True
tiles = []
music = {}
current_track = None
track_index = 0
pause_state = False

#LEVEL UP FUNCTION
#- Input: level number
#- Multiply all stats by 1.2
#- Return new stats
#- Display "Level Up!" message
def level_up(level):
    global player_stats
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
#
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
#
#PLAYER DODGE FUNCTION
#- Input: dodge button press
#- When pressed:
#  - Move player quickly 2 tiles in chosen direction
#  - Set "invulnerable" flag for short duration (e.g. 0.5 seconds)
#  - If enemy attack occurs during invulnerable window then no damage taken
#  - Show dodge animation
#
#BATTLE LOOP
#- Maintain list of active enemies
#- For each frame in battle mode:
#  - Player input: move, attack, dodge, item
#  - For each enemy in list:
#    - Run Enemy Update Loop
#    - Check collisions with player
#  - If all enemies HP <= 0 then battle ends
#  - If player HP <= 0 then game over
#
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

this_dir = os.path.dirname(os.path.abspath(__file__))
tracks = {
    "battle": os.path.join(this_dir, "Organization Battle.wav"),
    "town": os.path.join(this_dir, "Twilight Town.wav"),
    "destiny": os.path.join(this_dir, "Destiny Islands.wav")
}

# Verify files exist
for name, path in tracks.items():
    if not os.path.exists(path):
        print(f"Missing file for {name}: {path}")

print('Commands: "play <name>", "pause", "track", "end"')

track_names = list(tracks.keys())
current_track = None

def play_track(name):
    global current_track
    current_track = name
    winsound.PlaySound(tracks[current_track],
                       winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    print(f"Playing {current_track}...")

while True:
    command = input("> ").strip().lower()

    if command.startswith("play"):
        parts = command.split()
        if len(parts) == 2 and parts[1] in tracks:
            play_track(parts[1])
        else:
            print("Available tracks:")
            for name in track_names:
                print(f"play {name}")

    elif command == "pause":
        winsound.PlaySound(None, winsound.SND_PURGE)
        print("Playback paused.")

    elif command == "track":
        print("Track mode: press = for next, - for previous, Backspace to exit")
        while True:
            if msvcrt.kbhit():  # check if a key was pressed
                key = msvcrt.getch()

                # decode to string if possible
                try:
                    char = key.decode('utf-8')
                except UnicodeDecodeError:
                    char = ''

                if char == '=':
                    if current_track:
                        idx = track_names.index(current_track)
                        new_idx = (idx + 1) % len(track_names)
                        play_track(track_names[new_idx])
                    else:
                        play_track(track_names[0])

                elif char == '-':
                    if current_track:
                        idx = track_names.index(current_track)
                        new_idx = (idx - 1) % len(track_names)
                        play_track(track_names[new_idx])
                    else:
                        play_track(track_names[0])

                elif key == b'\x08':  # Backspace key
                    print("Exiting track mode.")
                    break

    elif command == "end":
        winsound.PlaySound(None, winsound.SND_PURGE)
        print("Playback stopped. Goodbye!")
        break

    else:
        print("Unknown command. Try play <name>, pause, track, or end.")

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