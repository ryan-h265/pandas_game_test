#version 330 core

// https://www.shadertoy.com/view/XtGGRt

// === UNIFORMS ===
uniform float u_time;// seconds
uniform vec2 u_resolution;// viewport size
uniform vec3 u_cameraPos;// camera position (optional)
uniform vec3 u_auroraDir;// base aurora orientation (e.g. vec3(-0.5, -0.6, 0.9))
uniform float u_transitionAlpha;// Fade-in alpha during transitions (0-1)

// Fog uniforms
uniform int fogEnabled;// 1 = fog enabled
uniform vec3 fogColor;// Fog tint
uniform float fogStart;// (unused, shared interface)
uniform float fogEnd;// (unused, shared interface)
uniform float fogStrength;// Fog multiplier

// === INPUTS ===
in vec3 v_position;// world-space vertex position (hemisphere)
in vec3 v_normal;// sky direction (should point upward)

// === OUTPUT ===
out vec4 fragColor;

// === HELPERS ===
mat2 mm2(float a){float c=cos(a),s=sin(a);return mat2(c,s,-s,c);}
mat2 m2=mat2(.95534,.29552,-.29552,.95534);

float tri(float x){return clamp(abs(fract(x)-.5),.01,.49);}
vec2 tri2(vec2 p){return vec2(tri(p.x)+tri(p.y),tri(p.y+tri(p.x)));}

float triNoise2d(vec2 p,float spd,float time){
  float z=1.8;
  float z2=2.5;
  float rz=0.;
  p*=mm2(p.x*.06);
  vec2 bp=p;
  for(float i=0.;i<5.;i++){
    vec2 dg=tri2(bp*1.85)*.75;
    dg*=mm2(time*spd);
    p-=dg/z2;
    bp*=1.3;
    z2*=.45;
    z*=.42;
    p*=1.21+(rz-1.)*.02;
    rz+=tri(p.x+tri(p.y))*z;
    p*=-m2;
  }
  return clamp(1./pow(rz*29.,1.3),0.,.55);
}

float hash21(vec2 n){return fract(sin(dot(n,vec2(12.9898,4.1414)))*43758.5453);}

vec4 aurora(vec3 ro,vec3 rd,float time){
  vec4 col=vec4(0);
  vec4 avgCol=vec4(0);
  for(float i=0.;i<50.;i++){
    float pt=((.8+pow(i,1.4)*.002)-ro.y)/(rd.y*2.+.4);
    vec3 bpos=ro+pt*rd;
    vec2 p=bpos.zx;
    float rzt=triNoise2d(p,.06,time);
    vec4 col2=vec4(0.);
    col2.a=rzt;
    col2.rgb=(sin(1.-vec3(2.15,-.5,1.2)+i*.043)*.5+.5)*rzt;
    avgCol=mix(avgCol,col2,.5);
    col+=avgCol*exp2(-i*.065-2.5)*smoothstep(0.,5.,i);
  }
  col*=clamp(rd.y*15.+.4,0.,1.);
  return col*1.8;
}

vec3 nmzHash33(vec3 q){
  uvec3 p=uvec3(ivec3(q));
  p=p*uvec3(374761393U,1103515245U,668265263U)+p.zxy+p.yzx;
  p=p.yzx*(p.zxy^(p>>3U));
  return vec3(p^(p>>16U))*(1./4294967295.);
}

vec3 stars(vec3 p){
  vec3 c=vec3(0.);
  float res=u_resolution.x;
  for(float i=0.;i<4.;i++){
    vec3 q=fract(p*(.15*res))-.5;
    vec3 id=floor(p*(.15*res));
    vec2 rn=nmzHash33(id).xy;
    float c2=1.-smoothstep(0.,.6,length(q));
    c2*=step(rn.x,.0005+i*i*.001);
    c+=c2*(mix(vec3(1.,.49,.1),vec3(.75,.9,1.),rn.y)*.1+.9);
    p*=1.3;
  }
  return c*c*.8;
}

vec3 bg(vec3 rd){
  float sd=dot(normalize(u_auroraDir),rd)*.5+.5;
  sd=pow(sd,5.);
  vec3 col=mix(vec3(.05,.1,.2),vec3(.1,.05,.2),sd);
  return col*.63;
}
void main(){
  // Use vertex position as ray direction
  vec3 rayDir=normalize(v_position);
  
  // FIX: Rotate from Shadertoy space (+Z forward, +Y up)
  // to hemisphere space (+Y up, +Z forward)
  rayDir=rayDir.xzy;// swaps Y and Z → fixes 90° rotation
  
  vec3 ro=u_cameraPos;// typically vec3(0,0,0)
  
  vec3 col=vec3(0.);
  vec3 rd=rayDir;
  
  // Fade horizon
  float fade=smoothstep(0.,.01,abs(rd.y))*.1+.9;
  col=bg(rd)*fade;
  
  if(rd.y>0.){
    vec4 aur=smoothstep(0.,1.5,aurora(ro,rd,u_time))*fade;
    col+=stars(rd);
    col=col*(1.-aur.a)+aur.rgb;
  }else{
    rd.y=abs(rd.y);
    col=bg(rd)*fade*.6;
    vec4 aur=smoothstep(0.,2.5,aurora(ro,rd,u_time));
    col+=stars(rd)*.1;
    col=col*(1.-aur.a)+aur.rgb;
    vec3 pos=ro+((.5-ro.y)/rd.y)*rd;
    float nz2=triNoise2d(pos.xz*vec2(.5,.7),0.,u_time);
    col+=mix(vec3(.2,.25,.5)*.08,vec3(.3,.3,.5)*.7,nz2*.4);
  }
  
  if(fogEnabled==1){
    float horizonFog=pow(clamp(1.-abs(rd.y),0.,1.),1.2);
    float fogFactor=clamp(horizonFog*fogStrength,0.,1.);
    col=mix(col,fogColor,fogFactor);
  }
  
  fragColor=vec4(col,u_transitionAlpha);
}
