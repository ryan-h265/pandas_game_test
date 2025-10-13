#version 330

// Simple fullscreen quad vertex shader
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

out vec2 vTexCoord;

void main() {
    vTexCoord = p3d_MultiTexCoord0;
    gl_Position = p3d_Vertex;
}
