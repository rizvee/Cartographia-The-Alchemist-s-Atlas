class Tile:
    """Represents a single tile on the game map."""
    TERRAIN_BASE_SATURATION = {
        "Empty": {'Earth': 0, 'Water': 0, 'Fire': 0, 'Air': 0, 'Life': 0, 'Decay': 0, 'Aether': 0},
        "Earth": {'Earth': 100, 'Water': 0, 'Fire': 0, 'Air': 0, 'Life': 10, 'Decay': 0, 'Aether': 0},
        "Water": {'Earth': 10, 'Water': 100, 'Fire': 0, 'Air': 0, 'Life': 5, 'Decay': 0, 'Aether': 0},
        "Forest": {'Earth': 50, 'Water': 20, 'Fire': 0, 'Air': 10, 'Life': 100, 'Decay': 5, 'Aether': 0},
    }
    ALL_ELEMENTS = ['Earth', 'Water', 'Fire', 'Air', 'Life', 'Decay', 'Aether']

    def __init__(self, terrain_type="Empty", initial_saturation=None, elevation=0, feature: str | None = None):
        self.terrain_type = terrain_type
        self.elevation = elevation
        self.feature = feature # New attribute
        if not isinstance(self.elevation, int):
            print(f"Warning: Elevation '{self.elevation}' is not an int. Setting to 0.")
            self.elevation = 0
        if self.feature is not None and not isinstance(self.feature, str):
            print(f"Warning: Feature '{self.feature}' is not a string. Setting to None.")
            self.feature = None
        self.elemental_saturation = self._initialize_saturation(terrain_type, initial_saturation)

    def _initialize_saturation(self, terrain_type, initial_saturation):
        if initial_saturation is not None:
            if not isinstance(initial_saturation, dict):
                raise ValueError("initial_saturation must be a dictionary.")
            return {element: initial_saturation.get(element, 0) for element in self.ALL_ELEMENTS}
        if terrain_type in self.TERRAIN_BASE_SATURATION:
            return self.TERRAIN_BASE_SATURATION[terrain_type].copy()
        else:
            print(f"Warning: Unknown terrain_type '{terrain_type}' for saturation init. Defaulting to Empty.")
            return self.TERRAIN_BASE_SATURATION["Empty"].copy()

    def update_terrain_based_on_saturation(self):
        original_terrain = self.terrain_type
        new_terrain = original_terrain
        water = self.elemental_saturation.get('Water', 0)
        earth = self.elemental_saturation.get('Earth', 0)
        fire = self.elemental_saturation.get('Fire', 0)
        life = self.elemental_saturation.get('Life', 0)
        decay = self.elemental_saturation.get('Decay', 0)

        if fire > 70 and earth > 50 and self.elevation > 1: new_terrain = "Volcano"
        elif life > 60 and earth > 30 and water > 40 and self.elevation <= 1: new_terrain = "Jungle"
        elif life > 60 and earth > 30 and water < 40 and self.elevation <= 2: new_terrain = "Forest"
        elif water > 50 and decay > 30 and earth > 30 and self.elevation == 0: new_terrain = "Swamp"
        elif earth > 70 and fire > 30 and water < 10 and life < 20 and self.elevation <=2: new_terrain = "Desert"
        elif earth > 70 and self.elevation > 2: new_terrain = "Mountain"
        elif water > 50 and earth > 20 and self.elevation == 0: new_terrain = "River"
        elif water > 60: new_terrain = "Shallow Water"
        elif earth > 60:
            if self.elevation <= 2: new_terrain = "Earth"
        elif fire > 60: new_terrain = "Scorched Earth"
        elif water > 40 and earth > 40: new_terrain = "Mud"
        else:
            if earth < 10 and water < 10 and fire < 10 and life < 10 and decay < 10: new_terrain = "Empty"

        if new_terrain != original_terrain:
            self.terrain_type = new_terrain
            return True
        return False

    def __repr__(self):
        return f"Tile(terrain='{self.terrain_type}', elev={self.elevation}, saturation={self.elemental_saturation})"

    def to_dict(self):
        return {
            'terrain_type': self.terrain_type,
            'elemental_saturation': self.elemental_saturation.copy(),
            'elevation': self.elevation
        }

    @staticmethod
    def from_dict(data):
        if not all(k in data for k in ['terrain_type', 'elemental_saturation', 'elevation']):
            raise ValueError(f"Invalid data for Tile deserialization: {data}")
        return Tile(
            terrain_type=data['terrain_type'],
            initial_saturation=data['elemental_saturation'],
            elevation=data['elevation']
        )

class MapGrid:
    def __init__(self, width, height):
        if not isinstance(width, int) or not isinstance(height, int): raise TypeError("Width/height must be int.")
        if width <= 0 or height <= 0: raise ValueError("Width/height must be positive.")
        self.width = width
        self.height = height
        self.grid = [[Tile() for _ in range(self.width)] for _ in range(self.height)]

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height: return self.grid[y][x]
        return None

    def get_neighbors(self, x, y, include_diagonals=False):
        neighbors = []
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)] if not include_diagonals else \
                 [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if tile := self.get_tile(nx, ny): neighbors.append(tile)
        return neighbors

    def __repr__(self):
        return f"MapGrid(width={self.width}, height={self.height})"

    def to_dict(self):
        return {
            'width': self.width,
            'height': self.height,
            'grid': [[tile.to_dict() for tile in row] for row in self.grid]
        }

    @staticmethod
    def from_dict(data):
        if not all(k in data for k in ['width', 'height', 'grid']):
            raise ValueError(f"Invalid data for MapGrid deserialization: {data}")
        new_map = MapGrid(data['width'], data['height'])
        if len(data['grid']) != new_map.height or \
           (new_map.height > 0 and len(data['grid'][0]) != new_map.width):
            raise ValueError("Grid dimensions in data do not match MapGrid dimensions.")
        new_map.grid = [[Tile.from_dict(td) for td in row_data] for row_data in data['grid']]
        return new_map

class ElementalSeed:
    def __init__(self, name, description="A basic elemental seed."):
        if not isinstance(name, str) or not name: raise ValueError("Seed name must be non-empty string.")
        self.name = name
        self.description = description

    def __repr__(self): return f"ElementalSeed(name='{self.name}')"
    def __eq__(self, other): return isinstance(other, ElementalSeed) and self.name == other.name
    def __hash__(self): return hash(self.name)

    def to_dict(self):
        return {'name': self.name, 'description': self.description}

    @staticmethod
    def from_dict(data):
        if not all(k in data for k in ['name', 'description']):
            raise ValueError(f"Invalid data for ElementalSeed deserialization: {data}")
        return ElementalSeed(name=data['name'], description=data['description'])

class PlayerHand:
    def __init__(self, initial_seeds=None, max_hand_size=10):
        self.seeds = []
        self.max_hand_size = max_hand_size
        if initial_seeds:
            for seed in initial_seeds:
                if len(self.seeds) < self.max_hand_size:
                    if not isinstance(seed, ElementalSeed): raise TypeError("Initial_seeds must be list of ElementalSeed.")
                    self.seeds.append(seed)
                else:
                    print(f"Warning: Hand full (max {self.max_hand_size}). Cannot add initial seed: {seed}")
                    break
        print(f"PlayerHand initialized. Max size: {self.max_hand_size}. Initial hand: {self.seeds}")

    def add_seed(self, seed: ElementalSeed) -> bool:
        if not isinstance(seed, ElementalSeed):
            print(f"Error: Invalid seed type: {type(seed)}")
            return False
        if len(self.seeds) >= self.max_hand_size:
            print(f"Hand full (max {self.max_hand_size}). Cannot add: {seed}. Hand: {self.seeds}")
            return False
        self.seeds.append(seed)
        print(f"Added {seed} to hand. Hand: {self.seeds}")
        return True

    def remove_seed(self, seed_name):
        if not isinstance(seed_name, str): raise TypeError("seed_name must be str.")
        for i, seed_in_hand in enumerate(self.seeds):
            if seed_in_hand.name == seed_name:
                removed_seed = self.seeds.pop(i)
                print(f"Removed {removed_seed} from hand. Hand: {self.seeds}")
                return True
        print(f"Seed '{seed_name}' not in hand. Hand: {self.seeds}")
        return False

    def get_hand_contents(self): return [seed.name for seed in self.seeds]
    def has_seed(self, seed_name: str) -> bool:
        if not isinstance(seed_name, str): return False
        return any(s.name == seed_name for s in self.seeds)
    def __repr__(self): return f"PlayerHand(seeds={self.seeds})"

    def to_dict(self):
        return {
            'seeds': [seed.to_dict() for seed in self.seeds],
            'max_hand_size': self.max_hand_size
        }

    @staticmethod
    def from_dict(data):
        if not all(k in data for k in ['seeds', 'max_hand_size']):
            raise ValueError(f"Invalid data for PlayerHand deserialization: {data}")
        loaded_seeds = [ElementalSeed.from_dict(sd) for sd in data['seeds']]
        return PlayerHand(initial_seeds=loaded_seeds, max_hand_size=data['max_hand_size'])

class Objective:
    """Represents a player objective in the game."""
    def __init__(self, id: str, description: str, requirements: dict, completed: bool = False):
        if not id or not isinstance(id, str):
            raise ValueError("Objective ID must be a non-empty string.")
        if not description or not isinstance(description, str):
            raise ValueError("Objective description must be a non-empty string.")
        if not isinstance(requirements, dict):
            raise ValueError("Objective requirements must be a dictionary.")

        self.id = id
        self.description = description
        self.requirements = requirements # e.g., {"Mountain": 2, "River": 1}
        self.completed = completed

    def __repr__(self):
        return (f"Objective(id='{self.id}', description='{self.description}', "
                f"requirements={self.requirements}, completed={self.completed})")

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'requirements': self.requirements.copy(), # Return a copy
            'completed': self.completed
        }

    def check_completion(self, game_map_instance) -> bool:
        """
        Checks if the objective's requirements are met based on the current game map.
        If met, sets self.completed to True and returns True. Otherwise, returns False.
        """
        if self.completed: # Already completed
            return True

        terrain_counts = {}
        for row in game_map_instance.grid:
            for tile in row:
                terrain_counts[tile.terrain_type] = terrain_counts.get(tile.terrain_type, 0) + 1

        all_requirements_met = True
        for terrain, required_count in self.requirements.items():
            if terrain_counts.get(terrain, 0) < required_count:
                all_requirements_met = False
                break

        if all_requirements_met:
            self.completed = True
            print(f"Objective '{self.id}' requirements met and marked as completed.")
            return True

        return False

    # No from_dict needed if we always create from predefined templates and then copy for current_objective.
    # If objectives were to be saved/loaded independently (e.g. player progress on objectives),
    # then a from_dict method would be useful here.
