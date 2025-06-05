from .game_logic import game_map, get_map_details, player_hand, get_player_hand_details, apply_element_to_tile
from .models import ElementalSeed # Import ElementalSeed

# Helper function to print a portion of the map for brevity
def print_map_section(current_game_map, start_x=0, start_y=0, width=5, height=5):
    print(f"Map Section (from {start_x},{start_y} for {width}x{height}):")
    for y in range(start_y, min(start_y + height, current_game_map.height)):
        row_str = []
        for x in range(start_x, min(start_x + width, current_game_map.width)):
            tile = current_game_map.get_tile(x,y)
            row_str.append(f"({x},{y}):{tile.terrain_type[:7]:<7}") # Print first 7 chars of terrain
        print(" | ".join(row_str))
    print("-" * 20)

def main():
    print("Cartographia Backend Initializing...")
    # Map Information
    print(f"\n--- Map Info ---")
    print(f"Game Map: {game_map}")
    print(f"Tile at (0,0): {game_map.get_tile(0,0)}")
    print(f"Tile at (9,9): {game_map.get_tile(9,9)}")
    print(f"Tile at (10,10): {game_map.get_tile(10,10)}") # Out of bounds

    map_details = get_map_details()
    print("\nMap Details from get_map_details():")
    print(f"  Width: {map_details['width']}")
    print(f"  Height: {map_details['height']}")
    print_map_section(game_map, 0, 0, 5, 5) # Print initial small section

    # Player Hand Information
    print(f"\n--- Player Hand Info ---")
    print(f"Initial Player Hand: {player_hand}")
    hand_details = get_player_hand_details()
    print(f"Initial Hand Details from get_player_hand_details():")
    print(f"  Seeds: {hand_details['seeds']}")
    print(f"  Count: {hand_details['count']}")

    print("\nTesting seed removal:")
    player_hand.remove_seed("Earth") # Should remove one Earth seed
    hand_details_after_remove = get_player_hand_details()
    print(f"Hand Details after removing 'Earth':")
    print(f"  Seeds: {hand_details_after_remove['seeds']}")
    print(f"  Count: {hand_details_after_remove['count']}")

    player_hand.remove_seed("Water") # Should remove one Water seed
    player_hand.remove_seed("Fire") # Should remove one Fire seed

    print("\nTesting removal of a non-existent seed:")
    player_hand.remove_seed("Air") # Should not find 'Air'
    hand_details_after_failed_remove = get_player_hand_details()
    print(f"Hand Details after attempting to remove 'Air':")
    print(f"  Seeds: {hand_details_after_failed_remove['seeds']}")
    print(f"  Count: {hand_details_after_failed_remove['count']}")

    print("\nTesting adding a new seed:")
    # new_seed variable was assigned the result of add_seed which is None (it prints internally).
    # We should just call add_seed.
    player_hand.add_seed(ElementalSeed(name="Wind", description="A gusty seed."))
    hand_details_after_add = get_player_hand_details()
    print(f"Hand Details after adding 'Wind':")
    print(f"  Seeds: {hand_details_after_add['seeds']}")
    print(f"  Count: {hand_details_after_add['count']}")

    # Terrain Transformation Tests
    print(f"\n--- Terrain Transformation Tests ---")

    # Setup: Change some initial tiles for testing
    print("\nSetting up initial tile terrains for transformation tests...")
    tile_0_0 = game_map.get_tile(0,0)
    if tile_0_0: tile_0_0.terrain_type = "Earth"
    tile_0_1 = game_map.get_tile(0,1)
    if tile_0_1: tile_0_1.terrain_type = "Earth"
    tile_1_0 = game_map.get_tile(1,0)
    if tile_1_0: tile_1_0.terrain_type = "Empty"
    tile_1_1 = game_map.get_tile(1,1)
    if tile_1_1: tile_1_1.terrain_type = "Forest" # For fire testing
    tile_2_0 = game_map.get_tile(2,0)
    if tile_2_0: tile_2_0.terrain_type = "Shallow Water" # For earth testing

    print("Initial map state for transformations:")
    print_map_section(game_map, 0, 0, 3, 3)

    # Test cases for apply_element_to_tile
    # 1. Water on Earth -> River
    apply_element_to_tile(game_map, 0, 0, "Water")
    # 2. Fire on Earth -> Scorched Earth
    apply_element_to_tile(game_map, 0, 1, "Fire")
    # 3. Water on Empty -> Shallow Water
    apply_element_to_tile(game_map, 1, 0, "Water")
    # 4. Fire on Forest -> Burning Forest
    apply_element_to_tile(game_map, 1, 1, "Fire")
    # 5. Earth on Shallow Water -> Earth
    apply_element_to_tile(game_map, 2, 0, "Earth")
    # 6. No transformation: Earth on Earth
    apply_element_to_tile(game_map, 0, 1, "Earth") # Was Scorched Earth, try to turn to Earth (no rule)
    # 7. No transformation: Unknown element
    apply_element_to_tile(game_map, 0, 0, "Wind") # Was River, try Wind (no rule yet for Wind on River)
    # 8. Out of bounds
    apply_element_to_tile(game_map, 100, 100, "Water")
    # 9. Fire on Empty -> Fire Patch
    tile_2_1 = game_map.get_tile(2,1) # Ensure it's empty first
    if tile_2_1: tile_2_1.terrain_type = "Empty"
    apply_element_to_tile(game_map, 2, 1, "Fire")
    # 10. Water on Fire Patch -> Wet Ground
    apply_element_to_tile(game_map, 2, 1, "Water") # Now apply Water to the Fire Patch

    print("\nFinal map state after transformations:")
    print_map_section(game_map, 0, 0, 3, 3)

    # You can print the full map details if needed
    # final_map_details = get_map_details()
    # print("\nFull Final Map Details:")
    # print(f"  Width: {final_map_details['width']}")
    # print(f"  Height: {final_map_details['height']}")
    # for r_idx, row in enumerate(final_map_details['tiles']):
    #     print(f"  Row {r_idx}: {row}")

if __name__ == "__main__":
    main()
