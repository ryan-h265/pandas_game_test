"""Simple building implementation with walls and a roof."""

from panda3d.core import Vec3, Vec4

from .building import Building, BuildingPiece


class SimpleBuilding(Building):
    """A simple building with walls and a roof."""

    def __init__(
        self,
        world,
        render,
        position,
        width=10,
        depth=10,
        height=8,
        name="simple_building",
    ):
        """Create a simple building.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 base position
            width: Building width (X axis)
            depth: Building depth (Y axis)
            height: Building height (Z axis)
            name: Building identifier
        """
        super().__init__(world, render, position, name)

        # Colors
        wall_color = Vec4(0.8, 0.7, 0.6, 1.0)  # Tan/beige
        roof_color = Vec4(0.5, 0.3, 0.2, 1.0)  # Brown
        foundation_color = Vec4(0.6, 0.6, 0.6, 1.0)  # Gray

        wall_thickness = 0.5
        wall_height = height
        wall_mass = 20.0  # Reasonable mass for when pieces become dynamic

        # Corner overlap amount - walls will extend this much into corners
        # to create seamless joints
        corner_overlap = wall_thickness

        # Create foundation (static)
        foundation = BuildingPiece(
            world,
            render,
            position,
            Vec3(width, depth, 1.0),
            0,  # Mass 0 = static
            foundation_color,
            f"{name}_foundation",
            "foundation",
        )
        self.add_piece(foundation)

        # Door dimensions
        door_width = 2.5
        door_height = 4.0

        # Create four walls with extended lengths to overlap at corners
        # Front and back walls extend the full width plus corner overlaps
        # Left and right walls fit between them with no extension

        # Front wall (negative Y) - split into segments around the doorway
        # Calculate positions for wall segments on either side of door
        front_y = -depth / 2

        # Left segment of front wall (from left corner to left side of door)
        left_segment_width = (width + 2 * corner_overlap - door_width) / 2
        left_segment_x = -(width + 2 * corner_overlap) / 2 + left_segment_width / 2

        front_wall_left = BuildingPiece(
            world,
            render,
            position + Vec3(left_segment_x, front_y, wall_height / 2),
            Vec3(left_segment_width, wall_thickness, wall_height),
            wall_mass * 0.4,  # Proportional mass
            wall_color,
            f"{name}_wall_front_left",
            "wall",
        )
        self.add_piece(front_wall_left)

        # Right segment of front wall (from right side of door to right corner)
        right_segment_width = left_segment_width  # Symmetric
        right_segment_x = (width + 2 * corner_overlap) / 2 - right_segment_width / 2

        front_wall_right = BuildingPiece(
            world,
            render,
            position + Vec3(right_segment_x, front_y, wall_height / 2),
            Vec3(right_segment_width, wall_thickness, wall_height),
            wall_mass * 0.4,  # Proportional mass
            wall_color,
            f"{name}_wall_front_right",
            "wall",
        )
        self.add_piece(front_wall_right)

        # Top segment above the door (lintel)
        lintel_height = wall_height - door_height
        lintel_z = wall_height / 2 + door_height / 2

        front_wall_top = BuildingPiece(
            world,
            render,
            position + Vec3(0, front_y, lintel_z),
            Vec3(door_width, wall_thickness, lintel_height),
            wall_mass * 0.2,  # Proportional mass
            wall_color,
            f"{name}_wall_front_top",
            "wall",
        )
        self.add_piece(front_wall_top)

        # Back wall (positive Y) - extends full width + overlaps on both sides
        back_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, depth / 2, wall_height / 2),
            Vec3(width + (2 * corner_overlap), wall_thickness, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_back",
            "wall",
        )
        self.add_piece(back_wall)

        # Left wall (negative X) - fits between front and back (no extension needed)
        left_wall = BuildingPiece(
            world,
            render,
            position + Vec3(-width / 2, 0, wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_left",
            "wall",
        )
        self.add_piece(left_wall)

        # Right wall (positive X) - fits between front and back (no extension needed)
        right_wall = BuildingPiece(
            world,
            render,
            position + Vec3(width / 2, 0, wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_right",
            "wall",
        )
        self.add_piece(right_wall)

        # Create roof
        roof = BuildingPiece(
            world,
            render,
            position + Vec3(0, 0, wall_height + 0.5),
            Vec3(width + 1, depth + 1, 0.5),  # Slightly larger than walls
            wall_mass * 1.5,  # Heavier roof
            roof_color,
            f"{name}_roof",
            "roof",
        )
        self.add_piece(roof)

        # Connect everything - since pieces are kinematic, constraints just track connections
        # They don't need high breaking thresholds since there's no physics forces on them

        # Connect walls to foundation
        self.connect_pieces(
            f"{name}_wall_front_left", f"{name}_foundation", breaking_threshold=100
        )
        self.connect_pieces(
            f"{name}_wall_front_right", f"{name}_foundation", breaking_threshold=100
        )
        self.connect_pieces(
            f"{name}_wall_front_top", f"{name}_foundation", breaking_threshold=100
        )
        self.connect_pieces(
            f"{name}_wall_back", f"{name}_foundation", breaking_threshold=100
        )
        self.connect_pieces(
            f"{name}_wall_left", f"{name}_foundation", breaking_threshold=100
        )
        self.connect_pieces(
            f"{name}_wall_right", f"{name}_foundation", breaking_threshold=100
        )

        # Connect front wall segments to each other
        self.connect_pieces(
            f"{name}_wall_front_left", f"{name}_wall_front_top", breaking_threshold=80
        )
        self.connect_pieces(
            f"{name}_wall_front_right", f"{name}_wall_front_top", breaking_threshold=80
        )

        # Connect walls to each other at corners
        self.connect_pieces(
            f"{name}_wall_front_left", f"{name}_wall_left", breaking_threshold=80
        )
        self.connect_pieces(
            f"{name}_wall_front_right", f"{name}_wall_right", breaking_threshold=80
        )
        self.connect_pieces(
            f"{name}_wall_back", f"{name}_wall_left", breaking_threshold=80
        )
        self.connect_pieces(
            f"{name}_wall_back", f"{name}_wall_right", breaking_threshold=80
        )

        # Connect roof to walls
        self.connect_pieces(
            f"{name}_roof", f"{name}_wall_front_left", breaking_threshold=60
        )
        self.connect_pieces(
            f"{name}_roof", f"{name}_wall_front_right", breaking_threshold=60
        )
        self.connect_pieces(
            f"{name}_roof", f"{name}_wall_front_top", breaking_threshold=60
        )
        self.connect_pieces(f"{name}_roof", f"{name}_wall_back", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof", f"{name}_wall_left", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof", f"{name}_wall_right", breaking_threshold=60)

        # Add windows to walls
        window_width = 2.0
        window_height = 1.5
        window_z = wall_height / 4  # Quarter way up the wall

        # Front wall segments - add windows to left and right segments
        # Windows should be in local coordinates relative to each segment
        front_wall_left.add_opening(
            "window",
            Vec3(0, 0, window_z),
            Vec3(window_width, wall_thickness, window_height),
        )
        front_wall_right.add_opening(
            "window",
            Vec3(0, 0, window_z),
            Vec3(window_width, wall_thickness, window_height),
        )

        # Back wall - two windows
        back_wall.add_opening(
            "window",
            Vec3(-width / 3, 0, window_z),
            Vec3(window_width, wall_thickness, window_height),
        )
        back_wall.add_opening(
            "window",
            Vec3(width / 3, 0, window_z),
            Vec3(window_width, wall_thickness, window_height),
        )

        # Left wall - one or two windows depending on depth
        if depth > 8:
            left_wall.add_opening(
                "window",
                Vec3(0, -depth / 4, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )
            left_wall.add_opening(
                "window",
                Vec3(0, depth / 4, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )
        else:
            left_wall.add_opening(
                "window",
                Vec3(0, 0, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )

        # Right wall - one or two windows depending on depth
        if depth > 8:
            right_wall.add_opening(
                "window",
                Vec3(0, -depth / 4, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )
            right_wall.add_opening(
                "window",
                Vec3(0, depth / 4, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )
        else:
            right_wall.add_opening(
                "window",
                Vec3(0, 0, window_z),
                Vec3(wall_thickness, window_width, window_height),
            )

        print(
            f"Created {name} with {len(self.pieces)} pieces and structural connections"
        )
