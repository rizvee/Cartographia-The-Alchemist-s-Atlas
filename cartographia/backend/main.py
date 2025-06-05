from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

# Import game logic functions and current game state variables
from .game_logic import (
    get_game_state,
    apply_element_to_tile,
    fuse_elements_logic,
    save_game_to_file,
    load_game_from_file,
    initialize_game,
    undo_last_action,
    redo_next_action
)

app = FastAPI(
    title="Cartographia: The Alchemist's Atlas API",
    description="API for managing the elemental alchemy game.",
    version="0.1.0",
)

# --- Request Models ---
class ApplyElementRequest(BaseModel):
    x: int
    y: int
    element_name: str

class FuseElementsRequest(BaseModel):
    element1_name: str
    element2_name: str

# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    Currently, this ensures the game is initialized when the server starts.
    """
    print("Application starting up... Initializing game state.")
    initialize_game() # Ensures game state is fresh on server start, or loads if save exists and load_game_from_file handles it


@app.get("/api/game_state", summary="Get Current Game State", response_description="The current state of the game map, player hand, and objectives.")
async def get_current_game_state() -> Dict:
    """
    Retrieves the complete current state of the game, including the map,
    player's hand, current objective, and any discovered lore or fusions.
    """
    return get_game_state()

@app.post("/api/apply_element", summary="Apply Element to Tile", response_description="The updated game state after applying the element.")
async def post_apply_element(request: ApplyElementRequest) -> Dict:
    """
    Applies a specified element to a target tile on the map.
    This action can alter the tile's terrain and elemental saturation,
    potentially affecting neighboring tiles and triggering game events.
    Consumes an elemental seed from the player's hand.
    """
    try:
        # Assuming apply_element_to_tile now returns a more comprehensive status or just True/False
        # and the game state is the ultimate source of truth.
        action_performed = apply_element_to_tile(request.x, request.y, request.element_name)
        # The original version returned 'terrain_changed_primary' (bool)
        # Let's assume for now that if it doesn't raise an error, it was "successful" in some way.
        # The client will rely on the returned game_state to see the effects.
        if not action_performed: # This condition might need adjustment based on apply_element_to_tile's return
            # If apply_element_to_tile returns False for "no change" but still valid,
            # we might not want to raise an HTTP error.
            # For now, let's assume False means something went wrong (e.g. no seed, bad coords)
            # that wasn't an exception but an expected failure.
            # The print statements in game_logic will indicate issues.
            # The game_logic.py should be modified to raise specific exceptions for API handling.
            # For now, we just return the state. If it was a "silent" failure (e.g. no seed),
            # the state won't have changed as expected by the player.
            pass # Continue to return game state

        return get_game_state()
    except Exception as e:
        # This is a general catch-all. Specific exceptions from game_logic would be better.
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/fuse_elements", summary="Fuse Elemental Seeds", response_description="Result of the fusion attempt and updated game state.")
async def post_fuse_elements(request: FuseElementsRequest) -> Dict:
    """
    Attempts to fuse two elemental seeds from the player's hand.
    If successful, a new element or item may be created, and seeds are consumed.
    The result of the fusion (e.g., new seed, message) is returned along with
    the updated game state.
    """
    try:
        fusion_result = fuse_elements_logic(request.element1_name, request.element2_name)
        # The fusion_result from game_logic is a dict: {'success': bool, 'message': str, 'new_seed_name': Optional[str]}
        # We should return this information along with the game state.
        current_state = get_game_state()
        current_state["last_fusion_result"] = fusion_result # Add fusion result to the response
        return current_state
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/save_map", summary="Save Game State", response_description="Confirmation message of the save operation.")
async def post_save_game():
    """
    Saves the current game state (map, player hand, objectives, etc.) to a persistent file.
    """
    if save_game_to_file():
        return {"message": "Game saved successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to save game.")

@app.post("/api/load_map", summary="Load Game State", response_description="The loaded game state.")
async def post_load_game() -> Dict:
    """
    Loads a previously saved game state from a file, replacing the current session's state.
    Returns the newly loaded game state.
    """
    if load_game_from_file():
        return get_game_state()
    else:
        # If loading fails, initialize_game() is called in game_logic, so return that fresh state.
        # Consider if a different HTTP status is more appropriate for "failed load, new game started".
        # For now, 200 with the new game state is returned.
        # raise HTTPException(status_code=500, detail="Failed to load game. A new game has been started.")
        return get_game_state()

@app.post("/api/reset_game", summary="Reset Game State", response_description="The fresh game state after reset.")
async def post_reset_game() -> Dict:
    """
    Resets the game to its initial state, clearing all progress.
    """
    initialize_game()
    return get_game_state()

@app.post("/api/undo", summary="Undo Last Action", response_description="The game state after undoing the last action.")
async def post_undo():
    """
    Reverts the game state to before the last action was performed.
    If there is no action to undo, an error is returned.
    """
    if undo_last_action():
        return get_game_state()
    else:
        # Consider more specific error messages based on why undo_last_action failed (e.g., empty stack)
        raise HTTPException(status_code=400, detail="Nothing to undo or undo failed.")

@app.post("/api/redo", summary="Redo Last Undone Action", response_description="The game state after redoing the last undone action.")
async def post_redo():
    """
    Reapplies the last action that was undone.
    If there is no action to redo, an error is returned.
    """
    if redo_next_action():
        return get_game_state()
    else:
        # Consider more specific error messages
        raise HTTPException(status_code=400, detail="Nothing to redo or redo failed.")

# To run this FastAPI app:
# 1. Ensure FastAPI and Uvicorn are installed: pip install fastapi uvicorn
# 2. Navigate to the directory containing `cartographia` (i.e., the parent of `cartographia`)
# 3. Run: uvicorn cartographia.backend.main:app --reload
#    (If your project root is `cartographia`, then from inside `cartographia/backend` run `uvicorn main:app --reload`
#     but the path for imports `from .game_logic` implies main.py is inside a package `backend`)

# Assuming the project structure is:
# project_root/
#   cartographia/
#     backend/
#       __init__.py  (empty, makes 'backend' a package)
#       main.py
#       game_logic.py
#       models.py
#     frontend/
#       ...
# You would run uvicorn from `project_root`.
# If `cartographia` is the root, then `backend` is a top-level package.

# Add __init__.py to backend to make it a package
# This is done by the agent in a separate step if needed.
