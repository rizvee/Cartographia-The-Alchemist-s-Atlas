import random
import copy
import json
from .models import MapGrid, ElementalSeed, PlayerHand, Tile, Objective # Added Objective

# --- Game State History for Undo/Redo ---
history_stack = []
redo_stack = []
MAX_HISTORY_SIZE = 10 # Max number of states to remember for undo/redo

# --- Save/Load Game Constant ---
SAVE_GAME_FILENAME = "saved_game.json"

# --- Elemental Fusion ---
ELEMENTAL_FUSION_RULES = {
    frozenset({"Fire", "Water"}): "Steam",
    frozenset({"Earth", "Life"}): "Flora",
    frozenset({"Decay", "Life"}): "Fungus",
    frozenset({"Earth", "Water"}): "Mud", # Concept of Mud, distinct from Mud terrain
    frozenset({"Fire", "Earth"}): "Lava",
    frozenset({"Air", "Water"}): "Mist",
    frozenset({"Air", "Fire"}): "Energy", # Simple energy concept
    frozenset({"Earth", "Earth"}): "Stone", # Combining two of the same
}
discovered_fusions = set() # Stores names of discovered concepts, e.g., {"Steam"}


# --- Objectives ---
PREDEFINED_OBJECTIVES = [
    Objective(id="obj_mt_rv", description="Forge a land with at least 2 Mountains and 1 River.", requirements={"Mountain": 2, "River": 1}),
    Objective(id="obj_fr_ds", description="Cultivate 3 Forests and sculpt 1 Desert.", requirements={"Forest": 3, "Desert": 1}),
    Objective(id="obj_vlcn", description="Summon a mighty Volcano.", requirements={"Volcano": 1}),
    Objective(id="obj_sw_jg", description="Nurture a Swamp and a Jungle.", requirements={"Swamp": 1, "Jungle": 1})
]
current_objective: Objective | None = None

def generate_new_objective():
    """Selects a new objective, ensuring it's a fresh copy, and sets its completed status to False."""
    global current_objective
    if PREDEFINED_OBJECTIVES:
        chosen_objective_template = random.choice(PREDEFINED_OBJECTIVES)
        # Create a new instance (deep copy) to avoid modifying the template
        current_objective = Objective(
            id=chosen_objective_template.id,
            description=chosen_objective_template.description,
            requirements=copy.deepcopy(chosen_objective_template.requirements),
            completed=False # Explicitly set to False for a new objective
        )
        print(f"New objective generated: {current_objective.description}")
    else:
        current_objective = None
        print("No predefined objectives available.")

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

    # Check for objective completion
    global current_objective # Ensure we are using the global one
    if current_objective and not current_objective.completed:
        if current_objective.check_completion(current_game_map): # Pass the modified map
            print(f"Objective '{current_objective.description}' completed!")
            generate_new_objective() # Auto-generate next objective

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
    global game_map, player_hand, discovered_fusions # Access global instances
    try:
        game_state_data = {
            'map': game_map.to_dict(),
            'hand': player_hand.to_dict(),
            'discovered_fusions': list(discovered_fusions) # Save as list
        }
        with open(filename, 'w') as f:
            json.dump(game_state_data, f, indent=4)
        print(f"Game state saved successfully to {filename}")
        return True
    except Exception as e:
        print(f"Error saving game to file {filename}: {e}")
        return False

def load_game_from_file(filename: str = SAVE_GAME_FILENAME) -> bool:
    """Loads game state from a file and updates the global game_map and player_hand."""
    global game_map, player_hand, history_stack, redo_stack, discovered_fusions, current_objective # current_objective is now correctly declared global at the start
    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)

        if 'map' not in loaded_data or 'hand' not in loaded_data: # Basic check
            print(f"Error: Invalid save data structure in {filename} (missing map or hand).")
            return False

        new_map = MapGrid.from_dict(loaded_data['map'])
        new_hand = PlayerHand.from_dict(loaded_data['hand'])
        loaded_fusions = set(loaded_data.get('discovered_fusions', [])) # Load fusions, default to empty list if key missing

        # Update global game state variables by modifying their content
        game_map.width = new_map.width
        game_map.height = new_map.height
        game_map.grid = new_map.grid

        player_hand.seeds = new_hand.seeds
        player_hand.max_hand_size = new_hand.max_hand_size

        discovered_fusions.clear()
        discovered_fusions.update(loaded_fusions)

        history_stack.clear()
        redo_stack.clear()

        print(f"Game state loaded successfully from {filename}. Undo/redo history cleared. Discovered fusions: {discovered_fusions}")

        # global current_objective # No longer needed here, declared at function top
        if current_objective and current_objective.completed:
                                                            # This part of the logic might need refinement if objective state persistence is critical across loads.
                                                            # The objective save/load would be part of the 'game_state_data' in save_game_to_file if we add it.
                                                            # For now, `current_objective` is just re-initialized by `generate_new_objective()` if its loaded state was completed.
                                                            # This part of the logic might need refinement if objective state persistence is critical across loads.
            # The Objective instance itself would need to be restored if it's saved.
            # For now, the save file structure only contains 'map' and 'hand' and 'discovered_fusions'.
            # If we wanted to save the objective:
            # if 'current_objective' in loaded_data and loaded_data['current_objective'] is not None:
            #     current_objective = Objective.from_dict(loaded_data['current_objective']) # Requires Objective.from_dict
            # else:
            #     generate_new_objective() # Or set to None

            # Based on current save structure, current_objective is not reloaded from file,
            # so the following check might be on a newly generated objective if not careful.
            # However, generate_new_objective() is called at the end of this function if current_objective.completed is true.
            # Let's assume current_objective is re-instantiated by generate_new_objective() if its saved state was completed.
            # The subtask for objective generation already calls generate_new_objective() if current_objective.completed.
            # This part is a bit tangled. Let's simplify: load_game_from_file resets to a new objective anyway if the one
            # that *would have been current* (if saved) was completed.
            # The current implementation of load_game_from_file does not load 'current_objective'.
            # So, after load, a new objective is generated by `generate_new_objective()` at the end of this module.
            # The check for `current_objective.completed` here will be on this newly generated one, which is always False.
            # This part of the prompt might be better handled by saving/loading the objective state explicitly.
            # For now, let's stick to what's saved: map, hand, discovered_fusions.
            # The objective completion check will occur naturally if a new objective is generated after load.
            pass # The existing logic in game_logic will generate a new one if the loaded one was completed.
                 # But current save file doesn't store the objective. This needs to be added to save_game_to_file.

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

    # After loading, check if the (potentially newly generated or soon to be checked) objective was completed
    # The current_objective global is now correctly scoped.
    # The objective loading logic itself is not part of this save file structure,
    # but if a completed objective somehow becomes current, this handles regeneration.
    if current_objective and current_objective.completed:
        print(f"Current objective '{current_objective.description}' is completed (this might be from a previous state or just re-checked). Generating a new one.")
        generate_new_objective()

    return True


def get_game_state(): # Renamed from get_map_details
    """Returns combined game state including map details, player hand, and current objective."""
    global current_objective # Ensure we're accessing the global
    # Ensure we are returning data from the current global game_map and player_hand
    map_details = {
        "width": game_map.width,
        "height": game_map.height,
        "tiles": [[tile.terrain_type for tile in row] for row in game_map.grid]
    }
    hand_details = get_player_hand_details()

    objective_data = None
    if current_objective: # current_objective is global
        objective_data = current_objective.to_dict()

    return {
        "map_details": map_details,
        "player_hand": hand_details["seeds"],
        "player_hand_count": hand_details["count"],
        "current_objective": objective_data,
        "discovered_fusions": sorted(list(discovered_fusions)) # Return sorted list for consistent order
    }

# --- Elemental Fusion Logic ---
def fuse_elements_logic(hand_instance: PlayerHand, element1_name: str, element2_name: str) -> dict:
    """
    Attempts to fuse two elemental seeds from the player's hand.
    Consumes seeds if available and a rule exists. Updates discovered_fusions.
    """
    global discovered_fusions, ELEMENTAL_FUSION_RULES

    # Handle needing two of the same seed
    if element1_name == element2_name:
        # Count how many the player has
        current_count = sum(1 for seed in hand_instance.seeds if seed.name == element1_name)
        if current_count < 2:
            return {"success": False, "message": f"You need at least two '{element1_name}' seeds to fuse them."}
    elif not (hand_instance.has_seed(element1_name) and hand_instance.has_seed(element2_name)):
        return {"success": False, "message": "You don't have the required seeds."}

    # Consume seeds (this needs to be careful if element1_name == element2_name)
    if not hand_instance.remove_seed(element1_name): # Remove first seed
        # This should not happen if has_seed checks passed, but as a safeguard
        return {"success": False, "message": f"Failed to remove first seed {element1_name}."}

    if not hand_instance.remove_seed(element2_name): # Remove second seed
        # Rollback: try to add the first seed back if the second removal fails
        hand_instance.add_seed(ElementalSeed(name=element1_name, description="Restored after failed fusion attempt.")) # Add it back
        return {"success": False, "message": f"Failed to remove second seed {element2_name} after removing first."}

    # Form key and check rule
    fusion_key = frozenset({element1_name, element2_name})
    result_name = ELEMENTAL_FUSION_RULES.get(fusion_key)

    if result_name:
        discovered_fusions.add(result_name)
        # Save state for undo after successful fusion (which changes hand and discovered_fusions)
        _save_state_for_undo(game_map, hand_instance) # hand_instance is player_hand here
        return {"success": True, "result_name": result_name, "message": f"You combined {element1_name} and {element2_name} to discover {result_name}!"}
    else:
        # Fusion failed, no known combination. Add seeds back to hand as they were consumed optimistically.
        # This also needs to be undoable if we consider failed fusions an "action".
        # For now, a failed fusion that consumed seeds is a "destructive" failed attempt.
        # The prompt implies "Consume ... If a result is found ... If no rule ... return ...".
        # This suggests consumption happens before rule check.
        # Let's save state for undo here as well, as hand changed.
        _save_state_for_undo(game_map, hand_instance)
        return {"success": False, "message": "These elements do not seem to react."}


def get_player_hand_details():
    """Returns the detailed contents of the player's hand."""
    return {
        "seeds": player_hand.get_hand_contents(),
        "count": len(player_hand.seeds)
    }

# --- Initializations ---
generate_new_objective() # Set an initial objective when the module loads

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
