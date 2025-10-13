#version 330

// Terrain rendering with PCF shadows (OPTIMIZED for performance)
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

in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vTexCoord;
in vec4 vShadowCoord0;
in vec4 vShadowCoord1;
in vec4 vShadowCoord2;
in float vViewDepth;
in vec4 vColor;  // Vertex color from vertex shader

out vec4 fragColor;

// Simple PCF with 4 samples (much faster than 16)
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
    float shadow = 0.0;

    // Simple 2x2 PCF (4 samples)
    vec2 texelSize = vec2(1.0) / shadowMapSize;
    for (int x = -1; x <= 0; x++) {
        for (int y = -1; y <= 0; y++) {
            vec2 offset = vec2(x, y) * texelSize * shadowSoftness;
            float pcfDepth = texture(shadowMap, projCoords.xy + offset).r;
            shadow += currentDepth - bias > pcfDepth ? 0.0 : 1.0;
        }
    }

    return shadow / 4.0;
}

// Calculate shadow with cascade selection
float calculateCascadedShadow() {
    float shadow;
    float bias = 0.005;

    // Select cascade based on view depth (only 2 cascades now)
    if (vViewDepth < cascadeSplits[0]) {
        shadow = calculateShadowPCF(shadowMap0, vShadowCoord0, bias * 0.5);
    } else {
        shadow = calculateShadowPCF(shadowMap1, vShadowCoord1, bias);
    }

    return shadow;
}

void main() {
    // Base terrain color - use vertex color if enabled, otherwise default grass green
    vec3 baseColor;
    if (useVertexColor == 1) {
        baseColor = vColor.rgb;
    } else {
        baseColor = vec3(0.4, 0.6, 0.3);  // Grass green
    }

    // Normal lighting
    vec3 normal = normalize(vNormal);
    vec3 lightDir = normalize(-lightDirection);
    float NdotL = max(dot(normal, lightDir), 0.0);

    // Calculate shadow
    float shadow = calculateCascadedShadow();

    // Final lighting calculation
    vec3 ambient = ambientColor * baseColor;
    vec3 diffuse = lightColor * baseColor * NdotL * shadow;

    vec3 finalColor = ambient + diffuse;

    // Gamma correction
    finalColor = pow(finalColor, vec3(1.0/2.2));

    fragColor = vec4(finalColor, 1.0);
}
