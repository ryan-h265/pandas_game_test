"""Shadow system configuration settings."""

# Shadow Map Settings
SHADOW_MAP_SIZE = 1024  # Resolution per cascade (1024, 2048, 4096)
NUM_CASCADES = 3  # Number of shadow cascades (2-4)
CASCADE_SPLITS = [20.0, 60.0, 160.0, 320.0]  # View space split distances
SHADOW_SOFTNESS = 2.5  # PCF kernel size multiplier (0.5-10.0)

# Advanced cascade tuning
CASCADE_BLEND_DISTANCE = 18.0  # Blend width between cascades (world units)
CASCADE_BIAS = (0.0008, 0.0012, 0.0018, 0.0024)  # Per-cascade depth bias
MAX_SHADOW_DISTANCE = 320.0  # Clamp cascades to this distance from camera

# Sun animation
SUN_ANIMATION_ENABLED = True  # Animate sun across the sky
SUN_ANIMATION_SPEED = 0.0125  # Revolutions per second (lower = slower day)
SUN_START_OFFSET = 0.25  # Start position on the unit circle (0-1)
SUN_MIN_ELEVATION = 0.08  # Minimum sun elevation (radians fraction of pi)
SUN_MAX_ELEVATION = 0.78  # Maximum sun elevation (radians fraction of pi)

# Light Settings
LIGHT_DIRECTION = (1.0, 1.0, -1.0)  # Sun direction (X, Y, Z)
LIGHT_COLOR = (0.8, 0.8, 0.7)  # Sun color (R, G, B)
AMBIENT_COLOR = (0.3, 0.3, 0.3)  # Ambient light color

# SSAO Settings
SSAO_ENABLED = True  # Enable/disable SSAO
SSAO_RADIUS = 1.5  # Occlusion sample radius (0.5-5.0)
SSAO_BIAS = 0.025  # Depth bias (0.001-0.1)
SSAO_KERNEL_SIZE = 16  # Number of samples (16, 32, 64)

# Denoising Settings
DENOISE_ENABLED = True  # Enable/disable denoising
DENOISE_SPATIAL_SIGMA = 2.0  # Spatial blur strength (1.0-5.0)
DENOISE_DEPTH_SIGMA = 0.1  # Depth edge preservation (0.05-0.5)
DENOISE_KERNEL_SIZE = 5  # Filter kernel size (3, 5, 7)

# Performance Presets
PRESETS = {
    "low": {
        "shadow_map_size": 1024,
        "num_cascades": 2,
        "cascade_splits": [16.0, 48.0, 120.0, 240.0],
        "max_shadow_distance": 240.0,
        "shadow_softness": 1.5,
        "ssao_enabled": False,
        "denoise_enabled": True,
        "sun_animation_speed": 0.008,
    },
    "medium": {
        "shadow_map_size": 2048,
        "num_cascades": 3,
        "cascade_splits": [20.0, 60.0, 160.0, 320.0],
        "max_shadow_distance": 320.0,
        "shadow_softness": 2.5,
        "ssao_enabled": True,
        "denoise_enabled": True,
        "sun_animation_speed": 0.0125,
    },
    "high": {
        "shadow_map_size": 4096,
        "num_cascades": 3,
        "cascade_splits": [24.0, 80.0, 220.0, 420.0],
        "max_shadow_distance": 420.0,
        "shadow_softness": 3.0,
        "ssao_enabled": True,
        "denoise_enabled": True,
        "sun_animation_speed": 0.015,
    },
    "ultra": {
        "shadow_map_size": 4096,
        "num_cascades": 4,
        "cascade_splits": [28.0, 96.0, 280.0, 560.0],
        "max_shadow_distance": 560.0,
        "shadow_softness": 3.5,
        "ssao_enabled": True,
        "denoise_enabled": True,
        "sun_animation_speed": 0.02,
    },
}

# Current preset
QUALITY_PRESET = "medium"  # 'low', 'medium', 'high', 'ultra'


def get_preset_settings(preset_name="medium"):
    """Get shadow settings for a quality preset.

    Args:
        preset_name: Name of the preset ('low', 'medium', 'high', 'ultra')

    Returns:
        Dictionary of settings
    """
    return PRESETS.get(preset_name, PRESETS["medium"])


def apply_preset(shadow_manager, post_process, preset_name=QUALITY_PRESET):
    """Apply a quality preset to the shadow system.

    Args:
        shadow_manager: ShadowManager instance
        post_process: PostProcessManager instance
        preset_name: Name of the preset to apply
    """
    settings = get_preset_settings(preset_name)

    # Apply shadow settings
    if hasattr(shadow_manager, "apply_quality_settings"):
        shadow_manager.apply_quality_settings(
            shadow_map_size=settings["shadow_map_size"],
            num_cascades=settings["num_cascades"],
            cascade_splits=settings.get("cascade_splits"),
            max_shadow_distance=settings.get("max_shadow_distance"),
            shadow_softness=settings["shadow_softness"],
            sun_animation_speed=settings.get("sun_animation_speed"),
        )
    else:
        shadow_manager.shadow_map_size = settings["shadow_map_size"]
        shadow_manager.num_cascades = settings["num_cascades"]
        shadow_manager.shadow_softness = settings["shadow_softness"]

    # Apply post-process settings
    if hasattr(post_process, "enabled"):
        post_process.enabled = settings["ssao_enabled"] and settings["denoise_enabled"]

    print(f"Applied '{preset_name}' quality preset")
