from .models import Tile, MapGrid, ElementalSeed, PlayerHand, Objective
from typing import Dict, List, Optional, Tuple, Set
import random
import json # For save/load
import copy # For deep copying states for undo/redo

# --- Game State Variables ---
game_map: MapGrid = MapGrid(width=20, height=15)
player_hand: PlayerHand = PlayerHand(max_hand_size=10)
current_objective: Optional[Objective] = None
discovered_fusions: Set[str] = set() # Stores names of discovered fusion products
discovered_lore_entries: Set[str] = set()
discovered_biome_types: Set[str] = set()
discovered_feature_types: Set[str] = set()

# --- Undo/Redo History ---
history_stack: List[Dict] = [] # Stores snapshots of game state for undo
redo_stack: List[Dict] = []   # Stores snapshots for redo
MAX_HISTORY_SIZE: int = 20    # Max number of undo steps


# --- Predefined Game Data ---
BASE_ELEMENT_SEEDS = {
    "Earth": ElementalSeed("Earth", "Solid and stable, the foundation of mountains and soil."),
    "Water": ElementalSeed("Water", "Flowing and adaptable, essential for life and carving landscapes."),
    "Fire": ElementalSeed("Fire", "Volatile and transformative, a source of destruction and creation."),
    "Air": ElementalSeed("Air", "Ephemeral and pervasive, carrying scents and shaping weather."),
    "Aether": ElementalSeed("Aether", "A mysterious, potent element that resonates with ancient structures.")
}

ELEMENTAL_FUSION_RULES: Dict[frozenset, Dict] = {
    frozenset(["Earth", "Water"]): {"name": "Mud", "is_usable_seed": True, "description": "Earth and Water combine to form fertile Mud."},
    frozenset(["Fire", "Earth"]): {"name": "Lava", "is_usable_seed": True, "description": "Fire melts Earth into flowing Lava."},
    frozenset(["Fire", "Water"]): {"name": "Steam", "is_usable_seed": True, "description": "Fire boils Water into rising Steam."},
    frozenset(["Air", "Water"]): {"name": "Mist", "is_usable_seed": True, "description": "Air disperses Water into a clinging Mist."},
    frozenset(["Earth", "Earth"]): {"name": "Rock", "is_usable_seed": False, "description": "Concentrated Earth forms solid Rock. Not a seed."},
    frozenset(["Lava", "Water"]): {"name": "Obsidian", "is_usable_seed": False, "description": "Lava cooled by Water forms Obsidian. Not a seed."},
    # More complex fusions
    frozenset(["Mud", "Fire"]): {"name": "Clay", "is_usable_seed": True, "description": "Mud baked by Fire creates Clay."},
    frozenset(["Steam", "Earth"]): {"name": "Geyser", "is_usable_seed": False, "description": "Steam erupting through Earth creates a Geyser. Not a seed, but a feature?"},
}

# --- Lore & Objectives ---
PREDEFINED_OBJECTIVES: List[Objective] = [
    Objective(id="OBJ001", description="Create a 2x2 area of 'Water' terrain.", requirements=[
        {"type": "terrain_count", "terrain": "Water", "min_count": 4}
    ]),
    Objective(id="OBJ002", description="Discover 2 different elemental fusions.", requirements=[
        {"type": "discover_fusions", "min_count": 2}
    ]),
    Objective(id="OBJ003", description="Create a 'Forest' tile adjacent to a 'River' tile.", requirements=[
        {"type": "feature_adjacent_to_terrain", "feature": None, "terrain": "River", "target_terrain": "Forest", "min_count": 1} # Simplified for now
    ]),
    # ... more objectives
]

def _add_lore_entry(category: str, item_name: str, description: Optional[str] = None):
    """Adds a lore entry if it's new."""
    global discovered_lore_entries
    entry = ""
    if category == "Biome":
        if item_name not in discovered_biome_types:
            discovered_biome_types.add(item_name)
            entry = f"New Biome Discovered: {item_name}."
            if description: entry += f" {description}"
    elif category == "Feature":
        if item_name not in discovered_feature_types:
            discovered_feature_types.add(item_name)
            entry = f"New Feature Observed: {item_name}."
            if description: entry += f" {description}"
    elif category == "Fusion":
        # Fusion lore is handled directly in fuse_elements_logic for now
        return
    elif category == "Objective":
        entry = f"New Objective: {item_name}" # item_name is objective description here

    if entry and entry not in discovered_lore_entries:
        discovered_lore_entries.add(entry)
        print(f"Lore added: {entry}")

def generate_new_objective():
    """Selects a new random objective that is not the current one (if any)."""
    global current_objective, PREDEFINED_OBJECTIVES
    available_objectives = [obj for obj in PREDEFINED_OBJECTIVES if obj.id != (current_objective.id if current_objective else None)]
    if not available_objectives:
        print("Warning: No new objectives available to generate.")
        # Potentially re-use objectives or have a default "no objective" state
        return

    new_obj_template = random.choice(available_objectives)
    # Create a new instance to avoid modifying the template
    current_objective = Objective(
        id=new_obj_template.id,
        description=new_obj_template.description,
        requirements=new_obj_template.requirements, # This should be fine as reqs are dicts/lists
        completed=False # Always start fresh
    )
    _add_lore_entry("Objective", current_objective.description)
    print(f"New objective generated: {current_objective.description}")


# --- Initialization ---
def initialize_game():
    """Initializes the game state."""
    global game_map, player_hand, discovered_fusions, current_objective, history_stack, redo_stack
    game_map = MapGrid(width=20, height=15) # Reset map
    player_hand = PlayerHand(max_hand_size=10) # Reset hand
    discovered_fusions = set()
    discovered_lore_entries.clear()
    discovered_biome_types.clear()
    discovered_feature_types.clear()
    history_stack.clear()
    redo_stack.clear()

    # Populate initial hand (example)
    player_hand.add_seed(BASE_ELEMENT_SEEDS["Earth"])
    player_hand.add_seed(BASE_ELEMENT_SEEDS["Earth"])
    player_hand.add_seed(BASE_ELEMENT_SEEDS["Water"])
    player_hand.add_seed(BASE_ELEMENT_SEEDS["Water"])
    player_hand.add_seed(BASE_ELEMENT_SEEDS["Fire"])

    generate_new_objective() # Get the first objective
    print("Game initialized.")

# --- Core Game Logic ---

ELEMENT_PROPERTIES = {
    "Earth": {"base_strength": 20, "echo_factor": 0.3},
    "Water": {"base_strength": 20, "echo_factor": 0.5},
    "Fire": {"base_strength": 25, "echo_factor": 0.4},
    "Air": {"base_strength": 15, "echo_factor": 0.6},
    "Mud": {"base_strength": 18, "echo_factor": 0.2},
    "Lava": {"base_strength": 30, "echo_factor": 0.3},
    "Steam": {"base_strength": 15, "echo_factor": 0.7},
    "Mist": {"base_strength": 12, "echo_factor": 0.8},
    # Derived elements might have different properties
    "Aether": {"base_strength": 50, "echo_factor": 0.1} # Potent, but doesn't echo much in normal use
}

TERRAIN_INTERACTIONS = { # Multiplier for element strength based on terrain
    "Earth": {"Earth": 1.2, "Fire": 0.8, "Water": 0.5},
    "Water": {"Water": 1.2, "Fire": 0.5, "Earth": 0.8},
    "Forest": {"Life": 1.2, "Fire": 1.5, "Water": 1.1}, # Fire spreads well
    "Desert": {"Fire": 1.2, "Water": 0.3, "Earth": 1.1},
    "Mountain": {"Earth": 1.3, "Air": 1.2, "Fire": 0.7},
    "Volcano": {"Fire": 1.5, "Earth": 1.2, "Water": 0.2},
    # Default if terrain not listed or element not in terrain's dict
    "Default": {"Default": 1.0}
}


def apply_element_to_tile(x: int, y: int, element_name: str) -> bool:
    """
    Applies an elemental seed to a tile and its neighbors.
    Returns True if the action was successfully processed, False otherwise.
    """
    global game_map, player_hand, discovered_lore_entries, discovered_feature_types # history_stack, redo_stack managed by _save_state_for_undo

    tile = game_map.get_tile(x, y)
    if not tile:
        print(f"Error: Tile at ({x},{y}) not found.")
        return False # Action cannot proceed

    if not player_hand.has_seed(element_name):
        print(f"Error: Player does not have '{element_name}' seed.")
        return False # Action cannot proceed

    _save_state_for_undo() # Save state now that basic checks have passed

    # Consume the seed FIRST for any action.
    # If a special interaction (like Obelisk) consumes it differently, it won't be available for saturation.
    player_hand.remove_seed(element_name)

    # --- Ancient Obelisk Interaction ---
    if tile.feature == "Ancient Obelisk" and element_name == "Aether":
        tile.feature = "Activated Obelisk"
        _add_lore_entry("Feature", "Activated Obelisk", "A once dormant obelisk now hums with power.")

        activation_lore = f"The Ancient Obelisk at ({x},{y}) resonates with Aether and awakens!"
        if activation_lore not in discovered_lore_entries:
            discovered_lore_entries.add(activation_lore)
            print(activation_lore)

        # Grant rewards
        rewards_granted = []
        if player_hand.add_seed(copy.deepcopy(BASE_ELEMENT_SEEDS["Aether"])): # Give a copy
            rewards_granted.append("Aether")
        # Add some base elements as reward
        for base_elem in ["Earth", "Water", "Fire", "Air"]:
            if len(rewards_granted) < 4 and player_hand.add_seed(copy.deepcopy(BASE_ELEMENT_SEEDS[base_elem])): # Limit additional seeds
                 rewards_granted.append(base_elem)

        if rewards_granted:
            reward_msg = f"The Activated Obelisk bestows seeds: {', '.join(rewards_granted)}."
            if reward_msg not in discovered_lore_entries: # Add to lore as it's a significant event
                discovered_lore_entries.add(reward_msg)
            print(reward_msg)
        else:
            full_hand_msg = "The Obelisk tries to bestow gifts, but your hands are full."
            if full_hand_msg not in discovered_lore_entries:
                 discovered_lore_entries.add(full_hand_msg)
            print(full_hand_msg)

        # Objective check after special interaction
        if current_objective and not current_objective.completed:
            if current_objective.check_completion(game_map, discovered_fusions):
                generate_new_objective()
        return True # Aether consumed, interaction complete, no normal saturation

    elif tile.feature == "Activated Obelisk" and element_name == "Aether":
        spent_lore = f"The Activated Obelisk at ({x},{y}) hums faintly with spent Aether, offering no more gifts."
        if spent_lore not in discovered_lore_entries: # Add to lore only once per obelisk perhaps, or make it generic
            discovered_lore_entries.add(spent_lore)
        print(spent_lore)
        # Aether is consumed, but no further effect or reward
        # Objective check might still be relevant if an objective is about repeat activations (though not currently)
        if current_objective and not current_objective.completed:
            if current_objective.check_completion(game_map, discovered_fusions):
                generate_new_objective()
        return True # Aether consumed, no further changes

    # --- Normal Element Application ---
    element_props = ELEMENT_PROPERTIES.get(element_name, {"base_strength": 10, "echo_factor": 0.2}) # Default for unlisted
    base_strength = element_props["base_strength"]
    echo_factor = element_props["echo_factor"]

    # Primary tile application
    terrain_modifier = TERRAIN_INTERACTIONS.get(tile.terrain_type, TERRAIN_INTERACTIONS["Default"])
    effective_strength = int(base_strength * terrain_modifier.get(element_name, terrain_modifier.get("Default", 1.0)))

    tile.elemental_saturation[element_name] = tile.elemental_saturation.get(element_name, 0) + effective_strength
    # Cap saturation
    tile.elemental_saturation[element_name] = min(tile.elemental_saturation[element_name], 100)

    terrain_changed_primary = tile.update_terrain_based_on_saturation()
    if terrain_changed_primary:
        _add_lore_entry("Biome", tile.terrain_type)


    # Echo to neighbors
    neighbors = game_map.get_neighbors(x, y, include_diagonals=False) # Cardinal neighbors
    echo_strength = int(effective_strength * echo_factor)

    if echo_strength > 0:
        for neighbor_tile in neighbors:
            # Consider neighbor's terrain for echo effectiveness
            neighbor_terrain_modifier = TERRAIN_INTERACTIONS.get(neighbor_tile.terrain_type, TERRAIN_INTERACTIONS["Default"])
            effective_echo_strength = int(echo_strength * neighbor_terrain_modifier.get(element_name, neighbor_terrain_modifier.get("Default", 1.0)))

            if effective_echo_strength > 0:
                neighbor_tile.elemental_saturation[element_name] = neighbor_tile.elemental_saturation.get(element_name, 0) + effective_echo_strength
                neighbor_tile.elemental_saturation[element_name] = min(neighbor_tile.elemental_saturation[element_name], 100)
                if neighbor_tile.update_terrain_based_on_saturation():
                     _add_lore_entry("Biome", neighbor_tile.terrain_type)


    # Probabilistic seed acquisition (e.g., 15% chance to get a random base element seed)
    if random.random() < 0.15: # 15% chance
        random_base_element = random.choice(list(BASE_ELEMENT_SEEDS.keys()))
        if player_hand.add_seed(BASE_ELEMENT_SEEDS[random_base_element]):
            # This message should ideally be part of the game state response
            print(f"Acquired a new '{random_base_element}' seed!")
            # discovered_lore_entries.add(f"Acquired a new '{random_base_element}' seed from the environment!")


    # Check objective completion (also done after obelisk interaction)
    if current_objective and not current_objective.completed:
        if current_objective.check_completion(game_map, discovered_fusions):
            generate_new_objective() # Generate next one

    _check_and_spawn_features(tile, x, y) # Check for features after saturation change
    # Water flow should also be after all saturation changes, including echo.
    # Consider if _handle_water_flow should be called for primary tile here, or after echo.
    # For now, let's assume it's mainly for the primary tile based on its direct saturation.
    _handle_water_flow(tile, x, y)

    return True # Action successfully processed


def fuse_elements_logic(element1_name: str, element2_name: str) -> Dict:
    """
    Attempts to fuse two elemental seeds from the player's hand.
    Returns a dictionary with 'success' (bool), 'message' (str), and optionally 'new_seed_name' (str).
    """
    global player_hand, discovered_fusions, discovered_lore_entries, discovered_feature_types # history_stack, redo_stack managed by _save_state_for_undo

    # Check if player has the seeds (do this before saving state for undo)
    if not player_hand.has_seed(element1_name) or not player_hand.has_seed(element2_name):
        return {"success": False, "message": "Missing one or both seeds for fusion."}
    if element1_name == element2_name: # Check for count if elements are same
        current_hand_contents = player_hand.get_hand_contents()
        if current_hand_contents.count(element1_name) < 2:
            return {"success": False, "message": f"Need two '{element1_name}' seeds to fuse them."}

    # Try to find a fusion rule (do this also before saving, as it's a check)
    elements_to_fuse = frozenset([element1_name, element2_name])
    fusion_result = ELEMENTAL_FUSION_RULES.get(elements_to_fuse)

    if not fusion_result:
        return {"success": False, "message": "These elements do not fuse into anything known."}

    _save_state_for_undo() # Save state now that preliminary checks passed

    # Consume seeds (already checked if they exist and rule exists)
    player_hand.remove_seed(element1_name)
    player_hand.remove_seed(element2_name)

    new_product_name = fusion_result["name"]
    is_new_discovery = new_product_name not in discovered_fusions

    discovered_fusions.add(new_product_name)

    message = f"Fusion successful! Created {new_product_name}."
    if is_new_discovery:
        message += " New fusion discovered!"
        lore_entry = f"New Fusion Discovered: {element1_name} + {element2_name} = {new_product_name}. {fusion_result['description']}"
        if lore_entry not in discovered_lore_entries:
            discovered_lore_entries.add(lore_entry)


    if fusion_result.get("is_usable_seed", False):
        new_seed = ElementalSeed(name=new_product_name, description=fusion_result["description"])
        # Add to known properties if not already there (for apply_element_to_tile)
        if new_product_name not in ELEMENT_PROPERTIES:
             ELEMENT_PROPERTIES[new_product_name] = {"base_strength": 10, "echo_factor": 0.2} # Default for new seeds

        if player_hand.add_seed(new_seed):
            message += f" Added '{new_product_name}' seed to hand."
        else:
            message += f" Hand is full, '{new_product_name}' seed was not added."
            # Potentially drop it on the ground or a temporary holding? For now, it's lost.
    else:
        message += f" {new_product_name} is not a usable seed."
        # Handle non-seed products (e.g., direct map changes, features - future enhancement)
        # For example, if "Geyser" is formed, it could try to spawn a geyser feature on a target tile.

    # Check objective completion
    if current_objective and not current_objective.completed:
        if current_objective.check_completion(game_map, discovered_fusions):
            generate_new_objective()

    # It's possible a fusion itself could spawn a feature if it's not a seed.
    # For now, _check_and_spawn_features is mainly tied to apply_element_to_tile.

    return {"success": True, "message": message, "new_seed_name": new_product_name if fusion_result.get("is_usable_seed") else None}


# --- Feature Spawning, Water Flow, etc. ---

def _check_and_spawn_features(tile: Tile, tile_x: int, tile_y: int):
    """Checks conditions and potentially spawns features on a tile."""
    global discovered_feature_types, discovered_lore_entries
    if tile.feature: # Don't overwrite existing features
        return

    # Rule for Ruins
    if tile.terrain_type == "Desert" and tile.elevation >= 0 and random.random() < 0.10: # 10% chance in desert
        tile.feature = "Ruins"
        _add_lore_entry("Feature", "Ruins", f"Ancient Ruins discovered at ({tile_x},{tile_y}) in the Desert.")
        print(f"Feature spawned: Ruins at ({tile_x},{tile_y})")

    # Rule for Ancient Obelisk
    elif tile.terrain_type == "Mountain" and tile.elevation >= 3 and random.random() < 0.05: # 5% chance on high mountain peaks
        tile.feature = "Ancient Obelisk"
        _add_lore_entry("Feature", "Ancient Obelisk", f"An Ancient Obelisk looms at ({tile_x},{tile_y}) on a high peak.")
        print(f"Feature spawned: Ancient Obelisk at ({tile_x},{tile_y})")
    # Add more feature spawning rules here...


def _handle_water_flow(tile: Tile, tile_x: int, tile_y: int):
    """Handles water flowing from a tile to its neighbors if conditions are met."""
    if tile.terrain_type not in ["Water", "River", "Shallow Water"] and \
       tile.elemental_saturation.get("Water", 0) >= 70 and tile.elevation > 0:

        neighbors = game_map.get_neighbors(tile_x, tile_y, include_diagonals=False)
        if not neighbors:
            return

        # Find valid neighbors to flow to: lower elevation, not already a major water body
        valid_flow_targets = []
        lowest_elevation = tile.elevation
        for neighbor_coords in neighbors: # Assuming get_neighbors returns list of (x,y) tuples or similar
            # Need to get actual neighbor Tile objects from game_map using these coords if get_neighbors doesn't return Tile objects
            # For now, assuming get_neighbors returns Tile objects as it was used previously
            # This part needs careful review of get_neighbors return type.
            # Let's assume game_map.get_neighbors returns list of Tile objects directly for now.
            # If it returns coords, we need game_map.get_tile(nx,ny)

            # This is a BUG in previous thought process. get_neighbors *does* return Tile objects.
            neighbor_tile = neighbor_coords # neighbor_coords is actually a Tile object

            if neighbor_tile.elevation < lowest_elevation:
                lowest_elevation = neighbor_tile.elevation
                valid_flow_targets = [neighbor_tile] # New lowest, reset targets
            elif neighbor_tile.elevation == lowest_elevation:
                valid_flow_targets.append(neighbor_tile)

        # Filter further: must be strictly lower than source, and not a major water body itself
        final_targets = [nt for nt in valid_flow_targets if nt.elevation < tile.elevation and \
                         nt.terrain_type not in ["Water", "River"]]

        if not final_targets:
            return

        chosen_target_tile = random.choice(final_targets)

        flow_amount = max(10, int(tile.elemental_saturation["Water"] * 0.20)) # Flow 20% of water, min 10

        # Reduce water from source
        tile.elemental_saturation["Water"] = max(0, tile.elemental_saturation["Water"] - flow_amount)
        source_terrain_changed = tile.update_terrain_based_on_saturation()
        if source_terrain_changed: _add_lore_entry("Biome", tile.terrain_type)

        # Add water to target
        chosen_target_tile.elemental_saturation["Water"] = min(100, chosen_target_tile.elemental_saturation.get("Water", 0) + flow_amount)
        target_terrain_changed = chosen_target_tile.update_terrain_based_on_saturation()
        if target_terrain_changed: _add_lore_entry("Biome", chosen_target_tile.terrain_type)

        flow_lore = f"Water flows from ({tile_x},{tile_y}) to an adjacent tile due to high saturation and elevation difference."
        if flow_lore not in discovered_lore_entries:
            discovered_lore_entries.add(flow_lore)
        print(flow_lore)
        # Recursively call for the target tile in case it also starts to flow (potential chain reaction)
        # Find target coords first. This is tricky if get_neighbors doesn't give coords.
        # For now, no recursive call to prevent complexity and potential infinite loops without careful checks.


# --- Undo/Redo Logic ---
def _deep_copy_game_state() -> Dict:
    """Creates a deep copy of the current game state for history."""
    # Ensure current_objective is handled correctly, especially its 'completed' status
    # which might be part of the Objective object itself.
    current_obj_dict = None
    if current_objective:
        current_obj_dict = {
            "id": current_objective.id,
            "description": current_objective.description, # Not strictly needed for restore but good for debug
            "requirements": copy.deepcopy(current_objective.requirements), # Also for debug/completeness
            "completed": current_objective.completed
        }

    return {
        "map": game_map.to_dict(),
        "hand": player_hand.to_dict(),
        "fusions": copy.deepcopy(discovered_fusions),
        "current_objective_internal": current_obj_dict, # Store the dict representation
        "lore": copy.deepcopy(discovered_lore_entries),
        "biomes": copy.deepcopy(discovered_biome_types),
        "features": copy.deepcopy(discovered_feature_types),
    }

def _restore_globals_from_state(state_to_restore: Dict):
    """Helper to update global variables from a state dictionary."""
    global game_map, player_hand, discovered_fusions, current_objective
    global discovered_lore_entries, discovered_biome_types, discovered_feature_types

    game_map = MapGrid.from_dict(state_to_restore["map"])
    player_hand = PlayerHand.from_dict(state_to_restore["hand"])

    discovered_fusions.clear()
    discovered_fusions.update(state_to_restore["fusions"])

    discovered_lore_entries.clear()
    discovered_lore_entries.update(state_to_restore["lore"])

    discovered_biome_types.clear()
    discovered_biome_types.update(state_to_restore["biomes"])

    discovered_feature_types.clear()
    discovered_feature_types.update(state_to_restore["features"])

    obj_dict = state_to_restore.get("current_objective_internal")
    current_objective = None # Reset
    if obj_dict and obj_dict.get("id"):
        # Reconstruct the objective object from the stored dict.
        # This assumes PREDEFINED_OBJECTIVES is available and contains the template.
        # Or, if Objective.from_dict exists and is robust, it could be used.
        # For now, we're creating a new Objective instance.
        current_objective = Objective(
            id=obj_dict["id"],
            description=obj_dict["description"], # Or fetch from PREDEFINED_OBJECTIVES
            requirements=obj_dict["requirements"], # Or fetch from PREDEFINED_OBJECTIVES
            completed=obj_dict["completed"]
        )
    elif obj_dict: # Fallback if only partial data (e.g. from older state format)
         # Attempt to find by ID from predefined if description/requirements missing
        found_obj_template = next((obj for obj in PREDEFINED_OBJECTIVES if obj.id == obj_dict.get("id")), None)
        if found_obj_template:
            current_objective = Objective(
                id=found_obj_template.id,
                description=found_obj_template.description,
                requirements=found_obj_template.requirements,
                completed=obj_dict.get("completed", False) # Use completed status from state
            )
    # If no objective in state or cannot reconstruct, current_objective remains None.
    # The game might need logic to then generate a new one if appropriate.


def _save_state_for_undo():
    """Saves the current game state to the history stack."""
    global history_stack, redo_stack
    if len(history_stack) >= MAX_HISTORY_SIZE:
        history_stack.pop(0)

    current_state_copy = _deep_copy_game_state()
    history_stack.append(current_state_copy)
    redo_stack.clear()
    # print(f"State saved. History: {len(history_stack)}, Redo: {len(redo_stack)}")

def undo_last_action() -> bool:
    """Restores the game state to the previous state in the history stack."""
    global history_stack, redo_stack
    if not history_stack:
        print("No actions in history to undo.")
        return False

    current_state_for_redo = _deep_copy_game_state()
    redo_stack.append(current_state_for_redo)
    if len(redo_stack) > MAX_HISTORY_SIZE:
        redo_stack.pop(0)

    state_to_restore = history_stack.pop()
    _restore_globals_from_state(state_to_restore)

    print(f"Action undone. History: {len(history_stack)}, Redo: {len(redo_stack)}")
    return True

def redo_next_action() -> bool:
    """Restores the game state from the redo stack."""
    global history_stack, redo_stack
    if not redo_stack:
        print("No actions in redo stack.")
        return False

    current_state_for_history = _deep_copy_game_state()
    history_stack.append(current_state_for_history)
    if len(history_stack) > MAX_HISTORY_SIZE:
        history_stack.pop(0)

    state_to_restore = redo_stack.pop()
    _restore_globals_from_state(state_to_restore)

    print(f"Action redone. History: {len(history_stack)}, Redo: {len(redo_stack)}")
    return True


# --- Game State Retrieval ---
def get_game_state() -> Dict:
    """Returns the current game state as a dictionary for the API."""
    map_details = game_map.to_dict()
    # Enrich map_details with feature information for each tile if not already there
    for r_idx, row in enumerate(map_details["grid"]):
        for c_idx, tile_dict in enumerate(row):
            tile_obj = game_map.get_tile(c_idx, r_idx) # Correct order for get_tile
            if tile_obj:
                tile_dict["feature"] = tile_obj.feature # Ensure feature is included

    objective_dict = None
    if current_objective:
        objective_dict = current_objective.to_dict()
        # Check completion status one last time before sending, in case it was just completed
        # and a new one was generated but not yet sent to client.
        # This might be redundant if generate_new_objective is consistently called.
        # objective_dict["completed"] = current_objective.check_completion(game_map, discovered_fusions)

    return {
        "map_details": map_details,
        "player_hand": player_hand.get_hand_contents(), # Just names for now
        "player_hand_count": {name: player_hand.get_hand_contents().count(name) for name in set(player_hand.get_hand_contents())},
        "current_objective": objective_dict,
        "discovered_fusions": sorted(list(discovered_fusions)),
        "discovered_lore": sorted(list(discovered_lore_entries))
    }

# --- Save/Load ---
SAVE_FILE_PATH = "saved_game.json"

def save_game_to_file():
    """Saves the current game state to a file."""
    global game_map, player_hand, discovered_fusions, current_objective, discovered_lore_entries, discovered_biome_types, discovered_feature_types
    state = {
        "map": game_map.to_dict(),
        "hand": player_hand.to_dict(),
        "fusions": list(discovered_fusions),
        "objective_id": current_objective.id if current_objective else None,
        "objective_completed_status": current_objective.completed if current_objective else False,
        "lore": list(discovered_lore_entries),
        "biomes_discovered": list(discovered_biome_types),
        "features_discovered": list(discovered_feature_types),
    }
    try:
        with open(SAVE_FILE_PATH, "w") as f:
            json.dump(state, f, indent=4)
        print(f"Game saved to {SAVE_FILE_PATH}")
        return True
    except IOError as e:
        print(f"Error saving game: {e}")
        return False

def load_game_from_file():
    """Loads the game state from a file."""
    global game_map, player_hand, discovered_fusions, current_objective, PREDEFINED_OBJECTIVES
    global discovered_lore_entries, discovered_biome_types, discovered_feature_types, history_stack, redo_stack
    try:
        with open(SAVE_FILE_PATH, "r") as f:
            state = json.load(f)

        # Use _restore_globals_from_state for consistency if it covers all needed fields for loading
        # For now, direct restoration as before, plus history clearing:
        game_map = MapGrid.from_dict(state["map"])
        player_hand = PlayerHand.from_dict(state["hand"])
        discovered_fusions = set(state.get("fusions", []))

        discovered_lore_entries = set(state.get("lore", []))
        discovered_biome_types = set(state.get("biomes_discovered", [])) # Keep these separate from full state for now
        discovered_feature_types = set(state.get("features_discovered", [])) # Keep these separate

        # Clear history stacks when loading a game
        history_stack.clear()
        redo_stack.clear()

        obj_id = state.get("objective_id") # This was part of the old save state format
        obj_internal_dict = state.get("current_objective_internal") # Check for new format

        if obj_internal_dict: # Prefer new format if available
             current_objective = None
             if obj_internal_dict.get("id"):
                current_objective = Objective(
                    id=obj_internal_dict["id"],
                    description=obj_internal_dict["description"],
                    requirements=obj_internal_dict["requirements"],
                    completed=obj_internal_dict["completed"]
                )
             if current_objective and current_objective.completed:
                 print(f"Loaded objective '{current_objective.description}' was already completed. Generating a new one.")
                 generate_new_objective()
             elif current_objective:
                 _add_lore_entry("Objective", current_objective.description)
             else: # No valid objective in new format
                generate_new_objective()

        elif obj_id: # Fallback to old format
            obj_completed = state.get("objective_completed_status", False)
            current_objective = None # Reset
            found_obj_template = next((obj for obj in PREDEFINED_OBJECTIVES if obj.id == obj_id), None)
            if found_obj_template:
                current_objective = Objective(
                    id=found_obj_template.id,
                    description=found_obj_template.description,
                    requirements=found_obj_template.requirements,
                    completed=obj_completed
                )
                if current_objective.completed:
                    print(f"Loaded objective '{current_objective.description}' was already completed. Generating a new one.")
                    generate_new_objective()
                else:
                     _add_lore_entry("Objective", current_objective.description)
            else:
                print(f"Warning: Objective with ID '{obj_id}' not found. Generating a new one.")
                generate_new_objective()
        else: # No objective info at all
            generate_new_objective()


        print(f"Game loaded from {SAVE_FILE_PATH}")
        return True
    except (IOError, json.JSONDecodeError, KeyError, ValueError) as e: # Added ValueError for from_dict issues
        print(f"Error loading game: {e}. Initializing a new game.")
        initialize_game() # Fallback to new game, which also clears history
        return False

# Initialize game on module load
# initialize_game() # This call is removed, see logic at the very end of the file.
        obj_completed = state.get("objective_completed_status", False)

        current_objective = None # Reset
        if obj_id:
            found_obj_template = next((obj for obj in PREDEFINED_OBJECTIVES if obj.id == obj_id), None)
            if found_obj_template:
                current_objective = Objective(
                    id=found_obj_template.id,
                    description=found_obj_template.description,
                    requirements=found_obj_template.requirements,
                    completed=obj_completed
                )
                if current_objective.completed: # If loaded objective was already done
                    print(f"Loaded objective '{current_objective.description}' was already completed. Generating a new one.")
                    generate_new_objective() # Generate a new one
                else:
                     _add_lore_entry("Objective", current_objective.description) # Re-add lore if not completed
            else:
                print(f"Warning: Objective with ID '{obj_id}' not found in predefined objectives. Generating a new one.")
                generate_new_objective()
        else:
            generate_new_objective() # If no objective was saved

        print(f"Game loaded from {SAVE_FILE_PATH}")
        return True
    except (IOError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error loading game: {e}. Initializing a new game.")
        initialize_game() # Fallback to new game, which also clears history
        return False

# Initialize game on module load
# initialize_game() # Already called from the bottom of the try-except block in load_game_from_file if it fails
# or called directly if load is successful.
# However, it should be called if save file does not exist.
# The current structure: load_game_from_file tries, on failure it calls initialize_game()
# itself. So, we just need to call load_game_from_file() once.
# If it fails (no file, corrupt), it initializes a new game and returns False.
# If it succeeds, it loads the game and returns True.
# The initial `initialize_game()` call at the very beginning of the script ensures that
# if `load_game_from_file` isn't called or has issues, the game objects are at least defined.

load_game_from_file() # Attempt to load. If it fails, it initializes a new game.
