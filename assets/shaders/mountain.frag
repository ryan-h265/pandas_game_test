#version 330

// === Inputs from vertex shader ===
in vec4 v_color;
in vec3 v_position;

// === Uniforms ===
uniform float u_time;
uniform float u_cycleSpeed;
uniform vec3 sunBaseColor;
uniform vec3 moonBaseColor;

// === Output ===
out vec4 fragColor;

void main(){
  // --- Day/night cycle (matches sky shader) ---
  float cycle=u_time*u_cycleSpeed;
  vec3 sunDir=normalize(vec3(sin(cycle),sin(cycle*.8),cos(cycle)));
  
  float sunHeight=sunDir.y;
  float dayFactor=smoothstep(-.3,.3,sunHeight);
  
  // --- Atmospheric perspective ---
  // Mountains further away fade toward sky color
  float distance=length(v_position);
  float atmosPerspective=smoothstep(500.,2500.,distance);
  
  // Day and night sky colors
  vec3 daySkySilhouette=vec3(.6,.7,.95);
  vec3 nightSkySilhouette=vec3(.05,.08,.15);
  vec3 skyColor=mix(nightSkySilhouette,daySkySilhouette,dayFactor);
  
  // --- Base mountain color from vertex colors ---
  vec3 mountainColor=v_color.rgb;
  
  // Brighten mountains during day, darken during night
  vec3 dayTint=vec3(.9,.95,1.);// Slightly brighter, bluer
  vec3 nightTint=vec3(.4,.45,.6);// Darker, more saturated
  vec3 timeTint=mix(nightTint,dayTint,dayFactor);
  
  // Apply time tint
  mountainColor*=timeTint;
  
  // --- Apply atmospheric perspective (fade to sky color) ---
  mountainColor=mix(mountainColor,skyColor,atmosPerspective*.5);
  
  // Keep the alpha from vertex color for transparency fade
  float alpha=v_color.a;
  
  // Fade out at extreme distances for silhouette effect
  alpha*=1.-atmosPerspective*.3;
  
  fragColor=vec4(mountainColor,alpha);
}
