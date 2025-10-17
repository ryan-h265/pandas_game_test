#version 330 core

// Screen Space Ambient Occlusion
uniform sampler2D depthTexture;
uniform sampler2D normalTexture;
uniform sampler2D noiseTexture;
uniform vec3 samples[64];  // Hemisphere samples
uniform mat4 projection;
uniform mat4 invProjection;
uniform vec2 noiseScale;
uniform float radius;
uniform float bias;
uniform int kernelSize;

in vec2 vTexCoord;
out float fragColor;

// Reconstruct view space position from depth
vec3 reconstructViewPos(vec2 uv, float depth) {
    vec4 clipSpacePos = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 viewSpacePos = invProjection * clipSpacePos;
    return viewSpacePos.xyz / viewSpacePos.w;
}

void main() {
    // Get view space position and normal
    float depth = texture(depthTexture, vTexCoord).r;
    if (depth >= 1.0) {
        fragColor = 1.0;  // Sky - no occlusion
        return;
    }

    vec3 viewPos = reconstructViewPos(vTexCoord, depth);
    vec3 normal = normalize(texture(normalTexture, vTexCoord).xyz * 2.0 - 1.0);

    // Get noise vector for random rotation
    vec3 randomVec = normalize(texture(noiseTexture, vTexCoord * noiseScale).xyz * 2.0 - 1.0);

    // Create TBN matrix for hemisphere orientation
    vec3 tangent = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 TBN = mat3(tangent, bitangent, normal);

    // Sample hemisphere around point
    float occlusion = 0.0;
    for (int i = 0; i < kernelSize; i++) {
        // Get sample position in view space
        vec3 samplePos = TBN * samples[i];
        samplePos = viewPos + samplePos * radius;

        // Project to screen space
        vec4 offset = projection * vec4(samplePos, 1.0);
        offset.xyz /= offset.w;
        offset.xyz = offset.xyz * 0.5 + 0.5;

        // Sample depth at offset position
        float sampleDepth = texture(depthTexture, offset.xy).r;
        vec3 sampleViewPos = reconstructViewPos(offset.xy, sampleDepth);

        // Range check
        float rangeCheck = smoothstep(0.0, 1.0, radius / abs(viewPos.z - sampleViewPos.z));

        // Add occlusion if sample is occluded
        occlusion += (sampleViewPos.z >= samplePos.z + bias ? 1.0 : 0.0) * rangeCheck;
    }

    // Normalize and invert (we want AO factor, not occlusion)
    occlusion = 1.0 - (occlusion / float(kernelSize));

    fragColor = occlusion;
}
