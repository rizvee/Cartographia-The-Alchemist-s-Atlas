from .models import MapGrid, ElementalSeed, PlayerHand

# Initialize a default game map
DEFAULT_MAP_WIDTH = 10
DEFAULT_MAP_HEIGHT = 10
game_map = MapGrid(DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT)

# Initialize player's hand
player_hand = PlayerHand()

# Add initial seeds to player's hand
default_seeds = [
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Fire", description="A seed of conflagration.") # Adding a different one for variety
]

# Initialize player's hand with a copy of default_seeds to avoid modifying the list during iteration if add_seed is changed
# However, current add_seed just appends to self.seeds, so direct iteration is fine.
for seed in default_seeds:
    player_hand.add_seed(seed)


def apply_element_to_tile(current_game_map, x, y, element_name):
    """
    Applies an element to a tile on the map, potentially transforming its terrain.

    Args:
        current_game_map (MapGrid): The game map instance.
        x (int): The x-coordinate of the tile.
        y (int): The y-coordinate of the tile.
        element_name (str): The name of the element being applied (e.g., "Water", "Fire").

    Returns:
        bool: True if a transformation occurred, False otherwise.
    """
    tile = current_game_map.get_tile(x, y)
    if not tile:
        print(f"Error: No tile at coordinates ({x},{y}).")
        return False

    original_terrain = tile.terrain_type
    transformed = False

    print(f"\nAttempting to apply '{element_name}' to tile ({x},{y}) with terrain '{original_terrain}'...")

    if element_name == "Water":
        if original_terrain == "Earth":
            tile.terrain_type = "River"
            transformed = True
        elif original_terrain == "Empty":
            tile.terrain_type = "Shallow Water"
            transformed = True
        elif original_terrain == "Fire Patch": # Example of interaction: Water puts out Fire Patch
            tile.terrain_type = "Wet Ground"
            transformed = True
    elif element_name == "Fire":
        if original_terrain == "Earth":
            tile.terrain_type = "Scorched Earth"
            transformed = True
        elif original_terrain == "Empty": # Fire on empty might create a small fire patch
            tile.terrain_type = "Fire Patch"
            transformed = True
        elif original_terrain == "Forest": # Fire on Forest
            tile.terrain_type = "Burning Forest"
            transformed = True
    elif element_name == "Earth":
        if original_terrain == "Empty":
            tile.terrain_type = "Plain" # Earth on Empty creates a Plain
            transformed = True
        elif original_terrain == "Shallow Water": # Earth on Shallow Water fills it in
            tile.terrain_type = "Earth"
            transformed = True
    # Add more elements and rules as needed:
    # elif element_name == "Wind":
    #     if original_terrain == "Fire Patch":
    #         tile.terrain_type = "Scattered Embers" # Wind spreads fire
    #         transformed = True

    if transformed:
        print(f"Success! Tile ({x},{y}) transformed from '{original_terrain}' to '{tile.terrain_type}'.")
    else:
        print(f"No transformation rule for '{element_name}' on '{original_terrain}' at ({x},{y}). Tile remains '{original_terrain}'.")

    return transformed


def get_map_details():
    """Returns basic details about the game map."""
    return {
        "width": game_map.width,
        "height": game_map.height,
        "tiles": [[tile.terrain_type for tile in row] for row in game_map.grid]
    }

def get_player_hand_details():
    """Returns the contents of the player's hand."""
    return {
        "seeds": player_hand.get_hand_contents(),
        "count": len(player_hand.seeds)
    }

# Example of how to access a tile and hand (optional, for testing)
# if __name__ == "__main__":
#     print(f"Map initialized: {game_map}")
#     tile_at_0_0 = game_map.get_tile(0, 0)
#     print(f"Tile at (0,0): {tile_at_0_0}")
#     print(get_map_details())
#
#     print(f"\nPlayer Hand Initialized: {player_hand}")
#     print(get_player_hand_details())
#     player_hand.remove_seed("Earth")
#     print(get_player_hand_details())
#     player_hand.remove_seed("Air") # Try removing a non-existent seed
#     print(get_player_hand_details())
