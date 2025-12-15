import importlib, sys
sys.path.append(r"c:\Users\DigitalRage\Documents\The-Fight-Beyond-Death-Text-Adventure-")
import DigitalRage.main as m


def test_load_updates_player_and_inventory(monkeypatch):
    controller = object()
    player_stats = {'x': 1, 'y': 2, 'HP': 10, 'max_hp': 100}
    inventory = [{'name': 'potion', 'count': 1}]

    # fake load returns new player state and inventory
    def fake_load(ctrl):
        return ({'x': 5, 'y': 6, 'HP': 200, 'max_hp': 250}, [{'name': 'potion', 'count': 2}], 'field', [])

    monkeypatch.setattr(m, 'load_game', fake_load)

    # simulate pressing down 5 times to get to index 5 (Load), then Enter
    keys = []
    for _ in range(5):
        keys.extend([b'\xe0', b'P'])
    keys.append(b'\r')

    monkeypatch.setattr(m.msvcrt, 'getch', lambda: keys.pop(0) if keys else b'\x1b')

    # run menu
    m.in_game_menu(player_stats, inventory, controller)

    # assert player_stats updated in-place
    assert player_stats['x'] == 5
    assert player_stats['y'] == 6
    assert player_stats['HP'] == 200
    # inventory replaced
    assert inventory == [{'name': 'potion', 'count': 2}]
