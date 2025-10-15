#version 330

// Terrain rendering with PCF shadows and SSAO (OPTIMIZED for performance)
uniform sampler2D shadowMap0;
uniform sampler2D shadowMap1;
uniform sampler2D shadowMap2;
uniform vec3 lightDirection;
uniform vec3 lightColor;
uniform vec3 ambientColor;
uniform float cascadeSplits[3];
uniform vec2 shadowMapSize;
uniform float shadowSoftness;
uniform int useVertexColor;  // 1 = use vertex colors, 0 = use default terrain color

// SSAO uniforms
uniform int ssaoEnabled;  // 1 = enabled, 0 = disabled
uniform float ssaoRadius;  // Occlusion sample radius
uniform float ssaoBias;    // Depth bias
uniform float ssaoStrength;  // AO strength multiplier (0.0-2.0)

in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vTexCoord;
in vec4 vShadowCoord0;
in vec4 vShadowCoord1;
in vec4 vShadowCoord2;
in float vViewDepth;
in vec4 vColor;  // Vertex color from vertex shader

out vec4 fragColor;

// Ultra-fast shadow lookup with minimal PCF (2 samples for performance)
float calculateShadowPCF(sampler2D shadowMap, vec4 shadowCoord, float bias) {
    // Perspective divide
    vec3 projCoords = shadowCoord.xyz / shadowCoord.w;

    // Transform to [0,1] range
    projCoords = projCoords * 0.5 + 0.5;

    // Outside shadow map bounds = no shadow
    if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
        projCoords.y < 0.0 || projCoords.y > 1.0 ||
        projCoords.z > 1.0) {
        return 1.0;
    }

    float currentDepth = projCoords.z;

    // Minimal PCF with only 2 samples (for maximum performance)
    vec2 texelSize = vec2(1.0) / shadowMapSize;
    float shadow = 0.0;

    float pcfDepth1 = texture(shadowMap, projCoords.xy).r;
    shadow += currentDepth - bias > pcfDepth1 ? 0.0 : 1.0;

    vec2 offset = texelSize * shadowSoftness;
    float pcfDepth2 = texture(shadowMap, projCoords.xy + offset).r;
    shadow += currentDepth - bias > pcfDepth2 ? 0.0 : 1.0;

    return shadow / 2.0;
}

// Calculate shadow with single cascade (maximum performance)
float calculateCascadedShadow() {
    float bias = 0.005;

    // Only 1 cascade for max performance
    float shadow = calculateShadowPCF(shadowMap0, vShadowCoord0, bias);

    return shadow;
}

// Simple hash function for pseudo-random sampling
float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

// Fast Screen-Space Ambient Occlusion
float calculateSSAO() {
    if (ssaoEnabled == 0) {
        return 1.0;  // No occlusion
    }

    vec3 normal = normalize(vNormal);
    vec3 worldPos = vWorldPos;

    // Simple geometric occlusion based on surface curvature
    // Sample surrounding geometry using world position
    float occlusion = 0.0;
    int numSamples = 8;  // Reduced for performance

    // Create sampling kernel in hemisphere around normal
    for (int i = 0; i < numSamples; i++) {
        // Generate pseudo-random sample direction
        float angle = float(i) * 0.785398;  // PI/4
        float radius = ssaoRadius * (0.5 + 0.5 * hash(worldPos + float(i)));

        // Create sample offset in tangent space
        vec3 tangent = normalize(cross(normal, vec3(0.0, 1.0, 0.0)));
        if (length(tangent) < 0.1) {
            tangent = normalize(cross(normal, vec3(1.0, 0.0, 0.0)));
        }
        vec3 bitangent = cross(normal, tangent);

        float cosAngle = cos(angle);
        float sinAngle = sin(angle);
        vec3 sampleDir = tangent * cosAngle + bitangent * sinAngle + normal * 0.5;
        sampleDir = normalize(sampleDir);

        // Simple depth-based occlusion
        // This is a simplified approach - proper SSAO needs screen-space depth buffer
        float occlusionFactor = max(0.0, dot(normal, sampleDir));
        occlusion += occlusionFactor;
    }

    // Normalize
    occlusion = occlusion / float(numSamples);

    // Apply strength and bias
    occlusion = pow(occlusion, 1.0 + ssaoBias);
    occlusion = 1.0 - ((1.0 - occlusion) * ssaoStrength);

    return clamp(occlusion, 0.0, 1.0);
}

void main() {
    // Base terrain color - use vertex color if enabled, otherwise default grass green
    vec3 baseColor;
    if (useVertexColor == 1) {
        baseColor = vColor.rgb;
    } else {
        // Auto-detect if vertex has meaningful color data (not default white/black)
        // If vertex color is not near white (1,1,1) or black (0,0,0), use it
        float colorMagnitude = length(vColor.rgb - vec3(1.0, 1.0, 1.0));
        if (colorMagnitude > 0.1) {
            // Vertex has custom color data, use it
            baseColor = vColor.rgb;
        } else {
            // Use default grass green for terrain
            baseColor = vec3(0.4, 0.6, 0.3);
        }
    }

    // Normal lighting
    vec3 normal = normalize(vNormal);
    vec3 lightDir = normalize(-lightDirection);
    float NdotL = max(dot(normal, lightDir), 0.0);

    // Calculate shadow
    float shadow = calculateCascadedShadow();

    // Calculate ambient occlusion
    float ao = calculateSSAO();

    // Final lighting calculation with AO
    vec3 ambient = ambientColor * baseColor * ao;  // AO affects ambient
    vec3 diffuse = lightColor * baseColor * NdotL * shadow;

    vec3 finalColor = ambient + diffuse;

    // Gamma correction
    finalColor = pow(finalColor, vec3(1.0/2.2));

    fragColor = vec4(finalColor, 1.0);
}
