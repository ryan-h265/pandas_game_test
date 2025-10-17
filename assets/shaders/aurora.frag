#version 330

// === Uniforms ===
uniform float u_time;// Elapsed time in seconds
uniform vec3 sunBaseColor;// Base sun color
uniform vec3 moonBaseColor;// Base moon color
uniform float u_cycleSpeed;// Day/night speed (0.025 ~= 4min cycle)

// === Inputs from vertex shader ===
in vec3 v_position;// World-space vertex position on hemisphere
in vec3 v_normal;// Vertex normal

// === Output ===
out vec4 fragColor;

// --- Noise for stars ---
float hash(vec3 p){
  return fract(sin(dot(p,vec3(12.9898,78.233,45.164)))*43758.5453);
}

float starField(vec3 rayDir,float intensity,float time){
  vec3 starCoord=rayDir*50.;// Scale up for star positions
  vec3 cellCoord=floor(starCoord);
  vec3 cellFraction=fract(starCoord);
  
  float star=0.;
  for(int x=-1;x<=1;x++){
    for(int y=-1;y<=1;y++){
      for(int z=-1;z<=1;z++){
        vec3 neighbor=cellCoord+vec3(x,y,z);
        float h=hash(neighbor);
        
        // Only some cells have stars (sparse)
        if(h>.95){
          vec3 starCenter=neighbor+vec3(
            fract(sin(h*12.34)*.5)+.5,
            fract(sin(h*23.45)*.5)+.5,
            fract(sin(h*34.56)*.5)+.5
          );
          
          float d=length(starCoord-starCenter);
          
          // Twinkle based on star's own hash and time
          float twinklePeriod=2.+h*3.;// 2-5 second twinkle cycles
          float twinkle=.3+.7*(sin(time*6.28/twinklePeriod+h*100.)*.5+.5);
          
          // Sharp core point
          float core=exp(-d*d*50.)*twinkle;// Tight gaussian for sharp point
          
          // Soft glow around star
          float glow=exp(-d*d*3.)*.3;// Wider gaussian for glow
          
          float starBrightness=(core+glow)*max(0.,h-.95)*2.;
          star=max(star,starBrightness);
        }
      }
    }
  }
  
  return clamp(star*intensity,0.,1.);
}

void main(){
  vec3 rayDir=normalize(v_position);
  
  // --- Day/night cycle ---
  float cycle=u_time*u_cycleSpeed;
  vec3 sunDir=normalize(vec3(sin(cycle),sin(cycle*.8),cos(cycle)));
  vec3 moonDir=-sunDir;
  
  float sunHeight=sunDir.y;
  float moonHeight=moonDir.y;
  
  // Transition factor: -1 = night, 0 = twilight, 1 = day
  float dayFactor=smoothstep(-.3,.3,sunHeight);
  
  // --- Sky gradient ---
  vec3 dayZenith=vec3(.2,.5,.9);// Rich blue zenith
  vec3 dayHorizon=vec3(.4,.65,.95);// Lighter blue horizon (not gray!)
  vec3 nightZenith=vec3(.01,.015,.03);
  vec3 nightHorizon=vec3(.05,.08,.12);// Slightly lighter night horizon
  
  // Use rayDir.z for height (Z is up in Panda3D)
  float heightFactor=clamp(rayDir.z,0.,1.);
  heightFactor=pow(heightFactor,.7);// Power curve for more zenith color
  
  vec3 zenith=mix(nightZenith,dayZenith,dayFactor);
  vec3 horizon=mix(nightHorizon,dayHorizon,dayFactor);
  vec3 skyColor=mix(horizon,zenith,heightFactor);
  
  // --- Sun disk + glow ---
  float sunDot=max(dot(rayDir,sunDir),0.);
  float sunDisk=smoothstep(.992,1.,sunDot);
  float sunGlow=pow(sunDot,30.);
  vec3 sunColor=mix(vec3(1.,.7,.3),sunBaseColor,dayFactor);
  skyColor+=sunColor*(sunDisk*2.+sunGlow*.8)*dayFactor;
  
  // --- Sunrise/sunset colors (only during twilight) ---
  float twilight=1.-abs(sunHeight);
  float sunsetFactor=smoothstep(0.,.5,twilight);
  vec3 sunsetColor=mix(vec3(0.,0.,0.),vec3(1.,.4,.1),sunsetFactor);
  float sunsetBlend=(1.-dayFactor)*sunsetFactor;
  skyColor=mix(skyColor,sunsetColor,sunsetBlend*.4);
  
  // --- Moon disk + glow ---
  float moonDot=max(dot(rayDir,moonDir),0.);
  float moonDisk=smoothstep(.992,1.,moonDot);
  float moonGlow=pow(moonDot,40.);
  skyColor+=moonBaseColor*(moonDisk*1.8+moonGlow*1.2)*(1.-dayFactor);
  
  // --- Moonlight tint at night ---
  float moonLight=smoothstep(0.,.4,moonHeight)*(1.-dayFactor);
  skyColor+=vec3(.04,.06,.1)*moonLight*.3;
  
  // --- Stars (only at night) ---
  float starIntensity=1.-dayFactor;
  float stars=starField(rayDir,starIntensity,u_time);
  skyColor+=vec3(.9,.95,1.)*stars;
  
  // Clamp and output
  skyColor=clamp(skyColor,0.,1.);
  fragColor=vec4(skyColor,1.);
}
