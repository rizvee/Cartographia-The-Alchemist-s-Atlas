import random
import copy # For deep copying game state
import json # For saving and loading game state to/from file
from .models import MapGrid, ElementalSeed, PlayerHand, Tile

# --- Game State History for Undo/Redo ---
history_stack = []
redo_stack = []
MAX_HISTORY_SIZE = 10 # Max number of states to remember for undo/redo

# --- Save/Load Game Constant ---
SAVE_GAME_FILENAME = "saved_game.json"

# Initialize a default game map
DEFAULT_MAP_WIDTH = 10
DEFAULT_MAP_HEIGHT = 10
game_map = MapGrid(DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT)

# Initialize player's hand
# PlayerHand() will use its default max_hand_size (e.g., 10)
# The number of default_seeds (5) is less than default max_hand_size.
player_hand = PlayerHand(initial_seeds=[ # Pass initial_seeds directly to constructor
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Fire", description="A seed of conflagration.")
])

# The following lines for default_seeds and the loop are now obsolete
# as initial_seeds are passed directly to the PlayerHand constructor above.
# Commenting them out fully or deleting them.

# # Add initial seeds to player's hand - This loop is removed as it's handled by constructor
# # default_seeds = [
# #     ElementalSeed(name="Earth", description="A seed of terrestrial power."),
# #     ElementalSeed(name="Earth", description="A seed of terrestrial power."), # This was line 22
# #     ElementalSeed(name="Water", description="A seed of aquatic essence."),   # This was line 23
# #     ElementalSeed(name="Water", description="A seed of aquatic essence."),   # This was line 24
# #     # ElementalSeed(name="Fire", description="A seed of conflagration.") # Adding a different one for variety
# # ]

# # for seed in default_seeds: # This loop is no longer needed
#     # player_hand.add_seed(seed)


def apply_element_to_tile(current_game_map: MapGrid, hand_instance: PlayerHand, x: int, y: int, element_name: str, strength: int = 25) -> bool:
    """
    Applies an element to a tile if the player has the seed, consuming the seed.
    Increases tile saturation, updates terrain, and triggers neighbor echoes.

    Args:
        current_game_map (MapGrid): The game map instance.
        hand_instance (PlayerHand): The player's hand instance.
        x (int): The x-coordinate of the tile.
        y (int): The y-coordinate of the tile.
        element_name (str): The name of the element/seed to apply.
        strength (int): The amount by which to increase the element's saturation.

    Returns:
        bool: True if the element was successfully applied (seed available and consumed),
              False otherwise (e.g., seed not in hand, invalid tile/element).
    """
    tile = current_game_map.get_tile(x, y)
    if not tile:
        print(f"Error: No tile at coordinates ({x},{y}). Cannot apply '{element_name}'.")
        return False # Invalid action: tile does not exist

    if element_name not in tile.ALL_ELEMENTS: # tile.ALL_ELEMENTS is a class variable in Tile
        print(f"Warning: Element '{element_name}' is not a recognized element type. Cannot apply to tile ({x},{y}).")
        return False # Invalid action: unknown element type

    # Check if player has the seed and consume it
    if not hand_instance.has_seed(element_name):
        print(f"Error: Seed '{element_name}' not in player's hand. Cannot apply.")
        return False # Seed not available

    # If seed is present, remove it first. If successful, then apply.
    if not hand_instance.remove_seed(element_name):
        # This should ideally not happen if has_seed was true, but as a safeguard:
        print(f"Error: Failed to remove seed '{element_name}' from hand, though it was reported as present.")
        return False

    print(f"\nSuccessfully consumed '{element_name}' seed. Applying effect (strength {strength}) to tile ({x},{y}). Initial state: {tile}")

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
    primary_terrain_changed = tile.update_terrain_based_on_saturation() # This is boolean: True if terrain type string changed

    if primary_terrain_changed:
        print(f"Success! Primary tile ({x},{y}) terrain changed to '{tile.terrain_type}'.")
    else:
        print(f"Primary tile ({x},{y}) terrain remains '{tile.terrain_type}'.")

    # Elemental Influence "Echo" to Neighbors
    echo_strength = strength // 2
    if echo_strength > 0:
        neighbors = current_game_map.get_neighbors(x, y)
        print(f"Applying echo of '{element_name}' (strength {echo_strength}) to {len(neighbors)} neighbors.")
        for i, neighbor_tile in enumerate(neighbors):
            original_neighbor_terrain = neighbor_tile.terrain_type # Store before saturation change
            # print(f"  Echo for neighbor {i+1}/{len(neighbors)} (current terrain: '{original_neighbor_terrain}', current saturation: {neighbor_tile.elemental_saturation.get(element_name,0)}).")

            neighbor_current_saturation = neighbor_tile.elemental_saturation.get(element_name, 0)
            neighbor_new_saturation = min(100, neighbor_current_saturation + echo_strength)
            neighbor_new_saturation = max(0, neighbor_new_saturation)
            neighbor_tile.elemental_saturation[element_name] = neighbor_new_saturation

            # print(f"    Neighbor {i+1} saturation for '{element_name}' updated to {neighbor_new_saturation}.")

            neighbor_terrain_changed = neighbor_tile.update_terrain_based_on_saturation()
            if neighbor_terrain_changed:
                print(f"    Success! Neighbor {i+1} (originally {original_neighbor_terrain}) terrain changed to '{neighbor_tile.terrain_type}'.")
            # else:
                # print(f"    Neighbor {i+1} (originally {original_neighbor_terrain}) terrain remains '{neighbor_tile.terrain_type}'.") # Terrain could be same string but different object
    else:
        print("Echo strength is 0, skipping neighbor effects.")

    # Seed Acquisition Logic (15% chance)
    if random.random() < 0.15: # 15% chance
        if Tile.ALL_ELEMENTS: # Ensure there are elements to choose from
            awarded_seed_name = random.choice(Tile.ALL_ELEMENTS)
            # Descriptions for awarded seeds can be generic or looked up if we store them somewhere
            awarded_seed = ElementalSeed(name=awarded_seed_name, description="A mysteriously found seed.")
            print(f"Player found a new seed! Attempting to add '{awarded_seed_name}' to hand...")
            if hand_instance.add_seed(awarded_seed):
                print(f"Successfully added '{awarded_seed_name}' seed to player's hand.")
            else:
                # This case means hand_instance.add_seed already printed "Hand is full"
                print(f"Could not add '{awarded_seed_name}' seed (hand likely full).")
        else:
            print("Warning: Tile.ALL_ELEMENTS is empty, cannot award a random seed.")

    return True # Action was successful (seed consumed, logic run)

# --- Undo/Redo Logic ---

def _deep_copy_game_state(game_map_instance: MapGrid, player_hand_instance: PlayerHand):
    """Creates and returns deep copies of the game map and player hand."""
    # Using copy.deepcopy as a starting point.
    # If this becomes problematic or too slow, custom copy methods in models might be needed.
    try:
        copied_map = copy.deepcopy(game_map_instance)
        copied_hand = copy.deepcopy(player_hand_instance)
        # Verify crucial nested elements are actually new objects (optional sanity check)
        # if copied_map.grid and game_map_instance.grid:
        #     assert id(copied_map.grid[0][0]) != id(game_map_instance.grid[0][0])
        # if copied_hand.seeds and player_hand_instance.seeds:
        #      assert id(copied_hand.seeds[0]) != id(player_hand_instance.seeds[0])
        return {'map': copied_map, 'hand': copied_hand}
    except Exception as e:
        print(f"Error during deep copy: {e}")
        # Fallback or re-raise, depending on how critical this is.
        # For now, if deepcopy fails, we can't reliably do undo/redo.
        raise


def _save_state_for_undo(current_game_map: MapGrid, current_player_hand: PlayerHand):
    """Saves a deep copy of the current game state to the history_stack."""
    global history_stack, redo_stack, MAX_HISTORY_SIZE

    copied_state = _deep_copy_game_state(current_game_map, current_player_hand)
    history_stack.append(copied_state)

    if len(history_stack) > MAX_HISTORY_SIZE:
        history_stack.pop(0) # Remove the oldest state

    redo_stack.clear() # Any new action clears the redo stack
    print(f"State saved for undo. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")


def undo_last_action() -> bool:
    """
    Restores the game state to the previous state from the history_stack.
    The undone state (current state before undo) is moved to the redo_stack.
    Returns True if successful, False otherwise.
    """
    global game_map, player_hand, history_stack, redo_stack, MAX_HISTORY_SIZE

    if not history_stack:
        print("Undo failed: No history available.")
        return False

    # Save current state to redo_stack before undoing
    state_to_redo = _deep_copy_game_state(game_map, player_hand)
    redo_stack.append(state_to_redo)
    if len(redo_stack) > MAX_HISTORY_SIZE:
        redo_stack.pop(0)

    # Pop from history and restore
    last_saved_state = history_stack.pop()

    # Restore by modifying the *contents* of the existing global instances
    # This avoids issues with other modules holding old references.

    # Restore MapGrid
    # It's safer to deepcopy the contents from the saved state into the global objects
    # to avoid the global objects accidentally sharing mutable state with the history.
    restored_map_obj = copy.deepcopy(last_saved_state['map'])
    game_map.width = restored_map_obj.width
    game_map.height = restored_map_obj.height
    game_map.grid = restored_map_obj.grid # This grid is already a deep copy of tiles

    # Restore PlayerHand
    restored_hand_obj = copy.deepcopy(last_saved_state['hand'])
    player_hand.seeds = restored_hand_obj.seeds
    player_hand.max_hand_size = restored_hand_obj.max_hand_size

    print(f"Undo successful. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")
    return True


def redo_next_action() -> bool:
    """
    Restores the game state from the redo_stack.
    The current state (before redo) is moved back to the history_stack.
    Returns True if successful, False otherwise.
    """
    global game_map, player_hand, history_stack, redo_stack, MAX_HISTORY_SIZE

    if not redo_stack:
        print("Redo failed: No actions to redo.")
        return False

    # Save current state to history_stack before redoing
    state_to_undo_again = _deep_copy_game_state(game_map, player_hand)
    history_stack.append(state_to_undo_again)
    if len(history_stack) > MAX_HISTORY_SIZE:
        history_stack.pop(0)

    # Pop from redo and restore
    next_state_to_restore = redo_stack.pop()

    # Restore MapGrid contents
    restored_map_obj = copy.deepcopy(next_state_to_restore['map'])
    game_map.width = restored_map_obj.width
    game_map.height = restored_map_obj.height
    game_map.grid = restored_map_obj.grid

    # Restore PlayerHand contents
    restored_hand_obj = copy.deepcopy(next_state_to_restore['hand'])
    player_hand.seeds = restored_hand_obj.seeds
    player_hand.max_hand_size = restored_hand_obj.max_hand_size

    print(f"Redo successful. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")
    return True

# --- Modified Game Logic to use Undo/Redo ---

# apply_element_to_tile needs to be modified to call _save_state_for_undo
# This is done by replacing the existing apply_element_to_tile function definition
# The definition of apply_element_to_tile is quite long, so the change will be shown
# in the diff by replacing the whole function.

# (Previous apply_element_to_tile function definition is implicitly replaced by the one below)

def apply_element_to_tile(current_game_map: MapGrid, hand_instance: PlayerHand, x: int, y: int, element_name: str, strength: int = 25) -> bool:
    """
    Saves state, then applies an element to a tile if the player has the seed, consuming the seed.
    Increases tile saturation, updates terrain, and triggers neighbor echoes.
    Returns True if the element was successfully applied, False otherwise.
    """
    # Save state BEFORE any modification for this action
    _save_state_for_undo(current_game_map, hand_instance) # current_game_map and hand_instance are the global ones

    tile = current_game_map.get_tile(x, y)
    if not tile:
        print(f"Error: No tile at coordinates ({x},{y}). Cannot apply '{element_name}'.")
        # Note: State was saved, but this action failed early.
        # Consider if history_stack.pop() is needed here if we don't want to record failed attempts as undoable.
        # For now, failed attempts that don't change state won't really clutter history if state is identical,
        # but if they consume resources or have other side effects, it might matter.
        # Current approach: save, then attempt. If attempt fails, the "undone" state is identical to "current" state before this call.
        return False

    if element_name not in Tile.ALL_ELEMENTS:
        print(f"Warning: Element '{element_name}' is not a recognized element type. Cannot apply to tile ({x},{y}).")
        return False

    if not hand_instance.has_seed(element_name):
        print(f"Error: Seed '{element_name}' not in player's hand. Cannot apply.")
        return False

    if not hand_instance.remove_seed(element_name):
        print(f"Error: Failed to remove seed '{element_name}' from hand, though it was reported as present.")
        return False

    print(f"\nSuccessfully consumed '{element_name}' seed. Applying effect (strength {strength}) to tile ({x},{y}). Initial state: {tile}")

    current_saturation = tile.elemental_saturation.get(element_name, 0)
    new_saturation = min(100, current_saturation + strength)
    new_saturation = max(0, new_saturation)
    tile.elemental_saturation[element_name] = new_saturation

    print(f"Saturation updated for '{element_name}' to {new_saturation} for primary tile ({x},{y}). Current saturations: {tile.elemental_saturation}")

    primary_terrain_changed = tile.update_terrain_based_on_saturation()

    if primary_terrain_changed:
        print(f"Success! Primary tile ({x},{y}) terrain changed to '{tile.terrain_type}'.")
    else:
        print(f"Primary tile ({x},{y}) terrain remains '{tile.terrain_type}'.")

    echo_strength = strength // 2
    if echo_strength > 0:
        neighbors = current_game_map.get_neighbors(x, y)
        print(f"Applying echo of '{element_name}' (strength {echo_strength}) to {len(neighbors)} neighbors.")
        for i, neighbor_tile in enumerate(neighbors):
            original_neighbor_terrain = neighbor_tile.terrain_type

            neighbor_current_saturation = neighbor_tile.elemental_saturation.get(element_name, 0)
            neighbor_new_saturation = min(100, neighbor_current_saturation + echo_strength)
            neighbor_new_saturation = max(0, neighbor_new_saturation)
            neighbor_tile.elemental_saturation[element_name] = neighbor_new_saturation

            neighbor_terrain_changed = neighbor_tile.update_terrain_based_on_saturation()
            if neighbor_terrain_changed:
                print(f"    Success! Neighbor {i+1} (originally {original_neighbor_terrain}) terrain changed to '{neighbor_tile.terrain_type}'.")
    else:
        print("Echo strength is 0, skipping neighbor effects.")

    if random.random() < 0.15:
        if Tile.ALL_ELEMENTS:
            awarded_seed_name = random.choice(Tile.ALL_ELEMENTS)
            awarded_seed = ElementalSeed(name=awarded_seed_name, description="A mysteriously found seed.")
            print(f"Player found a new seed! Attempting to add '{awarded_seed_name}' to hand...")
            if hand_instance.add_seed(awarded_seed): # This uses the PlayerHand instance passed in
                print(f"Successfully added '{awarded_seed_name}' seed to player's hand.")
            else:
                print(f"Could not add '{awarded_seed_name}' seed (hand likely full).")
        else:
            print("Warning: Tile.ALL_ELEMENTS is empty, cannot award a random seed.")

    return True


# Note: get_game_state() is defined after this block (this comment might be inaccurate depending on final placement)

def save_game_to_file(filename: str = SAVE_GAME_FILENAME): # Now SAVE_GAME_FILENAME is defined
    """Saves the current game state (map and player hand) to a file."""
    global game_map, player_hand # Access the global instances
    try:
        game_state_data = {
            'map': game_map.to_dict(),
            'hand': player_hand.to_dict()
        }
        with open(filename, 'w') as f:
            json.dump(game_state_data, f, indent=4) # Use indent for readability
        print(f"Game state saved successfully to {filename}")
        return True
    except Exception as e:
        print(f"Error saving game to file {filename}: {e}")
        return False

def load_game_from_file(filename: str = SAVE_GAME_FILENAME) -> bool:
    """Loads game state from a file and updates the global game_map and player_hand."""
    global game_map, player_hand, history_stack, redo_stack # Need to modify these globals
    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)

        if 'map' not in loaded_data or 'hand' not in loaded_data:
            print(f"Error: Invalid save data structure in {filename}.")
            return False

        # Reconstruct game objects from loaded data
        # This directly replaces the global instances.
        # Ensure this is the desired behavior for all parts of the application.
        new_map = MapGrid.from_dict(loaded_data['map'])
        new_hand = PlayerHand.from_dict(loaded_data['hand'])

        # Update global variables by replacing their content/attributes
        # This is safer than rebinding global variables if other modules hold direct references.
        game_map.width = new_map.width
        game_map.height = new_map.height
        game_map.grid = new_map.grid # new_map.grid already contains Tile objects

        player_hand.seeds = new_hand.seeds
        player_hand.max_hand_size = new_hand.max_hand_size

        # Clear undo/redo history as the game state has jumped
        history_stack.clear()
        redo_stack.clear()

        print(f"Game state loaded successfully from {filename}. Undo/redo history cleared.")
        # Potentially save this loaded state as the first entry in history? For now, no.
        # _save_state_for_undo(game_map, player_hand) # Optional: save loaded state as first history item

        return True
    except FileNotFoundError:
        print(f"Error: Save file {filename} not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. File might be corrupted.")
        return False
    except ValueError as ve: # Catch ValueError from from_dict methods
        print(f"Error: Invalid data format in save file {filename}: {ve}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred loading game from file {filename}: {e}")
        return False


def get_game_state(): # Renamed from get_map_details
    """Returns combined game state including map details and player hand."""
    # Ensure we are returning data from the current global game_map and player_hand
    map_details = {
        "width": game_map.width,
        "height": game_map.height,
        "tiles": [[tile.terrain_type for tile in row] for row in game_map.grid]
    }
    hand_details = get_player_hand_details() # Uses existing helper

    return {
        "map_details": map_details,
        "player_hand": hand_details["seeds"], # Just the list of seed names
        "player_hand_count": hand_details["count"]
    }

def get_player_hand_details(): # This helper is still useful internally or for other potential endpoints
    """Returns the detailed contents of the player's hand."""
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
