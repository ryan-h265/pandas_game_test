#version 330 core

// glTF model rendering with shadow mapping and point lights
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
uniform mat4 shadowMatrix0;  // Shadow cascade 0

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;  // Vertex color input

out vec3 vWorldPos;
out vec3 vNormal;
out vec2 vTexCoord;
out vec4 vShadowCoord0;
out vec4 vColor;  // Pass vertex color to fragment shader

void main() {
    // World position
    vWorldPos = (p3d_ModelMatrix * p3d_Vertex).xyz;

    // Normal in world space (not view space - needed for point lights)
    vNormal = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);

    // Texture coordinates
    vTexCoord = p3d_MultiTexCoord0;

    // Pass through vertex color
    vColor = p3d_Color;

    // Shadow coordinates
    vShadowCoord0 = shadowMatrix0 * vec4(vWorldPos, 1.0);

    // Final position
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
