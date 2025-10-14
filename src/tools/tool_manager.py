"""Tool system for player interactions with the world."""

from enum import Enum


class ToolType(Enum):
    """Types of tools available to the player."""

    FIST = "fist"
    TERRAIN = "terrain"
    CROWBAR = "crowbar"
    GUN = "gun"


class Tool:
    """Base class for player tools."""

    def __init__(self, name, tool_type):
        """Initialize tool.

        Args:
            name: Display name of the tool
            tool_type: ToolType enum value
        """
        self.name = name
        self.tool_type = tool_type
        self.is_active = False

    def on_activate(self):
        """Called when tool becomes active."""
        self.is_active = True
        # Return message for HUD display
        return f"Equipped: {self.name}"

    def on_deactivate(self):
        """Called when tool is switched away from."""
        self.is_active = False

    def on_primary_use(self, hit_info):
        """Called when primary action is used (e.g., left click).

        Args:
            hit_info: Dictionary with hit information (position, normal, etc.)

        Returns:
            bool: True if action was performed
        """
        return False

    def on_secondary_use(self, hit_info):
        """Called when secondary action is used (e.g., right click).

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        return False

    def on_tertiary_use(self, hit_info):
        """Called when tertiary action is used (e.g., middle click).

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        return False

    def update(self, dt):
        """Update tool state.

        Args:
            dt: Delta time since last update
        """
        pass


class FistTool(Tool):
    """Default tool - bare hands for basic interaction."""

    def __init__(self, world, camera, building_raycaster=None):
        """Initialize fist tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Fist", ToolType.FIST)
        self.world = world
        self.camera = camera
        self.building_raycaster = building_raycaster
        self.damage_per_hit = 25  # Low damage with fists
        self.max_range = 5.0  # Very short melee range

    def on_activate(self):
        """Called when fist is equipped."""
        return "Equipped: Fist (basic interaction)"

    def on_primary_use(self, hit_info):
        """Punch buildings (weak damage).

        Args:
            hit_info: Dictionary with hit information (from terrain raycast, not used)

        Returns:
            bool: True if something was hit
        """
        # Use building raycaster for physics-based hit detection
        if self.building_raycaster:
            physics_hit = self.building_raycaster.raycast_from_camera(self.camera, self.max_range)

            if physics_hit["hit"]:
                hit_pos = physics_hit["position"]
                
                # Try to damage a building at the hit position
                damaged = self.world.damage_building_at_position(hit_pos, damage=self.damage_per_hit)

                if damaged:
                    print(f"Fist HIT building at distance {physics_hit['distance']:.2f}")
                    return True
        
        # Fallback to terrain raycast if building raycaster not available
        elif hit_info and hit_info.get("position"):
            damaged = self.world.damage_building_at_position(
                hit_info["position"], damage=self.damage_per_hit
            )

            if damaged:
                return True

        return False


class TerrainTool(Tool):
    """Tool for terrain editing (dig, raise, smooth)."""

    def __init__(self, terrain_editor):
        """Initialize terrain tool.

        Args:
            terrain_editor: TerrainEditor instance
        """
        super().__init__("Terrain Editor", ToolType.TERRAIN)
        self.terrain_editor = terrain_editor
        self.edit_mode = "lower"

    def on_activate(self):
        """Called when terrain tool is equipped."""
        return "Equipped: Terrain Editor (dig/build/smooth)"

    def on_primary_use(self, hit_info):
        """Dig/lower terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("lower")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def on_secondary_use(self, hit_info):
        """Raise terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("raise")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def on_tertiary_use(self, hit_info):
        """Smooth terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("smooth")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def set_mode(self, mode):
        """Set terrain editing mode.

        Args:
            mode: 'lower', 'raise', or 'smooth'
        """
        self.edit_mode = mode
        self.terrain_editor.set_edit_mode(mode)
        # Return nothing - parent will handle via tool_manager


class CrowbarTool(Tool):
    """Tool for breaking building pieces (melee weapon)."""

    def __init__(self, world, camera, building_raycaster=None):
        """Initialize crowbar tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Crowbar", ToolType.CROWBAR)
        self.world = world
        self.camera = camera
        self.building_raycaster = building_raycaster
        self.damage_per_hit = 75  # High damage for crowbar
        self.swing_cooldown = 0.5  # Seconds between swings
        self.last_swing_time = 0.0
        self.current_time = 0.0
        self.max_range = 10.0  # Melee range (shorter than gun)

    def on_activate(self):
        """Called when crowbar is equipped."""
        return "Equipped: Crowbar (high damage to walls)"

    def on_primary_use(self, hit_info):
        """Swing crowbar to damage buildings.

        Args:
            hit_info: Dictionary with hit information (from terrain raycast, not used)

        Returns:
            bool: True if something was hit
        """
        # Check cooldown
        if self.current_time - self.last_swing_time < self.swing_cooldown:
            return False

        # Use building raycaster for physics-based hit detection
        hit_something = False
        if self.building_raycaster:
            physics_hit = self.building_raycaster.raycast_from_camera(self.camera, self.max_range)

            if physics_hit["hit"]:
                hit_pos = physics_hit["position"]
                hit_something = True
                
                # Try to damage building at hit position
                damaged = self.world.damage_building_at_position(hit_pos, damage=self.damage_per_hit)
                
                if damaged:
                    self.last_swing_time = self.current_time
                    print(f"Crowbar HIT building at distance {physics_hit['distance']:.2f}")
                    return True
        
        # Fallback to terrain raycast if building raycaster not available
        elif hit_info and hit_info.get("position"):
            damaged = self.world.damage_building_at_position(
                hit_info["position"], damage=self.damage_per_hit
            )

            if damaged:
                self.last_swing_time = self.current_time
                return True

        return False

    def on_secondary_use(self, hit_info):
        """Secondary action (could be used for prying)."""
        # For now, same as primary
        return self.on_primary_use(hit_info)

    def update(self, dt):
        """Update crowbar state.

        Args:
            dt: Delta time
        """
        self.current_time += dt


class GunTool(Tool):
    """Ranged weapon for shooting buildings from distance."""

    def __init__(self, world, camera, effects_manager=None, building_raycaster=None):
        """Initialize gun tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            effects_manager: EffectsManager for visual effects
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Gun", ToolType.GUN)
        self.world = world
        self.camera = camera
        self.effects_manager = effects_manager
        self.building_raycaster = building_raycaster
        self.damage_per_shot = 100  # One-shot walls
        self.fire_rate = 0.3  # Seconds between shots
        self.last_shot_time = 0.0
        self.current_time = 0.0
        self.max_range = 100.0
        self.bullets_fired = 0

    def on_activate(self):
        """Called when gun is equipped."""
        return "Equipped: Gun (ranged damage)"

    def on_primary_use(self, hit_info):
        """Fire gun at target.

        Args:
            hit_info: Dictionary with hit information (from terrain raycast)

        Returns:
            bool: True if shot was fired
        """
        # Check cooldown
        if self.current_time - self.last_shot_time < self.fire_rate:
            return False

        # Get camera position in world space
        camera_pos = self.camera.getPos(self.world.render)

        # Get forward direction from camera's transformation matrix
        # This properly accounts for both heading (yaw) and pitch
        cam_mat = self.camera.getMat(self.world.render)
        forward = cam_mat.getRow3(1)  # Y-axis (forward) from transformation matrix
        forward.normalize()

        # Debug: Get camera rotation
        hpr = self.camera.getHpr(self.world.render)
        print(f"\n=== GUN SHOT DEBUG ===")
        print(f"Camera pos: {camera_pos}")
        print(f"Camera HPR: {hpr}")
        print(f"Forward vector: {forward}")

        # Use building raycaster if available (physics-based)
        hit_something = False
        if self.building_raycaster:
            physics_hit = self.building_raycaster.raycast_from_camera(self.camera, self.max_range)

            if physics_hit["hit"]:
                end_pos = physics_hit["position"]
                hit_something = True
                print(f"Gun HIT physics object at {end_pos}, distance={physics_hit['distance']:.2f}")

                # Try to damage building at hit position
                damaged = self.world.damage_building_at_position(end_pos, damage=self.damage_per_shot)
                print(f"  Damage result: {damaged}")
            else:
                # No physics hit - shoot into distance
                end_pos = camera_pos + forward * self.max_range
                print(f"Gun MISS - no physics hit")
        else:
            # Fallback to terrain raycast
            if hit_info and hit_info.get("position"):
                end_pos = hit_info["position"]
                hit_something = True
                damaged = self.world.damage_building_at_position(end_pos, damage=self.damage_per_shot)
            else:
                end_pos = camera_pos + forward * self.max_range

        # Create visual effects
        if self.effects_manager:
            # Start bullet trail offset from camera (gun barrel position)
            muzzle_pos = camera_pos + forward * 3.0  # 3 units forward from camera (increased from 2.0)
            distance = (end_pos - muzzle_pos).length()
            print(f"Muzzle pos: {muzzle_pos} (camera + forward*2.0)")
            print(f"End pos: {end_pos}")
            print(f"Trail distance: {distance:.2f}")
            print(f"===================\n")
            self.effects_manager.create_bullet_trail(muzzle_pos, end_pos)
            self.effects_manager.create_muzzle_flash(muzzle_pos, forward)

            # Create debug ray visualization (shows exact raycast)
            self.effects_manager.create_debug_ray(camera_pos, end_pos, hit_something)

        self.last_shot_time = self.current_time
        self.bullets_fired += 1
        return True

    def update(self, dt):
        """Update gun state.

        Args:
            dt: Delta time
        """
        self.current_time += dt


class ToolManager:
    """Manages player tools and tool switching."""

    def __init__(self, terrain_editor, world, camera=None, effects_manager=None, building_raycaster=None):
        """Initialize tool manager.

        Args:
            terrain_editor: TerrainEditor instance
            world: Game world instance
            camera: Camera node for gun aiming (optional)
            effects_manager: EffectsManager for visual effects (optional)
            building_raycaster: BuildingRaycaster for physics raycasting (optional)
        """
        self.tools = {}
        self.active_tool = None
        self.tool_message_callback = None  # Optional callback for UI messages

        # Create tools (all melee weapons now use camera + building_raycaster for accurate hit detection)
        self.tools[ToolType.FIST] = FistTool(world, camera, building_raycaster)
        self.tools[ToolType.TERRAIN] = TerrainTool(terrain_editor)
        self.tools[ToolType.CROWBAR] = CrowbarTool(world, camera, building_raycaster)
        if camera:
            self.tools[ToolType.GUN] = GunTool(world, camera, effects_manager, building_raycaster)

        # Start with fist (default)
        self.set_active_tool(ToolType.FIST)

    def set_active_tool(self, tool_type):
        """Switch to a different tool.

        Args:
            tool_type: ToolType enum value
        """
        if tool_type not in self.tools:
            return

        # Deactivate current tool
        if self.active_tool:
            self.active_tool.on_deactivate()

        # Activate new tool
        self.active_tool = self.tools[tool_type]
        message = self.active_tool.on_activate()

        # Send message to callback if set
        if self.tool_message_callback and message:
            self.tool_message_callback(message)
        else:
            print(message)

    def get_active_tool(self):
        """Get currently active tool.

        Returns:
            Tool instance or None
        """
        return self.active_tool

    def use_primary(self, hit_info):
        """Use active tool's primary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            return self.active_tool.on_primary_use(hit_info)
        return False

    def use_secondary(self, hit_info):
        """Use active tool's secondary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            return self.active_tool.on_secondary_use(hit_info)
        return False

    def use_tertiary(self, hit_info):
        """Use active tool's tertiary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            return self.active_tool.on_tertiary_use(hit_info)
        return False

    def update(self, dt):
        """Update active tool.

        Args:
            dt: Delta time
        """
        if self.active_tool:
            self.active_tool.update(dt)

    def cycle_tool(self):
        """Cycle to next tool."""
        tool_types = list(self.tools.keys())
        if not self.active_tool:
            self.set_active_tool(tool_types[0])
            return

        current_type = self.active_tool.tool_type
        current_index = tool_types.index(current_type)
        next_index = (current_index + 1) % len(tool_types)
        self.set_active_tool(tool_types[next_index])
