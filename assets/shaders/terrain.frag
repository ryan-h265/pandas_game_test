#version 330 core

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

// Point light uniforms (for lanterns, torches, etc.)
#define MAX_POINT_LIGHTS 32  // Increased from 8 (supports more lights with distance culling)
uniform int numPointLights;  // Number of active point lights
uniform vec4 pointLightPositions[MAX_POINT_LIGHTS];  // World space positions (w unused)
uniform vec4 pointLightColors[MAX_POINT_LIGHTS];     // RGB colors (w unused)
uniform float pointLightRadii[MAX_POINT_LIGHTS];     // Maximum radius of effect
uniform float pointLightIntensities[MAX_POINT_LIGHTS]; // Brightness multiplier

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

// Calculate lighting contribution from point lights
vec3 calculatePointLights(vec3 worldPos, vec3 normal, vec3 baseColor) {
    vec3 pointLightContribution = vec3(0.0);

    for (int i = 0; i < numPointLights && i < MAX_POINT_LIGHTS; i++) {
        // Vector from surface to light (extract xyz from vec4)
        vec3 lightPos = pointLightPositions[i].xyz;
        vec3 lightVec = lightPos - worldPos;
        float distance = length(lightVec);

        // Skip if beyond light radius
        if (distance > pointLightRadii[i]) {
            continue;
        }

        vec3 lightDir = normalize(lightVec);

        // Diffuse lighting with wrap-around for omnidirectional feel
        float NdotL = dot(normal, lightDir);

        // Mix of diffuse and ambient-like contribution
        // This ensures all surfaces get some light, not just those facing the source
        float diffuse = max(NdotL, 0.0);  // Standard diffuse
        float wrap = (NdotL + 1.0) * 0.5;  // Wrap-around lighting (0.0 to 1.0)
        float lightContribution = mix(wrap, diffuse, 0.5);  // 50/50 mix for softer omnidirectional feel

        // Attenuation - softer falloff for wider glow
        float radius = pointLightRadii[i];

        // Linear + quadratic falloff (less aggressive than pure quadratic)
        float linearAtten = 0.5 / radius;
        float quadraticAtten = 0.5 / (radius * radius);
        float attenuation = pointLightIntensities[i] / (1.0 + linearAtten * distance + quadraticAtten * distance * distance);

        // Gentler edge falloff for wider visible glow
        float edgeFalloff = 1.0 - smoothstep(radius * 0.8, radius, distance);
        attenuation *= edgeFalloff;

        // Add this light's contribution (extract xyz from vec4 color)
        pointLightContribution += pointLightColors[i].xyz * baseColor * lightContribution * attenuation;
    }

    return pointLightContribution;
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

    // Add point light contributions (lanterns, torches)
    vec3 pointLights = calculatePointLights(vWorldPos, normal, baseColor);

    vec3 finalColor = ambient + diffuse + pointLights;

    // Gamma correction
    finalColor = pow(finalColor, vec3(1.0/2.2));

    fragColor = vec4(finalColor, 1.0);
}
