#version 330

// === Uniforms ===
uniform float u_time;// Elapsed time in seconds
uniform vec3 sunBaseColor;// Base sun color
uniform float u_cycleSpeed;// Day/night speed (0.025 ~= 4min cycle)
uniform float u_transitionAlpha;// Fade-in alpha during transitions (0-1)

// === Inputs from vertex shader ===
in vec3 v_position;// World-space vertex position on hemisphere
in vec3 v_normal;// Vertex normal

// === Output ===
out vec4 fragColor;

void main(){
  vec3 rayDir=normalize(v_position);
  
  // --- Day/night cycle ---
  float cycle=u_time*u_cycleSpeed;
  vec3 sunDir=normalize(vec3(sin(cycle),sin(cycle*.8),cos(cycle)));
  float sunHeight=sunDir.y;
  
  // Transition factor: -1 = night, 0 = twilight, 1 = day
  float dayFactor=smoothstep(-.3,.3,sunHeight);
  
  // --- Sky gradient ---
  vec3 dayZenith=vec3(.2,.5,.9);// Deep blue zenith
  vec3 dayHorizon=vec3(.4,.65,.95);// Light blue horizon
  vec3 nightZenith=vec3(.01,.015,.03);
  vec3 nightHorizon=vec3(.05,.08,.12);
  
  float heightFactor=clamp(rayDir.z,0.,1.);
  heightFactor=pow(heightFactor,.7);// Emphasize zenith color
  
  vec3 zenith=mix(nightZenith,dayZenith,dayFactor);
  vec3 horizon=mix(nightHorizon,dayHorizon,dayFactor);
  vec3 skyColor=mix(horizon,zenith,heightFactor);
  
  // --- Sun disk + glow ---
  float sunDot=max(dot(rayDir,sunDir),0.);
  float sunDisk=smoothstep(.992,1.,sunDot);
  float sunGlow=pow(sunDot,30.);
  
  // Mix a warm orange at low sun height, brighter white at noon
  vec3 warmColor=vec3(1.,.6,.3);
  vec3 coolColor=sunBaseColor;
  vec3 sunColor=mix(warmColor,coolColor,dayFactor);
  
  skyColor+=sunColor*(sunDisk*2.+sunGlow*.8)*dayFactor;
  
  // Clamp and output with fade-in during transition
  skyColor=clamp(skyColor,0.,1.);
  fragColor=vec4(skyColor,u_transitionAlpha);
}
