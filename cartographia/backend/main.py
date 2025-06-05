from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .game_logic import game_map, get_map_details, player_hand, get_player_hand_details, apply_element_to_tile # game_map and player_hand are initialized in game_logic
from .models import ElementalSeed, Tile # Tile might be needed for request/response models later

# --- Pydantic Models for Request/Response ---

class ApplyElementRequest(BaseModel):
    x: int
    y: int
    element_name: str

# Create FastAPI app
app = FastAPI()

# Game state (game_map, player_hand) is initialized when game_logic is imported.
# More sophisticated startup via @app.on_event("startup") could be added later.

# --- API Endpoints ---

@app.get("/api/map_details")
async def api_get_map_details():
    """
    Returns the current state of the game map including tile terrain types.
    """
    return get_map_details()

@app.post("/api/apply_element")
async def api_apply_element(request: ApplyElementRequest):
    """
    Applies an element to a specific tile and returns the updated map details.
    """
    print(f"Received request to apply '{request.element_name}' to ({request.x},{request.y})") # Server-side log

    # Validate element name if necessary (could also be done in ElementalSeed or game_logic)
    # For now, assume apply_element_to_tile handles unknown elements gracefully.

    # Call the game logic function
    # The `apply_element_to_tile` function in game_logic already has a default strength.
    # We can expose 'strength' in ApplyElementRequest later if needed.
    transformation_occurred = apply_element_to_tile(
        current_game_map=game_map,
        x=request.x,
        y=request.y,
        element_name=request.element_name
    )

    # Log if transformation happened (optional)
    # print(f"Transformation occurred on primary tile: {transformation_occurred}")

    # Return the updated map details
    # This ensures the frontend gets the full current state after any changes (including echoes)
    return get_map_details()


# The existing main() function and its test code are below.
# They can be kept for command-line testing or eventually removed/refactored.
# For FastAPI, they are not directly used unless called.

# Helper function to print a portion of the map for brevity
def print_map_section(current_game_map, start_x=0, start_y=0, width=3, height=3): # Reduced default size
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

    print("\n--- Initial Tile Saturation Tests (from game_map created by MapGrid) ---")
    print(f"Default Tile from map (0,0): {game_map.get_tile(0,0)}") # Should be Empty, all zero saturation
    print(f"Default Tile from map (1,1): {game_map.get_tile(1,1)}") # Should be Empty, all zero saturation

    print("\n--- Custom Tile Initialization Tests ---")
    earth_tile = Tile(terrain_type="Earth", elevation=0) # Default elevation
    print(f"Custom Earth Tile: {earth_tile}")

    water_tile = Tile(terrain_type="Water", elevation=-1) # Example with non-default elevation
    print(f"Custom Water Tile: {water_tile}")

    forest_tile = Tile(terrain_type="Forest", elevation=1)
    print(f"Custom Forest Tile: {forest_tile}")

    unknown_terrain_tile = Tile(terrain_type="MysticZone") # Default elevation
    print(f"Custom Unknown Terrain Tile: {unknown_terrain_tile}")

    custom_saturation_tile = Tile(terrain_type="Custom", initial_saturation={'Fire': 150, 'Air': 50, 'Earth': 0}, elevation=2)
    print(f"Custom Saturation Tile: {custom_saturation_tile}")

    high_elevation_tile = Tile(terrain_type="Empty", elevation=5)
    print(f"High Elevation Tile: {high_elevation_tile}")

    # game_map.grid[2][2] = Tile(terrain_type="Forest", elevation=1) # Example of placing a pre-defined tile
    # print(f"Manually placed Forest Tile in map at (2,2): {game_map.get_tile(2,2)}")


    print_map_section(game_map, 0, 0, 3, 3) # Print initial small section of the main game_map

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
    print(f"\n--- Terrain Transformation Tests (Saturation Driven) ---")

    # All tiles start as "Empty" with 0 saturation.
    # We will apply elements and observe changes.

    print("\nInitial map state for new transformation tests:")
    print_map_section(game_map, 0, 0, 3, 3) # Show a small section

    # Test Case 1: Water saturation leading to Shallow Water
    print("\n--- Test Case 1: Water -> Shallow Water ---")
    print(f"Initial Tile (0,0): {game_map.get_tile(0,0)}")
    apply_element_to_tile(game_map, 0, 0, "Water", strength=30) # Water = 30
    print(f"Tile (0,0) after 1st Water: {game_map.get_tile(0,0)}")
    apply_element_to_tile(game_map, 0, 0, "Water", strength=35) # Water = 30+35 = 65 -> Shallow Water
    print(f"Tile (0,0) after 2nd Water: {game_map.get_tile(0,0)}")
    apply_element_to_tile(game_map, 0, 0, "Water", strength=50) # Water = 100 (capped)
    print(f"Tile (0,0) after 3rd Water (capped): {game_map.get_tile(0,0)}")


    # Test Case 2: Earth saturation leading to Earth
    print("\n--- Test Case 2: Earth -> Earth ---")
    print(f"Initial Tile (0,1): {game_map.get_tile(0,1)}")
    apply_element_to_tile(game_map, 0, 1, "Earth", strength=70) # Earth = 70 -> Earth
    print(f"Tile (0,1) after Earth: {game_map.get_tile(0,1)}")


    # Test Case 3: Fire saturation leading to Scorched Earth
    print("\n--- Test Case 3: Fire -> Scorched Earth ---")
    print(f"Initial Tile (1,0): {game_map.get_tile(1,0)}")
    apply_element_to_tile(game_map, 1, 0, "Fire", strength=65) # Fire = 65 -> Scorched Earth
    print(f"Tile (1,0) after Fire: {game_map.get_tile(1,0)}")


    # Test Case 4: Water + Earth leading to Mud
    print("\n--- Test Case 4: Water + Earth -> Mud ---")
    print(f"Initial Tile (1,1): {game_map.get_tile(1,1)}")
    apply_element_to_tile(game_map, 1, 1, "Water", strength=45) # Water = 45
    print(f"Tile (1,1) after Water: {game_map.get_tile(1,1)}")
    apply_element_to_tile(game_map, 1, 1, "Earth", strength=45) # Earth = 45. Water=45, Earth=45 -> Mud
    print(f"Tile (1,1) after Earth: {game_map.get_tile(1,1)}")
    # What if Water increases further? Rule: Shallow Water if Water > 60
    apply_element_to_tile(game_map, 1, 1, "Water", strength=20) # Water = 65, Earth = 45. Water > 60 -> Shallow Water
    print(f"Tile (1,1) after more Water: {game_map.get_tile(1,1)}")


    # Test Case 5: Applying an unknown element
    print("\n--- Test Case 5: Unknown element ---")
    apply_element_to_tile(game_map, 2, 0, "Mystic", strength=50)
    print(f"Tile (2,0) after Mystic element: {game_map.get_tile(2,0)}")


    # Test Case 6: Applying to out-of-bounds tile
    print("\n--- Test Case 6: Out of bounds ---")
    apply_element_to_tile(game_map, 100, 100, "Water")


    # Test Case 7: Element that doesn't meet threshold
    print("\n--- Test Case 7: Element below threshold ---")
    print(f"Initial Tile (2,1): {game_map.get_tile(2,1)}")
    apply_element_to_tile(game_map, 2, 1, "Fire", strength=30) # Fire = 30 (no change from Empty)
    print(f"Tile (2,1) after low Fire: {game_map.get_tile(2,1)}")


    print("\nFinal map state after new transformation tests:")
    print_map_section(game_map, 0, 0, 3, 3)

    # Detailed look at a few specific tiles
    print("\n--- Detailed final states for specific tiles ---")
    print(f"Tile (0,0) final: {game_map.get_tile(0,0)}") # Expected: Shallow Water, Water=100
    print(f"Tile (0,1) final: {game_map.get_tile(0,1)}") # Expected: Earth, Earth=70
    print(f"Tile (1,0) final: {game_map.get_tile(1,0)}") # Expected: Scorched Earth, Fire=65
    print(f"Tile (1,1) final: {game_map.get_tile(1,1)}") # Expected: Shallow Water, Water=65, Earth=45
    print(f"Tile (2,1) final: {game_map.get_tile(2,1)}")


    # --- Elevation and Mountain Tests ---
    print(f"\n--- Elevation and Mountain Terrain Tests ---")

    # Test Case E1: Earth > 70 and elevation > 2 -> Mountain
    print("\n--- Test Case E1: Earth for Mountain ---")
    # Initialize a tile with high elevation, then apply Earth
    game_map.grid[2][2] = Tile(terrain_type="Empty", elevation=3) # Tile at (2,2) with elevation 3
    print(f"Initial Tile (2,2) for Mountain Test: {game_map.get_tile(2,2)}")
    apply_element_to_tile(game_map, 2, 2, "Earth", strength=75) # Earth = 75
    print(f"Tile (2,2) after Earth (75) application: {game_map.get_tile(2,2)}") # Expected: Mountain, Elev=3, Earth=75

    # Test Case E2: Earth > 60 and elevation <= 2 -> Earth (not Mountain)
    print("\n--- Test Case E2: Earth for Standard Earth (low elevation) ---")
    # Need to use a tile not affected by previous echoes, or reset it.
    # Tile (0,2) was affected by echo from (0,1) [Earth 35] and (1,2) [Water 22] in previous tests.
    # Let's use a fresh tile or reset one. (2,0) was affected by Fire echo.
    # Let's use game_map.grid[0][2] and ensure it's reset.
    game_map.grid[0][2] = Tile(terrain_type="Empty", elevation=1)
    print(f"Initial Tile (0,2) for Earth Test: {game_map.get_tile(0,2)}")
    apply_element_to_tile(game_map, 0, 2, "Earth", strength=65)
    print(f"Tile (0,2) after Earth (65) application: {game_map.get_tile(0,2)}") # Expected: Earth, Elev=1, Earth=65

    # Test Case E3: Earth > 60 but just under Mountain threshold (e.g. Earth 65, elev 3) OR
    # Earth > 70 but elevation is not > 2
    print("\n--- Test Case E3: Earth, high elevation, but not enough saturation for Mountain ---")
    game_map.grid[1][2] = Tile(terrain_type="Empty", elevation=3)
    print(f"Initial Tile (1,2) for 'Almost Mountain' Test (low Earth): {game_map.get_tile(1,2)}")
    apply_element_to_tile(game_map, 1, 2, "Earth", strength=65) # Earth=65, Elev=3. Earth > 60 but not > 70 for Mountain.
                                                                # And elev > 2 so not "Earth". Should remain Empty.
    print(f"Tile (1,2) after Earth (65), Elev 3: {game_map.get_tile(1,2)}")

    print("\n--- Test Case E4: Earth, high saturation, but not enough elevation for Mountain ---")
    # Tile (2,0) was Scorched Earth, Fire 32, Water 22, Elev 0 (default)
    game_map.grid[2][0] = Tile(terrain_type="Empty", elevation=1) # Reset with low elevation
    print(f"Initial Tile (2,0) for 'Almost Mountain' Test (low Elev): {game_map.get_tile(2,0)}")
    apply_element_to_tile(game_map, 2, 0, "Earth", strength=75) # Earth=75, Elev=1. Earth > 70, but Elev not > 2. Should be "Earth".
    print(f"Tile (2,0) after Earth (75), Elev 1: {game_map.get_tile(2,0)}")


    print(f"\n--- Elemental Echo Tests (with elevation) ---")
    # The echo tests will now run on a map where some tiles might have non-zero elevation.

    print("\nRe-initializing tiles around (1,1) for echo test (all elev 0)...")
    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            tile_x, tile_y = 1 + x_offset, 1 + y_offset
            # Ensure we don't overwrite tiles used in Elevation tests if they overlap
            if not ((tile_x == 2 and tile_y == 2) or \
                    (tile_x == 0 and tile_y == 2) or \
                    (tile_x == 1 and tile_y == 2) or \
                    (tile_x == 2 and tile_y == 0)):
                if game_map.get_tile(tile_x, tile_y):
                    game_map.grid[tile_y][tile_x] = Tile(terrain_type="Empty", elevation=0) # Explicitly set elev 0

    print("Map state before echo test centered at (1,1) (most elev 0):")
    print_map_section(game_map, 0, 0, 3, 3)

    print("\n--- Test Case 8: Echo from applying strong Fire to (1,1) ---")
    # Target tile (1,1), neighbors are (0,1), (1,0), (1,2), (2,1)
    # Primary Fire strength 70. Echo strength = 70 // 2 = 35.
    # (1,1) should become Scorched Earth (Fire 70 > 60)
    # Neighbors should get Fire 35. This is not enough to change their terrain from Empty.
    print(f"Initial state of (1,1): {game_map.get_tile(1,1)}")
    print(f"Initial state of neighbor (0,1): {game_map.get_tile(0,1)}")
    print(f"Initial state of neighbor (1,0): {game_map.get_tile(1,0)}")

    apply_element_to_tile(game_map, 1, 1, "Fire", strength=70)

    print("\nMap state after echo test (Fire on (1,1)):")
    print_map_section(game_map, 0, 0, 3, 3)
    print(f"Tile (1,1) after: {game_map.get_tile(1,1)}")
    print(f"Neighbor (0,1) after: {game_map.get_tile(0,1)}") # Expected: Empty, Fire=35
    print(f"Neighbor (1,0) after: {game_map.get_tile(1,0)}") # Expected: Empty, Fire=35
    print(f"Neighbor (1,2) after: {game_map.get_tile(1,2)}") # Expected: Empty, Fire=35
    print(f"Neighbor (2,1) after: {game_map.get_tile(2,1)}") # Expected: Empty, Fire=35

    print("\n--- Test Case 9: Echo from applying Water to (0,0) (corner case) ---")
    # Target tile (0,0). Neighbors: (0,1), (1,0)
    # Primary Water strength 70. Echo strength 35.
    # (0,0) becomes Shallow Water. Neighbors get Water 35.
    # Re-initialize (0,0), (0,1), (1,0)
    game_map.grid[0][0] = Tile(terrain_type="Empty")
    game_map.grid[0][1] = Tile(terrain_type="Empty") # Neighbor
    game_map.grid[1][0] = Tile(terrain_type="Empty") # Neighbor

    print(f"Initial state of (0,0): {game_map.get_tile(0,0)}")
    apply_element_to_tile(game_map, 0, 0, "Water", strength=70)

    print("\nMap state after echo test (Water on (0,0)):")
    print_map_section(game_map, 0, 0, 2, 2) # Show relevant section
    print(f"Tile (0,0) after: {game_map.get_tile(0,0)}") # Expected: Shallow Water, Water=70
    print(f"Neighbor (0,1) after: {game_map.get_tile(0,1)}") # Expected: Empty, Water=35
    print(f"Neighbor (1,0) after: {game_map.get_tile(1,0)}") # Expected: Empty, Water=35
    if game_map.width > 1 and game_map.height > 1: # Check if (1,1) exists
      print(f"Tile (1,1) (not a direct neighbor) after: {game_map.get_tile(1,1)}") # Should be unchanged by this echo


    # --- Complex Biome Tests ---
    print(f"\n--- Complex Biome Tests ---")

    # Helper to create a tile and immediately check its terrain after saturation update.
    # This allows direct testing of update_terrain_based_on_saturation()
    def test_biome_rule(test_name, terrain_type, elevation, saturation_dict, expected_terrain):
        print(f"\n--- Test Biome: {test_name} ---")
        tile = Tile(terrain_type=terrain_type, initial_saturation=saturation_dict, elevation=elevation)
        print(f"Initial for {test_name}: {tile}")
        changed = tile.update_terrain_based_on_saturation() # Call method directly
        print(f"After update_terrain for {test_name}: {tile} (Changed: {changed})")
        if tile.terrain_type == expected_terrain:
            print(f"SUCCESS: {test_name} correctly became {expected_terrain}")
        else:
            print(f"FAILURE: {test_name} became {tile.terrain_type}, expected {expected_terrain}")
        return tile

    # B1: Volcano: Fire > 70, Earth > 50, elev > 1
    test_biome_rule("Volcano", "Empty", 2, {'Fire': 75, 'Earth': 55, 'Water': 0, 'Life': 0, 'Decay': 0, 'Air':0, 'Aether':0}, "Volcano")

    # B2: Jungle: Life > 60, Earth > 30, Water > 40, elev <= 1
    test_biome_rule("Jungle", "Empty", 1, {'Life': 65, 'Earth': 35, 'Water': 45, 'Fire':0,'Decay':0,'Air':0,'Aether':0}, "Jungle")

    # B3: Forest: Life > 60, Earth > 30, Water < 40, elev <= 2
    test_biome_rule("Forest", "Empty", 2, {'Life': 65, 'Earth': 35, 'Water': 15, 'Fire':0,'Decay':0,'Air':0,'Aether':0}, "Forest")
    test_biome_rule("Forest (not Jungle due to low water)", "Empty", 1, {'Life': 65, 'Earth': 35, 'Water': 15, 'Fire':0,'Decay':0,'Air':0,'Aether':0}, "Forest")


    # B4: Swamp: Water > 50, Decay > 30, Earth > 30, elev == 0
    test_biome_rule("Swamp", "Empty", 0, {'Water': 55, 'Decay': 35, 'Earth': 35, 'Life':0,'Fire':0,'Air':0,'Aether':0}, "Swamp")

    # B5: Desert: Earth > 70, Fire > 30, Water < 10, Life < 20, elev <=2
    test_biome_rule("Desert", "Empty", 1, {'Earth': 75, 'Fire': 35, 'Water': 5, 'Life': 10,'Decay':0,'Air':0,'Aether':0}, "Desert")
    test_biome_rule("Desert (not Mountain due to low elev)", "Mountain", 1, {'Earth': 75, 'Fire': 35, 'Water': 5, 'Life': 10,'Decay':0,'Air':0,'Aether':0}, "Desert")


    # B6: River: Water > 50, Earth > 20, elev == 0 (and not Swamp)
    test_biome_rule("River", "Empty", 0, {'Water': 55, 'Earth': 25, 'Decay': 10, 'Life':0,'Fire':0,'Air':0,'Aether':0}, "River")
    test_biome_rule("River (not Shallow Water due to elev 0 and earth)", "Shallow Water", 0, {'Water': 65, 'Earth': 25, 'Decay':0,'Life':0,'Fire':0,'Air':0,'Aether':0}, "River")


    # B7: Testing precedence and fallbacks
    # Should become Mountain, not Desert (elev > 2)
    test_biome_rule("Mountain (not Desert due to high elev)", "Empty", 3, {'Earth': 75, 'Fire': 35, 'Water': 5, 'Life': 10,'Decay':0,'Air':0,'Aether':0}, "Mountain")
    # Should become Forest, not Earth (Life condition met)
    test_biome_rule("Forest (not Earth)", "Earth", 1, {'Life': 65, 'Earth': 65, 'Water': 15, 'Fire':0,'Decay':0,'Air':0,'Aether':0}, "Forest")
    # Should become Earth (Life too low for Forest)
    test_biome_rule("Earth (Life too low for Forest)", "Forest", 1, {'Life': 15, 'Earth': 65, 'Water': 15, 'Fire':0,'Decay':0,'Air':0,'Aether':0}, "Earth")
    # Test Empty fallback
    test_biome_rule("Empty (all low)", "Mud", 0, {'Earth': 5, 'Water': 5, 'Fire': 5, 'Life': 5, 'Decay': 5, 'Air':0,'Aether':0}, "Empty")


    # Note: Existing tests for Mountain (E1), Earth (E2, E4), Scorched Earth (TC3), Mud (TC4), Shallow Water (TC1)
    # might need reviewing if their conditions are now met by a more specific biome rule placed earlier,
    # or if their own conditions were tightened.
    # For example, TC2 (Earth 65, elev 0) should still be Earth.
    # TC3 (Fire 65, elev 0) should still be Scorched Earth.
    # TC4 (Water 65, Earth 45, elev 0) was Shallow Water, now could be River. Let's check:
    # Water 65 > 50, Earth 45 > 20, elev 0. Yes, this will now be River. This is a good change.
    print("\n--- Verifying TC4 outcome with new rules (expect River) ---")
    # Re-run conditions for the old TC4's final state for tile (1,1)
    # Initial state for TC4 was: Tile(terrain='Empty', elev=0, saturation={'Earth': 35, 'Water': 0, 'Fire': 32, ...})
    # After Water 45: Earth 35, Water 45, Fire 32. (Empty)
    # After Earth 45: Earth 80, Water 45, Fire 32. (Earth)
    # After Water 20: Earth 80, Water 65, Fire 32. (Shallow Water before, now River)
    # This tile (1,1) will be affected by echoes from its neighbours in TC1,2,3.
    # Instead of tracing, let's directly test the final saturation state of TC4, (Earth 80, Water 65, Fire 32, elev 0)
    test_biome_rule("TC4 Check (Earth 80, Water 65, elev 0)", "Empty", 0,
                    {'Earth': 80, 'Water': 65, 'Fire': 32, 'Life':0, 'Decay':0, 'Air':0, 'Aether':0}, "River")


    # You can print the full map details if needed for a broader view
    # final_map_details = get_map_details()
    # print("\nFull Final Map Details:")
    # print(f"  Width: {final_map_details['width']}")
    # print(f"  Height: {final_map_details['height']}")
    # for r_idx, row in enumerate(final_map_details['tiles']):
    #     print(f"  Row {r_idx}: {row}")

# To run the FastAPI server (ensure you are in the 'cartographia' directory, the parent of 'backend'):
# uvicorn cartographia.backend.main:app --reload --port 8000
#
# Or, if you are directly in the 'cartographia/backend' directory:
# uvicorn main:app --reload --port 8000

# if __name__ == "__main__":
#     # main() # Commented out to prevent running test suite when starting server
#     print("To run the test suite, uncomment main() and run: python -m cartographia.backend.main")
#     print("To run the FastAPI server: uvicorn cartographia.backend.main:app --reload --port 8000")
