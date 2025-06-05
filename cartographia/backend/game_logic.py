import random
import copy
import json
from .models import MapGrid, ElementalSeed, PlayerHand, Tile, Objective

# --- Game State History for Undo/Redo ---
history_stack = []
redo_stack = []
MAX_HISTORY_SIZE = 10

# --- Save/Load Game Constant ---
SAVE_GAME_FILENAME = "saved_game.json"

# --- Element Properties & Interactions ---
ELEMENT_PROPERTIES = {
    "Fire": {"echo_factor": 0.6, "base_strength": 25},
    "Water": {"echo_factor": 0.4, "base_strength": 25},
    "Earth": {"echo_factor": 0.2, "base_strength": 30},
    "Life": {"echo_factor": 0.5, "base_strength": 20},
    "Decay": {"echo_factor": 0.3, "base_strength": 25},
    "Steam": {"echo_factor": 0.7, "base_strength": 30},
    "Stone": {"echo_factor": 0.1, "base_strength": 35},
    # Default if not listed: echo_factor 0.5, base_strength 25
}

TERRAIN_INTERACTIONS = {
    "Water": {"Fire": 0.5, "Water": 1.2, "Steam": 1.1, "Earth": 0.7},
    "Shallow Water": {"Fire": 0.6, "Water": 1.1, "Steam": 1.1, "Earth": 0.8},
    "River": {"Fire": 0.5, "Water": 1.3, "Steam": 1.2, "Earth": 0.6},
    "Earth": {"Fire": 1.0, "Water": 0.8, "Earth": 1.1, "Stone": 1.2},
    "Mountain": {"Fire": 1.2, "Water": 0.5, "Earth": 1.3, "Stone": 1.3},
    "Forest": {"Fire": 1.5, "Water": 0.9, "Life": 1.2, "Decay": 1.1},
    "Jungle": {"Fire": 1.3, "Water": 1.1, "Life": 1.3, "Decay": 1.2},
    "Desert": {"Fire": 1.2, "Water": 0.2, "Earth": 1.1},
    "Scorched Earth": {"Fire": 1.1, "Water": 0.7, "Decay": 1.2},
    "Volcano": {"Fire": 1.5, "Earth": 1.2, "Water": 0.3},
    "Swamp": {"Water": 1.1, "Decay": 1.3, "Fire": 0.7},
    "Mud": {"Water": 1.0, "Earth": 1.0},
}

# --- Elemental Fusion ---
ELEMENTAL_FUSION_RULES = {
    frozenset({"Fire", "Water"}): {"name": "Steam", "is_usable_seed": True, "description": "Hot, swirling vapor."},
    frozenset({"Earth", "Life"}): {"name": "Flora", "is_usable_seed": False, "description": "The essence of plant life."},
    frozenset({"Decay", "Life"}): {"name": "Fungus", "is_usable_seed": True, "description": "Rapidly spreading spores."},
    frozenset({"Earth", "Water"}): {"name": "Mud", "is_usable_seed": False, "description": "Soft, wet earth - a basic concept."},
    frozenset({"Fire", "Earth"}): {"name": "Lava", "is_usable_seed": True, "description": "Molten rock that reshapes landscapes."},
    frozenset({"Air", "Water"}): {"name": "Mist", "is_usable_seed": False, "description": "A veil of fine water droplets."},
    frozenset({"Air", "Fire"}): {"name": "Energy", "is_usable_seed": False, "description": "Raw, untamed power."},
    frozenset({"Earth", "Earth"}): {"name": "Stone", "is_usable_seed": True, "description": "Solid, enduring matter."},
    frozenset({"Steam", "Earth"}): {"name": "Geyser", "is_usable_seed": True, "description": "A burst of steam from the earth."}
}
discovered_fusions = set()

# --- Objectives ---
PREDEFINED_OBJECTIVES = [
    Objective(id="obj_mt_rv", description="Forge a land with at least 2 Mountains and 1 River.", requirements={"Mountain": 2, "River": 1}),
    Objective(id="obj_fr_ds", description="Cultivate 3 Forests and sculpt 1 Desert.", requirements={"Forest": 3, "Desert": 1}),
    Objective(id="obj_vlcn", description="Summon a mighty Volcano.", requirements={"Volcano": 1}),
    Objective(id="obj_sw_jg", description="Nurture a Swamp and a Jungle.", requirements={"Swamp": 1, "Jungle": 1})
]
current_objective: Objective | None = None

def generate_new_objective():
    global current_objective
    if PREDEFINED_OBJECTIVES:
        chosen_objective_template = random.choice(PREDEFINED_OBJECTIVES)
        current_objective = Objective(
            id=chosen_objective_template.id,
            description=chosen_objective_template.description,
            requirements=copy.deepcopy(chosen_objective_template.requirements),
            completed=False
        )
        print(f"New objective generated: {current_objective.description}")
    else:
        current_objective = None
        print("No predefined objectives available.")

DEFAULT_MAP_WIDTH = 10
DEFAULT_MAP_HEIGHT = 10
game_map = MapGrid(DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT)

player_hand = PlayerHand(initial_seeds=[
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Earth", description="A seed of terrestrial power."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Water", description="A seed of aquatic essence."),
    ElementalSeed(name="Fire", description="A seed of conflagration.")
])

def _deep_copy_game_state(game_map_instance: MapGrid, player_hand_instance: PlayerHand):
    try:
        copied_map = copy.deepcopy(game_map_instance)
        copied_hand = copy.deepcopy(player_hand_instance)
        return {'map': copied_map, 'hand': copied_hand}
    except Exception as e:
        print(f"Error during deep copy: {e}")
        raise

def _save_state_for_undo(current_game_map: MapGrid, current_player_hand: PlayerHand):
    global history_stack, redo_stack, MAX_HISTORY_SIZE
    copied_state = _deep_copy_game_state(current_game_map, current_player_hand)
    history_stack.append(copied_state)
    if len(history_stack) > MAX_HISTORY_SIZE:
        history_stack.pop(0)
    redo_stack.clear()
    print(f"State saved for undo. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")

def apply_element_to_tile(current_game_map: MapGrid, hand_instance: PlayerHand, x: int, y: int, element_name: str, strength: int = -1) -> bool:
    _save_state_for_undo(current_game_map, hand_instance)

    tile = current_game_map.get_tile(x, y)
    if not tile:
        print(f"Error: No tile at coordinates ({x},{y}). Cannot apply '{element_name}'.")
        return False

    # This check is commented out to allow derived elements:
    # if element_name not in Tile.ALL_ELEMENTS:
    #     print(f"Warning: Element '{element_name}' is not a recognized element type. Cannot apply to tile ({x},{y}).")
    #     return False

    if not hand_instance.has_seed(element_name):
        print(f"Error: Seed '{element_name}' not in player's hand. Cannot apply.")
        return False

    if not hand_instance.remove_seed(element_name):
        print(f"Error: Failed to remove seed '{element_name}' from hand.")
        return False

    element_props = ELEMENT_PROPERTIES.get(element_name, {})
    current_strength = strength if strength != -1 else element_props.get("base_strength", 25)

    print(f"\nSuccessfully consumed '{element_name}' seed. Applying effect (original strength {current_strength}) to tile ({x},{y}) with terrain '{tile.terrain_type}'. Initial state: {tile}")

    terrain_modifiers = TERRAIN_INTERACTIONS.get(tile.terrain_type, {})
    interaction_modifier = terrain_modifiers.get(element_name, 1.0)
    effective_strength = int(current_strength * interaction_modifier)
    print(f"Interaction: '{element_name}' on '{tile.terrain_type}' (modifier: {interaction_modifier}). Effective strength: {effective_strength}")

    current_saturation = tile.elemental_saturation.get(element_name, 0)
    new_saturation = min(100, current_saturation + effective_strength)
    new_saturation = max(0, new_saturation)
    tile.elemental_saturation[element_name] = new_saturation

    print(f"Saturation for '{element_name}' on primary tile ({x},{y}) updated to {new_saturation}. Current saturations: {tile.elemental_saturation}")

    terrain_before_update = tile.terrain_type
    primary_terrain_changed = tile.update_terrain_based_on_saturation()

    if primary_terrain_changed:
        print(f"Success! Primary tile ({x},{y}) terrain changed from '{terrain_before_update}' to '{tile.terrain_type}'.")
    else:
        print(f"Primary tile ({x},{y}) terrain remains '{tile.terrain_type}'.")

    echo_factor = element_props.get("echo_factor", 0.5)
    echo_strength = int(current_strength * echo_factor)

    if echo_strength > 0:
        neighbors = current_game_map.get_neighbors(x, y)
        print(f"Applying echo of '{element_name}' (base strength {current_strength}, factor {echo_factor} -> echo_strength {echo_strength}) to {len(neighbors)} neighbors.")
        for i, neighbor_tile in enumerate(neighbors):
            original_neighbor_terrain = neighbor_tile.terrain_type
            neighbor_terrain_modifiers = TERRAIN_INTERACTIONS.get(original_neighbor_terrain, {})
            neighbor_interaction_modifier = neighbor_terrain_modifiers.get(element_name, 1.0)
            effective_echo_strength = int(echo_strength * neighbor_interaction_modifier)

            neighbor_current_saturation = neighbor_tile.elemental_saturation.get(element_name, 0)
            neighbor_new_saturation = min(100, neighbor_current_saturation + effective_echo_strength)
            neighbor_new_saturation = max(0, neighbor_new_saturation)
            neighbor_tile.elemental_saturation[element_name] = neighbor_new_saturation

            neighbor_terrain_before_update = neighbor_tile.terrain_type
            neighbor_terrain_changed = neighbor_tile.update_terrain_based_on_saturation()
            if neighbor_terrain_changed:
                print(f"    Success! Neighbor {i+1} (originally {neighbor_terrain_before_update}) terrain changed to '{neighbor_tile.terrain_type}'.")
    else:
        print("Echo strength is 0, skipping neighbor effects.")

    if random.random() < 0.15:
        if Tile.ALL_ELEMENTS:
            awarded_seed_name = random.choice(Tile.ALL_ELEMENTS)
            awarded_seed = ElementalSeed(name=awarded_seed_name, description="A mysteriously found seed.")
            print(f"Player found a new seed! Attempting to add '{awarded_seed_name}' to hand...")
            if hand_instance.add_seed(awarded_seed):
                print(f"Successfully added '{awarded_seed_name}' seed to player's hand.")
            else:
                print(f"Could not add '{awarded_seed_name}' seed (hand likely full).")
        else:
            print("Warning: Tile.ALL_ELEMENTS is empty, cannot award a random seed.")

    global current_objective
    if current_objective and not current_objective.completed:
        if current_objective.check_completion(current_game_map):
            print(f"Objective '{current_objective.description}' completed!")
            generate_new_objective()

    return True

def undo_last_action() -> bool:
    global game_map, player_hand, history_stack, redo_stack, MAX_HISTORY_SIZE
    if not history_stack:
        print("Undo failed: No history available.")
        return False
    state_to_redo = _deep_copy_game_state(game_map, player_hand)
    redo_stack.append(state_to_redo)
    if len(redo_stack) > MAX_HISTORY_SIZE:
        redo_stack.pop(0)
    last_saved_state = history_stack.pop()
    restored_map_obj = copy.deepcopy(last_saved_state['map'])
    game_map.width = restored_map_obj.width
    game_map.height = restored_map_obj.height
    game_map.grid = restored_map_obj.grid
    restored_hand_obj = copy.deepcopy(last_saved_state['hand'])
    player_hand.seeds = restored_hand_obj.seeds
    player_hand.max_hand_size = restored_hand_obj.max_hand_size
    print(f"Undo successful. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")
    return True

def redo_next_action() -> bool:
    global game_map, player_hand, history_stack, redo_stack, MAX_HISTORY_SIZE
    if not redo_stack:
        print("Redo failed: No actions to redo.")
        return False
    state_to_undo_again = _deep_copy_game_state(game_map, player_hand)
    history_stack.append(state_to_undo_again)
    if len(history_stack) > MAX_HISTORY_SIZE:
        history_stack.pop(0)
    next_state_to_restore = redo_stack.pop()
    restored_map_obj = copy.deepcopy(next_state_to_restore['map'])
    game_map.width = restored_map_obj.width
    game_map.height = restored_map_obj.height
    game_map.grid = restored_map_obj.grid
    restored_hand_obj = copy.deepcopy(next_state_to_restore['hand'])
    player_hand.seeds = restored_hand_obj.seeds
    player_hand.max_hand_size = restored_hand_obj.max_hand_size
    print(f"Redo successful. History size: {len(history_stack)}, Redo size: {len(redo_stack)}")
    return True

def save_game_to_file(filename: str = SAVE_GAME_FILENAME):
    global game_map, player_hand, discovered_fusions, current_objective # Added current_objective
    try:
        game_state_data = {
            'map': game_map.to_dict(),
            'hand': player_hand.to_dict(),
            'discovered_fusions': list(discovered_fusions),
            'current_objective_id': current_objective.id if current_objective else None,
            'current_objective_completed_status': current_objective.completed if current_objective else None
        }
        with open(filename, 'w') as f:
            json.dump(game_state_data, f, indent=4)
        print(f"Game state saved successfully to {filename}")
        return True
    except Exception as e:
        print(f"Error saving game to file {filename}: {e}")
        return False

def load_game_from_file(filename: str = SAVE_GAME_FILENAME) -> bool:
    global game_map, player_hand, history_stack, redo_stack, discovered_fusions, current_objective
    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
        if 'map' not in loaded_data or 'hand' not in loaded_data:
            print(f"Error: Invalid save data structure in {filename} (missing map or hand).")
            return False
        new_map = MapGrid.from_dict(loaded_data['map'])
        new_hand = PlayerHand.from_dict(loaded_data['hand'])
        loaded_fusions = set(loaded_data.get('discovered_fusions', []))

        game_map.width = new_map.width
        game_map.height = new_map.height
        game_map.grid = new_map.grid
        player_hand.seeds = new_hand.seeds
        player_hand.max_hand_size = new_hand.max_hand_size
        discovered_fusions.clear()
        discovered_fusions.update(loaded_fusions)
        history_stack.clear()
        redo_stack.clear()

        loaded_objective_id = loaded_data.get('current_objective_id')
        loaded_objective_completed_status = loaded_data.get('current_objective_completed_status', False)

        if loaded_objective_id:
            found_objective_template = next((obj_template for obj_template in PREDEFINED_OBJECTIVES if obj_template.id == loaded_objective_id), None)
            if found_objective_template:
                current_objective = Objective(
                    id=found_objective_template.id,
                    description=found_objective_template.description,
                    requirements=copy.deepcopy(found_objective_template.requirements),
                    completed=loaded_objective_completed_status
                )
                print(f"Loaded objective: {current_objective.description}, Completed: {current_objective.completed}")
            else:
                print(f"Warning: Objective ID '{loaded_objective_id}' from save file not found. Generating new one.")
                generate_new_objective()
        else:
            print("No objective ID in save file. Generating new one.")
            generate_new_objective()

        print(f"Game state loaded successfully from {filename}. Undo/redo history cleared. Discovered fusions: {discovered_fusions}")

        if current_objective and current_objective.completed:
            print(f"The current objective '{current_objective.description}' is completed. Generating a new one immediately.")
            generate_new_objective()

        return True
    except FileNotFoundError:
        print(f"Error: Save file {filename} not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. File might be corrupted.")
        return False
    except ValueError as ve:
        print(f"Error: Invalid data format in save file {filename}: {ve}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred loading game from file {filename}: {e}")
        return False

def get_game_state():
    global current_objective
    map_details = {
        "width": game_map.width,
        "height": game_map.height,
        "tiles": [[tile.to_dict() for tile in row] for row in game_map.grid]
    }
    hand_details = get_player_hand_details()
    objective_data = None
    if current_objective:
        objective_data = current_objective.to_dict()
    return {
        "map_details": map_details,
        "player_hand": hand_details["seeds"],
        "player_hand_count": hand_details["count"],
        "current_objective": objective_data,
        "discovered_fusions": sorted(list(discovered_fusions))
    }

def fuse_elements_logic(hand_instance: PlayerHand, element1_name: str, element2_name: str) -> dict:
    global discovered_fusions, ELEMENTAL_FUSION_RULES, game_map

    _save_state_for_undo(game_map, hand_instance) # Save state before any hand modification

    if element1_name == element2_name:
        current_count = sum(1 for seed in hand_instance.seeds if seed.name == element1_name)
        if current_count < 2:
            # history_stack.pop() # Optional: pop invalid action state (but what if user wants to undo to "before trying to fuse"?)
            return {"success": False, "message": f"You need at least two '{element1_name}' seeds to fuse them."}
    elif not (hand_instance.has_seed(element1_name) and hand_instance.has_seed(element2_name)):
        # history_stack.pop()
        return {"success": False, "message": "You don't have the required seeds."}

    if not hand_instance.remove_seed(element1_name):
        # history_stack.pop()
        return {"success": False, "message": f"Failed to remove first seed {element1_name}."}

    if not hand_instance.remove_seed(element2_name):
        hand_instance.add_seed(ElementalSeed(name=element1_name, description="Restored after failed fusion attempt.")) # Rollback
        # history_stack.pop() # State changed (added seed back), then changed again by pop. Better to let undo handle.
        return {"success": False, "message": f"Failed to remove second seed {element2_name} after removing first."}

    fusion_key = frozenset({element1_name, element2_name})
    rule_result = ELEMENTAL_FUSION_RULES.get(fusion_key)
    message = ""
    if rule_result:
        result_name = rule_result["name"]
        discovered_fusions.add(result_name)
        if rule_result.get("is_usable_seed", False):
            new_seed = ElementalSeed(name=result_name, description=rule_result.get("description", "A newly discovered seed."))
            if hand_instance.add_seed(new_seed):
                message = f"You combined {element1_name} and {element2_name} to create a {result_name} seed!"
            else:
                message = f"You combined {element1_name} and {element2_name} to discover {result_name}, but your hand is full!"
        else:
            message = f"You combined {element1_name} and {element2_name} to discover the concept of {result_name}!"
        # _save_state_for_undo was already called.
        return {"success": True, "result_name": result_name, "message": message, "is_seed": rule_result.get("is_usable_seed", False)}
    else:
        message = "These elements do not seem to react."
        # _save_state_for_undo was already called.
        return {"success": False, "message": message}

def get_player_hand_details():
    return {
        "seeds": player_hand.get_hand_contents(),
        "count": len(player_hand.seeds)
    }

generate_new_objective()
