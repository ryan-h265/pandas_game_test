#version 330

uniform sampler2D shadowMap0;
uniform sampler2D shadowMap1;
uniform sampler2D shadowMap2;
uniform sampler2D shadowMap3;
uniform vec3 lightDirection;
uniform vec3 lightColor;
uniform vec3 ambientColor;
uniform vec4 cascadeSplits;
uniform int numCascades;
uniform vec2 shadowMapInvSize;
uniform float shadowSoftness;
uniform float cascadeBlendDistance;
uniform vec4 cascadeBias;
uniform int shadowsEnabled;
uniform int useVertexColor;  // 1 = use vertex colors, 0 = default terrain color

// Fog uniforms
uniform int fogEnabled;
uniform vec3 fogColor;
uniform float fogStart;
uniform float fogEnd;
uniform float fogStrength;

// SSAO uniforms
uniform int ssaoEnabled;
uniform float ssaoRadius;
uniform float ssaoBias;
uniform float ssaoStrength;

// Point light uniforms
#define MAX_POINT_LIGHTS 32
uniform int numPointLights;
uniform vec4 pointLightPositions[MAX_POINT_LIGHTS];
uniform vec4 pointLightColors[MAX_POINT_LIGHTS];
uniform float pointLightRadii[MAX_POINT_LIGHTS];
uniform float pointLightIntensities[MAX_POINT_LIGHTS];

in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vTexCoord;
in vec4 vShadowCoord0;
in vec4 vShadowCoord1;
in vec4 vShadowCoord2;
in vec4 vShadowCoord3;
in float vViewDepth;
in vec4 vColor;

out vec4 fragColor;

const int MAX_CASCADES = 4;
const vec2 POISSON_OFFSETS[8] = vec2[](
    vec2(-0.613392, 0.617481),
    vec2(0.170019, -0.040254),
    vec2(-0.299417, -0.875105),
    vec2(-0.651784, -0.420089),
    vec2(0.756483, -0.321331),
    vec2(0.834133, 0.517993),
    vec2(-0.020331, 0.942286),
    vec2(0.223321, 0.203821)
);

vec4 getShadowCoord(int cascadeIndex) {
    if (cascadeIndex == 0) {
        return vShadowCoord0;
    } else if (cascadeIndex == 1) {
        return vShadowCoord1;
    } else if (cascadeIndex == 2) {
        return vShadowCoord2;
    }
    return vShadowCoord3;
}

float sampleShadowMap(sampler2D shadowMap, vec4 shadowCoord, float bias) {
    vec4 coord = shadowCoord;
    coord.xyz /= coord.w;

    // Transform from clip space to texture space
    vec3 projCoords = coord.xyz * 0.5 + 0.5;

    if (projCoords.z <= 0.0 || projCoords.z >= 1.0) {
        return 1.0;
    }

    if (projCoords.x < 0.0 || projCoords.x > 1.0 || projCoords.y < 0.0 || projCoords.y > 1.0) {
        return 1.0;
    }

    float currentDepth = projCoords.z - bias;
    vec2 texelSize = shadowMapInvSize;
    float softness = max(shadowSoftness, 0.5);

    float occlusion = 0.0;
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    occlusion += currentDepth <= closestDepth ? 1.0 : 0.0;

    for (int i = 0; i < 8; ++i) {
        vec2 offset = POISSON_OFFSETS[i] * softness * texelSize;
        closestDepth = texture(shadowMap, projCoords.xy + offset).r;
        occlusion += currentDepth <= closestDepth ? 1.0 : 0.0;
    }

    return occlusion / 9.0;
}

float sampleCascadeShadow(int cascadeIndex, float bias) {
    if (cascadeIndex == 0) {
        return sampleShadowMap(shadowMap0, vShadowCoord0, bias);
    } else if (cascadeIndex == 1) {
        return sampleShadowMap(shadowMap1, vShadowCoord1, bias);
    } else if (cascadeIndex == 2) {
        return sampleShadowMap(shadowMap2, vShadowCoord2, bias);
    }
    return sampleShadowMap(shadowMap3, vShadowCoord3, bias);
}

float computeShadow(float surfaceNdL) {
    if (shadowsEnabled == 0 || numCascades <= 0) {
        return 1.0;
    }

    float depth = vViewDepth;
    int cascadeIndex = numCascades - 1;
    for (int i = 0; i < numCascades; ++i) {
        if (depth <= cascadeSplits[i]) {
            cascadeIndex = i;
            break;
        }
    }

    float baseBias = cascadeBias[cascadeIndex];
    float slopeBias = baseBias * (1.0 - surfaceNdL);
    float shadow = sampleCascadeShadow(cascadeIndex, baseBias + slopeBias);

    if (cascadeIndex < numCascades - 1 && cascadeBlendDistance > 0.0) {
        float split = cascadeSplits[cascadeIndex];
        float blendStart = max(0.0, split - cascadeBlendDistance);
        float blendFactor = clamp((depth - blendStart) / max(cascadeBlendDistance, 0.0001), 0.0, 1.0);
        float nextBias = cascadeBias[cascadeIndex + 1];
        float nextSlopeBias = nextBias * (1.0 - surfaceNdL);
        float nextShadow = sampleCascadeShadow(cascadeIndex + 1, nextBias + nextSlopeBias);
        shadow = mix(shadow, nextShadow, blendFactor);
    }

    return shadow;
}

float hash(vec3 p) {
    vec3 q = fract(p * 0.3183099 + 0.1);
    q *= 17.0;
    return fract(q.x * q.y * q.z * (q.x + q.y + q.z));
}

float calculateSSAO() {
    if (ssaoEnabled == 0) {
        return 1.0;
    }

    vec3 normal = normalize(vNormal);
    vec3 worldPos = vWorldPos;

    float occlusion = 0.0;
    int numSamples = 8;

    for (int i = 0; i < numSamples; ++i) {
        float angle = float(i) * 0.785398;
        float radius = ssaoRadius * (0.5 + 0.5 * hash(worldPos + float(i)));

        vec3 tangent = normalize(cross(normal, vec3(0.5451, 0.1569, 0.7686)));
        if (length(tangent) < 0.1) {
            tangent = normalize(cross(normal, vec3(1.0, 0.0, 0.0)));
        }
        vec3 bitangent = cross(normal, tangent);

        float cosAngle = cos(angle);
        float sinAngle = sin(angle);
        vec3 sampleDir = tangent * cosAngle + bitangent * sinAngle + normal * 0.5;
        sampleDir = normalize(sampleDir);

        float occlusionFactor = max(0.0, dot(normal, sampleDir));
        occlusion += occlusionFactor;
    }

    occlusion /= float(numSamples);
    occlusion = pow(occlusion, 1.0 + ssaoBias);
    occlusion = 1.0 - ((1.0 - occlusion) * ssaoStrength);
    return clamp(occlusion, 0.0, 1.0);
}

vec3 calculatePointLights(vec3 worldPos, vec3 normal, vec3 baseColor) {
    vec3 contribution = vec3(0.0);

    for (int i = 0; i < numPointLights && i < MAX_POINT_LIGHTS; ++i) {
        vec3 lightPos = pointLightPositions[i].xyz;
        vec3 lightVec = lightPos - worldPos;
        float distance = length(lightVec);
        if (distance > pointLightRadii[i]) {
            continue;
        }

        vec3 lightDir = normalize(lightVec);
        float NdotL = max(dot(normal, lightDir), 0.0);

        float radius = pointLightRadii[i];
        float intensity = pointLightIntensities[i];
        float attenuation = intensity / (1.0 + 0.5 * distance / radius + 0.5 * (distance * distance) / (radius * radius));
        attenuation *= 1.0 - smoothstep(radius * 0.8, radius, distance);

        float wrap = (NdotL + 1.0) * 0.5;
        float lit = mix(wrap, NdotL, 0.6);

        contribution += pointLightColors[i].rgb * baseColor * lit * attenuation;
    }

    return contribution;
}

void main() {
    vec3 baseColor;
    if (useVertexColor == 1) {
        baseColor = vColor.rgb;
    } else {
        float colorMagnitude = length(vColor.rgb - vec3(1.0));
        if (colorMagnitude > 0.1) {
            baseColor = vColor.rgb;
        } else {
            baseColor = vec3(0.4, 0.6, 0.3);
        }
    }

    vec3 normal = normalize(vNormal);
    vec3 lightDir = normalize(-lightDirection);
    float NdotL = max(dot(normal, lightDir), 0.0);

    float shadowFactor = computeShadow(NdotL);
    float ao = calculateSSAO();

    vec3 ambient = ambientColor * baseColor * ao;
    vec3 diffuse = lightColor * baseColor * NdotL * shadowFactor;
    vec3 pointLights = calculatePointLights(vWorldPos, normal, baseColor);

    vec3 finalColor = ambient + diffuse + pointLights;
    finalColor = pow(finalColor, vec3(1.0 / 2.2));

    if (fogEnabled == 1) {
        float range = max(fogEnd - fogStart, 0.001);
        float fogFactor = clamp((vViewDepth - fogStart) / range, 0.0, 1.0);
        fogFactor = clamp(fogFactor * fogStrength, 0.0, 1.0);
        finalColor = mix(finalColor, fogColor, fogFactor);
    }

    fragColor = vec4(finalColor, 1.0);
}
