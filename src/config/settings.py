from panda3d.core import loadPrcFileData


def configure():
    # Window settings
    loadPrcFileData("", "window-title Terrain Builder Game")
    loadPrcFileData("", "win-size 1920 1080")
    loadPrcFileData("", "fullscreen false")
    loadPrcFileData("", "framebuffer-multisample 1")
    loadPrcFileData("", "multisamples 4")

    # Performance
    loadPrcFileData("", "sync-video true")
    loadPrcFileData("", "show-frame-rate-meter true")
    loadPrcFileData("", "texture-minfilter linear-mipmap-linear")

    # Model loading
    loadPrcFileData("", "model-path $MAIN_DIR/assets/models")
    loadPrcFileData("", "model-path $MAIN_DIR/assets")

    # Audio
    loadPrcFileData("", "audio-library-name p3openal_audio")


# Game constants
CHUNK_SIZE = 32
RENDER_DISTANCE = 8
PHYSICS_FPS = 60
GRAVITY = -9.81

# World generation
FLAT_WORLD = True  # Set to True for a completely flat world at height 0
