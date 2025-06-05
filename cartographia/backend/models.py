class Tile:
    """Represents a single tile on the game map."""
    # Define default elemental properties for terrain types
    TERRAIN_BASE_SATURATION = {
        "Empty": {'Earth': 0, 'Water': 0, 'Fire': 0, 'Air': 0, 'Life': 0, 'Decay': 0, 'Aether': 0},
        "Earth": {'Earth': 100, 'Water': 0, 'Fire': 0, 'Air': 0, 'Life': 10, 'Decay': 0, 'Aether': 0},
        "Water": {'Earth': 10, 'Water': 100, 'Fire': 0, 'Air': 0, 'Life': 5, 'Decay': 0, 'Aether': 0},
        "Forest": {'Earth': 50, 'Water': 20, 'Fire': 0, 'Air': 10, 'Life': 100, 'Decay': 5, 'Aether': 0},
        # Add other terrain types and their base saturations here
    }
    ALL_ELEMENTS = ['Earth', 'Water', 'Fire', 'Air', 'Life', 'Decay', 'Aether']


    def __init__(self, terrain_type="Empty", initial_saturation=None, elevation=0):
        self.terrain_type = terrain_type
        self.elevation = elevation
        if not isinstance(self.elevation, int):
            # Or raise ValueError, but for now, ensure it's int.
            print(f"Warning: Elevation '{self.elevation}' is not an int. Setting to 0.")
            self.elevation = 0
        self.elemental_saturation = self._initialize_saturation(terrain_type, initial_saturation)

    def _initialize_saturation(self, terrain_type, initial_saturation):
        """Initializes elemental saturation based on terrain type or direct input."""
        if initial_saturation is not None:
            if not isinstance(initial_saturation, dict):
                raise ValueError("initial_saturation must be a dictionary.")
            # Ensure all elements are present, defaulting to 0 if not provided
            saturations = {element: initial_saturation.get(element, 0) for element in self.ALL_ELEMENTS}
            return saturations

        # If terrain_type has a defined base saturation, use it
        if terrain_type in self.TERRAIN_BASE_SATURATION:
            return self.TERRAIN_BASE_SATURATION[terrain_type].copy()
        else:
            # Default to "Empty" like saturation if terrain_type is unknown
            print(f"Warning: Unknown terrain_type '{terrain_type}' for saturation initialization. Defaulting to Empty-like saturation.")
            return self.TERRAIN_BASE_SATURATION["Empty"].copy()

    def update_terrain_based_on_saturation(self):
        """
        Updates the tile's terrain_type based on its dominant elemental saturation.
        This is a placeholder for more complex logic. For now, it might not change
        terrain type or have very simple rules.
        """
        # Example: If Fire is dominant and high, change to "Scorched Earth"
        # if self.elemental_saturation['Fire'] > 70 and self.elemental_saturation['Fire'] >= self.elemental_saturation['Earth']:
        #     self.terrain_type = "Scorched Earth"
        # elif self.elemental_saturation['Water'] > 70 and self.elemental_saturation['Water'] >= self.elemental_saturation['Earth']:
        #     self.terrain_type = "Shallow Water" # or "River" depending on other factors
        # This logic will be expanded in a later subtask.

        original_terrain = self.terrain_type
        new_terrain = original_terrain # Default to no change

        # Highest saturation determines general type, with some combinations
        # Note: Order of these checks can matter if a tile qualifies for multiple types.
        # More specific combinations should usually come before general single-element types.

        water = self.elemental_saturation.get('Water', 0)
        earth = self.elemental_saturation.get('Earth', 0)
        fire = self.elemental_saturation.get('Fire', 0)
        life = self.elemental_saturation.get('Life', 0)
        decay = self.elemental_saturation.get('Decay', 0)
        # air = self.elemental_saturation.get('Air', 0)

        # --- Specific, Complex Biomes (usually checked first) ---
        if fire > 70 and earth > 50 and self.elevation > 1:
            new_terrain = "Volcano"
        elif life > 60 and earth > 30 and water > 40 and self.elevation <= 1: # Jungle needs more water
            new_terrain = "Jungle"
        elif life > 60 and earth > 30 and water < 40 and self.elevation <= 2: # Forest needs less water
            new_terrain = "Forest"
        elif water > 50 and decay > 30 and earth > 30 and self.elevation == 0:
            new_terrain = "Swamp"
        elif earth > 70 and fire > 30 and water < 10 and life < 20 and self.elevation <=2: # Desert is very dry
            new_terrain = "Desert"

        # --- Elevation-Specific Terrains (like Mountain) ---
        elif earth > 70 and self.elevation > 2: # Mountain (already exists)
            new_terrain = "Mountain"

        # --- General Elemental Dominance or Combinations ---
        elif water > 50 and earth > 20 and self.elevation == 0: # River (more specific than Shallow Water)
             new_terrain = "River"
        elif water > 60: # General water body
            new_terrain = "Shallow Water" # Could become "Lake" if large area, or based on depth (elevation diff)
        elif earth > 60: # General earthy terrain
            if self.elevation <= 2: # Non-mountain, non-volcano, non-desert earthy terrain
                 new_terrain = "Earth"
            # else: could be "Hills" or "Highlands" if earth > 60 but elevation > 2 but not Mountain
        elif fire > 60: # General fiery terrain (if not Volcano or Desert)
            new_terrain = "Scorched Earth"
        elif water > 40 and earth > 40: # Mud (if not River, Swamp, Jungle)
            new_terrain = "Mud"

        # --- Fallback/Default ---
        # If no specific rule is met, it might remain its current type,
        # or revert to a very basic type like "Empty" if saturations are all low.
        # For now, only change if a positive rule is met. If new_terrain is still original_terrain:
        else:
            # Consider a rule for "Empty" if all saturations are very low
            if earth < 10 and water < 10 and fire < 10 and life < 10 and decay < 10: # All key saturations low
                 new_terrain = "Empty"
            # Otherwise, (if no rule matched before this 'else' and not all saturations are low)
            # new_terrain remains what it was (either original_terrain or set by a previous rule in the chain if this 'else' was part of a larger if/elif/else).
            # Given the current structure, if it reaches this 'else', it means no prior biome rule matched.

        # This final check and terrain type assignment should be at the same indentation level
        # as the start of the main biome rule chain (e.g., the 'if fire > 70 ...' for Volcano).
        if new_terrain != original_terrain:
            self.terrain_type = new_terrain
            # print(f"DEBUG: Tile terrain updated from '{original_terrain}' to '{new_terrain}' due to saturation: {self.elemental_saturation}")
            return True
        return False

    def __repr__(self):
        # Limit saturation display for brevity in general repr
        # Show all elements for better debugging during this phase, can be reverted later.
        # displayed_saturation = {k: v for k, v in self.elemental_saturation.items() if v > 0}
        # if not displayed_saturation and any(self.elemental_saturation.values()): # handles all zeros
        #      displayed_saturation = "{all zeros}"
        # elif not displayed_saturation: # handles empty dict if ALL_ELEMENTS was empty
        #      displayed_saturation = "{}"
        displayed_saturation = self.elemental_saturation

        return f"Tile(terrain='{self.terrain_type}', elev={self.elevation}, saturation={displayed_saturation})"


class MapGrid:
    """Represents the game map as a grid of Tiles."""
    def __init__(self, width, height):
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("Width and height must be integers.")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive.")
        self.width = width
        self.height = height
        # The _initialize_grid method in MapGrid will now automatically use the new Tile constructor.
        # Tiles will be initialized as "Empty" by default, which in turn initializes their saturation
        # to all zeros according to the new Tile class logic.
        self.grid = self._initialize_grid()

    def _initialize_grid(self):
        """Initializes a 2D list of Tile objects."""
        # Tile() by default creates an "Empty" tile with corresponding saturation.
        return [[Tile() for _ in range(self.width)] for _ in range(self.height)]

    def get_tile(self, x, y):
        """Returns the Tile object at the given coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        # print(f"DEBUG: get_tile({x},{y}) out of bounds")
        return None

    def get_neighbors(self, x, y, include_diagonals=False):
        """
        Returns a list of valid Tile objects adjacent to the tile at (x, y).

        Args:
            x (int): The x-coordinate of the central tile.
            y (int): The y-coordinate of the central tile.
            include_diagonals (bool): Whether to include diagonal neighbors.

        Returns:
            list[Tile]: A list of neighboring Tile objects.
        """
        neighbors = []
        # Define potential relative coordinates for neighbors
        if include_diagonals:
            deltas = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        else: # Cardinal neighbors only
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            # Check if the neighbor coordinates are within the grid boundaries
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbor_tile = self.get_tile(nx, ny)
                if neighbor_tile: # Should always be true if coords are valid
                    neighbors.append(neighbor_tile)
        return neighbors

    def __repr__(self):
        return f"MapGrid(width={self.width}, height={self.height})"


class ElementalSeed:
    """Represents an elemental seed that players can use."""
    def __init__(self, name, description="A basic elemental seed."):
        if not isinstance(name, str) or not name:
            raise ValueError("Seed name must be a non-empty string.")
        self.name = name
        self.description = description

    def __repr__(self):
        return f"ElementalSeed(name='{self.name}')"

    def __eq__(self, other):
        if isinstance(other, ElementalSeed):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)


class PlayerHand:
    """Represents the player's hand of elemental seeds."""
    def __init__(self, initial_seeds=None):
        self.seeds = []
        if initial_seeds:
            for seed in initial_seeds:
                if not isinstance(seed, ElementalSeed):
                    raise TypeError("initial_seeds must be a list of ElementalSeed objects.")
                self.seeds.append(seed)

    def add_seed(self, seed):
        """Adds an ElementalSeed to the player's hand."""
        if not isinstance(seed, ElementalSeed):
            raise TypeError("Can only add ElementalSeed objects to hand.")
        self.seeds.append(seed)
        print(f"Added {seed} to hand. Current hand: {self.seeds}")


    def remove_seed(self, seed_name):
        """Removes an ElementalSeed from the player's hand by its name.
        Removes the first matching seed found.
        Returns True if a seed was removed, False otherwise.
        """
        if not isinstance(seed_name, str):
            raise TypeError("seed_name must be a string.")
        for i, seed_in_hand in enumerate(self.seeds):
            if seed_in_hand.name == seed_name:
                removed_seed = self.seeds.pop(i)
                print(f"Removed {removed_seed} from hand. Current hand: {self.seeds}")
                return True
        print(f"Seed '{seed_name}' not found in hand. Current hand: {self.seeds}")
        return False

    def get_hand_contents(self):
        """Returns a list of seed names in the hand."""
        return [seed.name for seed in self.seeds]

    def __repr__(self):
        return f"PlayerHand(seeds={self.seeds})"
