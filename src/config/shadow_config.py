"""Shadow system configuration settings."""

# Shadow Map Settings
SHADOW_MAP_SIZE = 2048  # Resolution per cascade (1024, 2048, 4096)
NUM_CASCADES = 3        # Number of shadow cascades (2-4)
CASCADE_SPLITS = [20.0, 50.0, 150.0]  # View space split distances
SHADOW_SOFTNESS = 2.0   # PCF kernel size multiplier (0.5-10.0)

# Light Settings
LIGHT_DIRECTION = (1.0, 1.0, -1.0)  # Sun direction (X, Y, Z)
LIGHT_COLOR = (0.8, 0.8, 0.7)       # Sun color (R, G, B)
AMBIENT_COLOR = (0.3, 0.3, 0.3)     # Ambient light color

# SSAO Settings
SSAO_ENABLED = True      # Enable/disable SSAO
SSAO_RADIUS = 1.5        # Occlusion sample radius (0.5-5.0)
SSAO_BIAS = 0.025        # Depth bias (0.001-0.1)
SSAO_KERNEL_SIZE = 32    # Number of samples (16, 32, 64)

# Denoising Settings
DENOISE_ENABLED = True           # Enable/disable denoising
DENOISE_SPATIAL_SIGMA = 2.0      # Spatial blur strength (1.0-5.0)
DENOISE_DEPTH_SIGMA = 0.1        # Depth edge preservation (0.05-0.5)
DENOISE_KERNEL_SIZE = 5          # Filter kernel size (3, 5, 7)

# Performance Presets
PRESETS = {
    'low': {
        'shadow_map_size': 1024,
        'num_cascades': 2,
        'shadow_softness': 1.0,
        'ssao_enabled': False,
        'denoise_enabled': True,
    },
    'medium': {
        'shadow_map_size': 2048,
        'num_cascades': 3,
        'shadow_softness': 2.0,
        'ssao_enabled': True,
        'denoise_enabled': True,
    },
    'high': {
        'shadow_map_size': 4096,
        'num_cascades': 3,
        'shadow_softness': 3.0,
        'ssao_enabled': True,
        'denoise_enabled': True,
    },
    'ultra': {
        'shadow_map_size': 4096,
        'num_cascades': 4,
        'shadow_softness': 4.0,
        'ssao_enabled': True,
        'denoise_enabled': True,
    }
}

# Current preset
QUALITY_PRESET = 'medium'  # 'low', 'medium', 'high', 'ultra'


def get_preset_settings(preset_name='medium'):
    """Get shadow settings for a quality preset.

    Args:
        preset_name: Name of the preset ('low', 'medium', 'high', 'ultra')

    Returns:
        Dictionary of settings
    """
    return PRESETS.get(preset_name, PRESETS['medium'])


def apply_preset(shadow_manager, post_process, preset_name='medium'):
    """Apply a quality preset to the shadow system.

    Args:
        shadow_manager: ShadowManager instance
        post_process: PostProcessManager instance
        preset_name: Name of the preset to apply
    """
    settings = get_preset_settings(preset_name)

    # Apply shadow settings
    shadow_manager.shadow_map_size = settings['shadow_map_size']
    shadow_manager.num_cascades = settings['num_cascades']
    shadow_manager.shadow_softness = settings['shadow_softness']

    # Apply post-process settings
    if hasattr(post_process, 'enabled'):
        post_process.enabled = settings['ssao_enabled'] and settings['denoise_enabled']

    print(f"Applied '{preset_name}' quality preset")
