#version 330

// Sky dome vertex shader
uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
in vec3 p3d_Normal;

out vec3 v_position;
out vec3 v_normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    
    // Pass vertex position (in model space, which represents direction)
    v_position = p3d_Vertex.xyz;
    v_normal = p3d_Normal;
}
