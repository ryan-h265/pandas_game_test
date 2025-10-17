#version 330 core

// Shadow map generation fragment shader
// Depth is automatically written to the depth buffer
out vec4 fragColor;

void main() {
    // We only need depth, but some drivers require color output
    fragColor = vec4(gl_FragCoord.z, 0.0, 0.0, 1.0);
}
