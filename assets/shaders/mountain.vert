#version 330

// === Inputs ===
in vec3 vertex;
in vec4 color;

// === Outputs ===
out vec4 v_color;
out vec3 v_position;

// === Uniforms ===
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

void main(){
  gl_Position=p3d_ModelViewProjectionMatrix*vec4(vertex,1.);
  
  // Pass vertex color to fragment shader
  v_color=color;
  
  // Pass world position for distance calculations
  v_position=(p3d_ModelMatrix*vec4(vertex,1.)).xyz;
}
