class Tile:
    """Represents a single tile on the game map."""
    def __init__(self, terrain_type="Empty"):
        self.terrain_type = terrain_type

    def __repr__(self):
        return f"Tile('{self.terrain_type}')"


class MapGrid:
    """Represents the game map as a grid of Tiles."""
    def __init__(self, width, height):
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("Width and height must be integers.")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive.")
        self.width = width
        self.height = height
        self.grid = self._initialize_grid()

    def _initialize_grid(self):
        """Initializes a 2D list of Tile objects."""
        return [[Tile() for _ in range(self.width)] for _ in range(self.height)]

    def get_tile(self, x, y):
        """Returns the Tile object at the given coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None  # Or raise an IndexError

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
