from panda3d.core import loadPrcFileData


def configure():
    # Window settings
    loadPrcFileData("", "window-title Mountain Game")
    loadPrcFileData("", "win-size 1920 1080")
    loadPrcFileData("", "fullscreen false")
    loadPrcFileData("", "framebuffer-multisample 1")
    loadPrcFileData("", "multisamples 4")

    # Graphics API - Force OpenGL (hardware accelerated)
    loadPrcFileData("", "load-display pandagl")
    loadPrcFileData("", "aux-display pandagl")

    # Performance
    loadPrcFileData("", "sync-video true")
    loadPrcFileData("", "show-frame-rate-meter true")
    loadPrcFileData("", "texture-minfilter linear-mipmap-linear")

    # Enable hardware acceleration features
    loadPrcFileData("", "hardware-animated-vertices true")
    loadPrcFileData("", "basic-shaders-only false")

    # Model loading
    loadPrcFileData("", "model-path $MAIN_DIR/assets/models")
    loadPrcFileData("", "model-path $MAIN_DIR/assets")

    # Audio
    loadPrcFileData("", "audio-library-name p3openal_audio")


# Game constants
CHUNK_SIZE = 32
RENDER_DISTANCE = 25
PHYSICS_FPS = 60
GRAVITY = -9.81

# World generation
FLAT_WORLD = False  # Set to True for a completely flat world at height 0
MODIFIABLE_TERRAIN = True  # Set to False to disable terrain editing
# When False + FLAT_WORLD=True: uses minimal geometry (2 triangles/chunk)
# for maximum performance instead of TERRAIN_RESOLUTION vertices

# Terrain resolution (vertices per chunk edge)
# Higher = more detail but worse performance
# Examples:
#   TERRAIN_RESOLUTION = 32  # Default: 32x32 = 2,048 triangles per chunk
#   TERRAIN_RESOLUTION = 16  # Lower:   16x16 = 512 triangles per chunk (4x fewer)
#   TERRAIN_RESOLUTION = 8   # Lowest:  8x8   = 128 triangles per chunk (16x fewer)
TERRAIN_RESOLUTION = 32  # Reduced from 32 for better performance

# Debug visualization
DEBUG_CHUNK_COLORS = False  # Show each chunk with a different color
DEBUG_CHUNK_WIREFRAME = False  # Show wireframe overlay on chunks

# God mode settings
GODMODE_ENABLED = True  # Enable god mode features (flying, etc.)
GODMODE_FLY_SPEED = 30.0  # Speed when flying in god mode
