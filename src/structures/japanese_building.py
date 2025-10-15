"""Traditional Japanese-style building implementation."""

from panda3d.core import Vec3, Vec4

from .building import Building, BuildingPiece, CurvedRoofPiece


class JapaneseBuilding(Building):
    """A traditional Japanese-style building with characteristic architectural features.

    Features:
    - Raised wooden floor/platform
    - Wide overhanging roof (deep eaves)
    - Sliding door openings (engawa/veranda style)
    - Shoji-style window openings
    - Natural wood colors
    - Lower profile, horizontal emphasis
    """

    def __init__(self, world, render, position, width=12, depth=10, height=6, name="japanese_building"):
        """Create a traditional Japanese-style building.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 base position
            width: Building width (X axis) - typically wider than Western buildings
            depth: Building depth (Y axis)
            height: Building height (Z axis) - typically lower than Western buildings
            name: Building identifier
        """
        super().__init__(world, render, position, name)

        # Traditional Japanese color palette
        wood_color = Vec4(0.55, 0.35, 0.25, 1.0)  # Dark natural wood
        light_wood_color = Vec4(0.75, 0.6, 0.45, 1.0)  # Light wood for walls
        roof_color = Vec4(0.25, 0.25, 0.28, 1.0)  # Dark gray (traditional tile/thatch)
        foundation_color = Vec4(0.5, 0.5, 0.5, 1.0)  # Stone gray

        wall_thickness = 0.3  # Thinner walls (traditional construction)
        wall_height = height
        wall_mass = 15.0  # Lighter construction

        # Corner overlap
        corner_overlap = wall_thickness

        # Japanese buildings have a raised floor platform
        platform_height = 0.8
        platform_color = Vec4(0.6, 0.45, 0.35, 1.0)  # Medium wood tone

        # Create stone foundation
        foundation = BuildingPiece(
            world,
            render,
            position,
            Vec3(width + 1, depth + 1, 0.6),
            0,  # Mass 0 = static
            foundation_color,
            f"{name}_foundation",
            "foundation",
        )
        self.add_piece(foundation)

        # Create raised wooden platform/floor
        platform = BuildingPiece(
            world,
            render,
            position + Vec3(0, 0, 0.3 + platform_height / 2),
            Vec3(width, depth, platform_height),
            0,  # Static
            platform_color,
            f"{name}_platform",
            "foundation",  # Treat as foundation for stability
        )
        self.add_piece(platform)

        # Adjust wall base height to sit on platform
        wall_base_z = 0.3 + platform_height

        # Sliding door/opening dimensions (wider than Western doors)
        door_width = 3.5  # Wide sliding opening
        door_height = 3.0  # Lower than Western doors

        # Front wall (negative Y) - split for wide sliding door opening
        front_y = -depth / 2

        # Left segment of front wall
        left_segment_width = (width + 2 * corner_overlap - door_width) / 2
        left_segment_x = -(width + 2 * corner_overlap) / 2 + left_segment_width / 2

        front_wall_left = BuildingPiece(
            world,
            render,
            position + Vec3(left_segment_x, front_y, wall_base_z + wall_height / 2),
            Vec3(left_segment_width, wall_thickness, wall_height),
            wall_mass * 0.4,
            light_wood_color,
            f"{name}_wall_front_left",
            "wall",
        )
        self.add_piece(front_wall_left)

        # Right segment of front wall
        right_segment_width = left_segment_width
        right_segment_x = (width + 2 * corner_overlap) / 2 - right_segment_width / 2

        front_wall_right = BuildingPiece(
            world,
            render,
            position + Vec3(right_segment_x, front_y, wall_base_z + wall_height / 2),
            Vec3(right_segment_width, wall_thickness, wall_height),
            wall_mass * 0.4,
            light_wood_color,
            f"{name}_wall_front_right",
            "wall",
        )
        self.add_piece(front_wall_right)

        # Top segment above the door (lintel) - smaller since door is lower
        lintel_height = wall_height - door_height
        lintel_z = wall_base_z + wall_height / 2 + door_height / 2

        front_wall_top = BuildingPiece(
            world,
            render,
            position + Vec3(0, front_y, lintel_z),
            Vec3(door_width, wall_thickness, lintel_height),
            wall_mass * 0.2,
            light_wood_color,
            f"{name}_wall_front_top",
            "wall",
        )
        self.add_piece(front_wall_top)

        # Back wall - solid with shoji window openings
        back_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, depth / 2, wall_base_z + wall_height / 2),
            Vec3(width + (2 * corner_overlap), wall_thickness, wall_height),
            wall_mass,
            light_wood_color,
            f"{name}_wall_back",
            "wall",
        )
        self.add_piece(back_wall)

        # Left wall - can have sliding panels
        left_wall = BuildingPiece(
            world,
            render,
            position + Vec3(-width / 2, 0, wall_base_z + wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            light_wood_color,
            f"{name}_wall_left",
            "wall",
        )
        self.add_piece(left_wall)

        # Right wall
        right_wall = BuildingPiece(
            world,
            render,
            position + Vec3(width / 2, 0, wall_base_z + wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            light_wood_color,
            f"{name}_wall_right",
            "wall",
        )
        self.add_piece(right_wall)

        # Create multi-tiered curved roof (characteristic of Japanese architecture)
        roof_base_z = wall_base_z + wall_height + 0.3

        # Main curved roof - extends well beyond walls (deep eaves)
        eave_overhang = 2.0  # Deep eaves characteristic of Japanese roofs
        main_roof = CurvedRoofPiece(
            world,
            render,
            position + Vec3(0, 0, roof_base_z + 0.2),
            Vec3(width + eave_overhang, depth + eave_overhang, 0.5),
            wall_mass * 1.5,
            roof_color,
            f"{name}_roof_main",
            parent_building=self,
            curve_amount=0.8,  # Strong upward curve
            tier=1,
        )
        self.add_piece(main_roof)

        # Middle roof tier (second layer)
        middle_roof = CurvedRoofPiece(
            world,
            render,
            position + Vec3(0, 0, roof_base_z + 1.2),
            Vec3(width * 0.75, depth * 0.75, 0.4),
            wall_mass * 0.8,
            roof_color,
            f"{name}_roof_middle",
            parent_building=self,
            curve_amount=0.9,  # Even more curve
            tier=2,
        )
        self.add_piece(middle_roof)

        # Upper roof tier (top layer - gives traditional three-tiered pagoda look)
        upper_roof = CurvedRoofPiece(
            world,
            render,
            position + Vec3(0, 0, roof_base_z + 2.2),
            Vec3(width * 0.5, depth * 0.5, 0.3),
            wall_mass * 0.5,
            roof_color,
            f"{name}_roof_upper",
            parent_building=self,
            curve_amount=1.0,  # Maximum curve for top tier
            tier=3,
        )
        self.add_piece(upper_roof)

        # Create roof support posts (decorative structural elements)
        post_width = 0.3
        post_height = platform_height + wall_height
        post_positions = [
            Vec3(-width / 2 + 1, -depth / 2 + 1, 0.3 + post_height / 2),  # Front left
            Vec3(width / 2 - 1, -depth / 2 + 1, 0.3 + post_height / 2),   # Front right
            Vec3(-width / 2 + 1, depth / 2 - 1, 0.3 + post_height / 2),   # Back left
            Vec3(width / 2 - 1, depth / 2 - 1, 0.3 + post_height / 2),    # Back right
        ]

        for i, pos in enumerate(post_positions):
            post = BuildingPiece(
                world,
                render,
                position + pos,
                Vec3(post_width, post_width, post_height),
                wall_mass * 0.3,
                wood_color,
                f"{name}_post_{i}",
                "wall",
            )
            self.add_piece(post)

        # Connect everything
        # Connect walls to platform (raised floor)
        self.connect_pieces(f"{name}_wall_front_left", f"{name}_platform", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_front_right", f"{name}_platform", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_front_top", f"{name}_platform", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_back", f"{name}_platform", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_left", f"{name}_platform", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_right", f"{name}_platform", breaking_threshold=100)

        # Connect platform to foundation
        self.connect_pieces(f"{name}_platform", f"{name}_foundation", breaking_threshold=150)

        # Connect front wall segments to each other
        self.connect_pieces(f"{name}_wall_front_left", f"{name}_wall_front_top", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_front_right", f"{name}_wall_front_top", breaking_threshold=80)

        # Connect walls to each other at corners
        self.connect_pieces(f"{name}_wall_front_left", f"{name}_wall_left", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_front_right", f"{name}_wall_right", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_back", f"{name}_wall_left", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_back", f"{name}_wall_right", breaking_threshold=80)

        # Connect posts to platform and walls
        for i in range(4):
            self.connect_pieces(f"{name}_post_{i}", f"{name}_platform", breaking_threshold=100)

        # Connect main roof to walls and posts
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_front_left", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_front_right", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_front_top", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_back", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_left", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof_main", f"{name}_wall_right", breaking_threshold=60)

        # Connect roof tiers (three-tiered structure)
        self.connect_pieces(f"{name}_roof_middle", f"{name}_roof_main", breaking_threshold=50)
        self.connect_pieces(f"{name}_roof_upper", f"{name}_roof_middle", breaking_threshold=50)

        # Connect posts to main roof
        for i in range(4):
            self.connect_pieces(f"{name}_post_{i}", f"{name}_roof_main", breaking_threshold=80)

        # Add shoji-style window openings (paper screen style)
        shoji_color = Vec4(0.95, 0.95, 0.85, 0.6)  # Off-white, semi-transparent
        window_width = 2.5
        window_height = 2.0
        window_z = wall_height / 3  # Lower than Western windows

        # Front wall segments - shoji windows with grid pattern effect
        front_wall_left.add_opening("window", Vec3(0, 0, window_z),
                                    Vec3(window_width, wall_thickness, window_height),
                                    color=shoji_color)
        front_wall_right.add_opening("window", Vec3(0, 0, window_z),
                                     Vec3(window_width, wall_thickness, window_height),
                                     color=shoji_color)

        # Back wall - multiple shoji windows
        num_back_windows = 3
        window_spacing = width / (num_back_windows + 1)
        for i in range(num_back_windows):
            x_pos = -width / 2 + window_spacing * (i + 1)
            back_wall.add_opening("window", Vec3(x_pos, 0, window_z),
                                 Vec3(window_width * 0.8, wall_thickness, window_height),
                                 color=shoji_color)

        # Side walls - shoji windows
        if depth > 8:
            left_wall.add_opening("window", Vec3(0, -depth / 4, window_z),
                                 Vec3(wall_thickness, window_width * 0.8, window_height),
                                 color=shoji_color)
            left_wall.add_opening("window", Vec3(0, depth / 4, window_z),
                                 Vec3(wall_thickness, window_width * 0.8, window_height),
                                 color=shoji_color)
            right_wall.add_opening("window", Vec3(0, -depth / 4, window_z),
                                  Vec3(wall_thickness, window_width * 0.8, window_height),
                                  color=shoji_color)
            right_wall.add_opening("window", Vec3(0, depth / 4, window_z),
                                  Vec3(wall_thickness, window_width * 0.8, window_height),
                                  color=shoji_color)
        else:
            left_wall.add_opening("window", Vec3(0, 0, window_z),
                                 Vec3(wall_thickness, window_width, window_height),
                                 color=shoji_color)
            right_wall.add_opening("window", Vec3(0, 0, window_z),
                                  Vec3(wall_thickness, window_width, window_height),
                                  color=shoji_color)

        print(f"Created traditional Japanese-style {name} with {len(self.pieces)} pieces")
        print(f"  - Raised platform at {platform_height}m")
        print(f"  - Wide sliding entrance: {door_width}m × {door_height}m")
        print(f"  - Three-tiered curved roof with deep eaves ({eave_overhang}m overhang)")
