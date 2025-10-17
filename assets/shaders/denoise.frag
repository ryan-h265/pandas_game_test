#version 330 core

// Bilateral filter for shadow denoising
// Preserves edges while smoothing shadows
uniform sampler2D sceneTexture;
uniform sampler2D depthTexture;
uniform vec2 texelSize;
uniform float spatialSigma;
uniform float depthSigma;
uniform int kernelSize;

in vec2 vTexCoord;
out vec4 fragColor;

// Gaussian weight
float gaussian(float x, float sigma) {
    return exp(-(x * x) / (2.0 * sigma * sigma));
}

void main() {
    vec3 centerColor = texture(sceneTexture, vTexCoord).rgb;
    float centerDepth = texture(depthTexture, vTexCoord).r;

    vec3 sum = vec3(0.0);
    float totalWeight = 0.0;

    int halfKernel = kernelSize / 2;

    // Bilateral filtering
    for (int x = -halfKernel; x <= halfKernel; x++) {
        for (int y = -halfKernel; y <= halfKernel; y++) {
            vec2 offset = vec2(float(x), float(y)) * texelSize;
            vec2 sampleCoord = vTexCoord + offset;

            // Sample color and depth
            vec3 sampleColor = texture(sceneTexture, sampleCoord).rgb;
            float sampleDepth = texture(depthTexture, sampleCoord).r;

            // Spatial weight (distance in screen space)
            float spatialDist = length(vec2(x, y));
            float spatialWeight = gaussian(spatialDist, spatialSigma);

            // Range weight (depth difference)
            float depthDiff = abs(centerDepth - sampleDepth);
            float depthWeight = gaussian(depthDiff, depthSigma);

            // Combined weight
            float weight = spatialWeight * depthWeight;

            sum += sampleColor * weight;
            totalWeight += weight;
        }
    }

    // Normalize
    vec3 denoisedColor = sum / max(totalWeight, 0.0001);

    fragColor = vec4(denoisedColor, 1.0);
}
