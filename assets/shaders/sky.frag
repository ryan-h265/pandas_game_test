#version 330

// Sky shader - computes procedural sky based on vertex position
uniform vec3 zenithColor;
uniform vec3 horizonColor;
uniform vec3 sunDirection;

in vec3 v_position;  // World-space vertex position
in vec3 v_normal;    // Normal (pointing to sky direction)

out vec4 fragColor;

void main() {
    // Use vertex position as ray direction (normalized)
    vec3 rayDir = normalize(v_position);
    
    // Compute sky color based on ray direction
    // heightFactor: 0 at horizon, 1 at zenith
    float heightFactor = max(0.0, rayDir.z);
    heightFactor = pow(heightFactor, 0.6); // Adjust gradient curve
    
    // Interpolate between horizon and zenith
    vec3 skyColor = mix(horizonColor, zenithColor, heightFactor);
    
    // Optional: Add subtle sun glow
    float sunDot = max(0.0, dot(rayDir, normalize(sunDirection)));
    float sunGlow = pow(sunDot, 32.0) * 0.3;
    skyColor += vec3(sunGlow);
    
    fragColor = vec4(skyColor, 1.0);
}
