#version 330

// Cloud vertex shader - realistic volumetric clouds
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform vec3 camera;  // Camera position for depth effects

in vec4 p3d_Vertex;
in vec4 p3d_Color;

out vec3 vWorldPos;
out vec4 vColor;
out float vDistanceToCamera;
out vec2 vCloudCoord;

void main() {
    // World position
    vec4 worldPos = p3d_ModelMatrix * p3d_Vertex;
    vWorldPos = worldPos.xyz;

    // Pass through vertex color (contains opacity gradient)
    vColor = p3d_Color;

    // Calculate distance to camera for atmospheric perspective
    vDistanceToCamera = length(worldPos.xyz - camera);

    // Create UV coordinates based on position for noise sampling
    vCloudCoord = p3d_Vertex.xy * 0.01;

    // Final position
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
