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


def apply_element_to_tile(current_game_map, x, y, element_name, strength=25):
    """
    Applies an element to a tile, increasing its saturation and then updating its terrain type
    based on the new saturation levels.

    Args:
        current_game_map (MapGrid): The game map instance.
        x (int): The x-coordinate of the tile.
        y (int): The y-coordinate of the tile.
        element_name (str): The name of the element being applied (e.g., "Water", "Fire").
        strength (int): The amount by which to increase the element's saturation.

    Returns:
        bool: True if the terrain type changed as a result of updated saturation, False otherwise.
    """
    tile = current_game_map.get_tile(x, y)
    if not tile:
        print(f"Error: No tile at coordinates ({x},{y}). Cannot apply '{element_name}'.")
        return False

    if element_name not in tile.ALL_ELEMENTS:
        print(f"Warning: Element '{element_name}' is not a recognized element. Cannot apply to tile ({x},{y}).")
        return False

    print(f"\nApplying '{element_name}' (strength {strength}) to tile ({x},{y}). Initial state: {tile}")

    # Increase saturation of the applied element
    current_saturation = tile.elemental_saturation.get(element_name, 0)
    new_saturation = min(100, current_saturation + strength) # Cap at 100
    new_saturation = max(0, new_saturation) # Ensure >= 0 (though strength is positive here)
    tile.elemental_saturation[element_name] = new_saturation

    # Placeholder for normalization or reduction of other elements if a total cap is exceeded.
    # For now, we just cap individual elements.
    # Example: if sum(tile.elemental_saturation.values()) > MAX_TOTAL_SATURATION:
    #    normalize_saturations(tile)

    print(f"Saturation updated for '{element_name}' to {new_saturation} for primary tile ({x},{y}). Current saturations: {tile.elemental_saturation}")

    # Update terrain type based on new saturation for the primary tile
    primary_terrain_changed = tile.update_terrain_based_on_saturation()

    if primary_terrain_changed:
        print(f"Success! Primary tile ({x},{y}) terrain changed to '{tile.terrain_type}'.")
    else:
        print(f"Primary tile ({x},{y}) terrain remains '{tile.terrain_type}'.")

    # Elemental Influence "Echo" to Neighbors
    echo_strength = strength // 2 # Or a fixed value like 10, or min(10, strength // 2)
    if echo_strength > 0:
        neighbors = current_game_map.get_neighbors(x, y) # Using cardinal neighbors by default
        print(f"Applying echo of '{element_name}' (strength {echo_strength}) to {len(neighbors)} neighbors.")
        for i, neighbor_tile in enumerate(neighbors):
            # Need to find neighbor's coordinates to make print statements more informative,
            # but get_neighbors returns Tile objects directly. For now, use index.
            # To get coords, MapGrid would need to return (tile, nx, ny) or Tile stores its own coords.

            original_neighbor_terrain = neighbor_tile.terrain_type
            print(f"  Echo for neighbor {i+1}/{len(neighbors)} (current terrain: '{original_neighbor_terrain}', current saturation: {neighbor_tile.elemental_saturation.get(element_name,0)}).")

            neighbor_current_saturation = neighbor_tile.elemental_saturation.get(element_name, 0)
            neighbor_new_saturation = min(100, neighbor_current_saturation + echo_strength)
            neighbor_new_saturation = max(0, neighbor_new_saturation)
            neighbor_tile.elemental_saturation[element_name] = neighbor_new_saturation

            print(f"    Neighbor {i+1} saturation for '{element_name}' updated to {neighbor_new_saturation}.")

            neighbor_terrain_changed = neighbor_tile.update_terrain_based_on_saturation()
            if neighbor_terrain_changed:
                print(f"    Success! Neighbor {i+1} terrain changed to '{neighbor_tile.terrain_type}'.")
            else:
                print(f"    Neighbor {i+1} terrain remains '{original_neighbor_terrain}'.")
    else:
        print("Echo strength is 0, skipping neighbor effects.")

    return primary_terrain_changed


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
