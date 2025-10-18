
#define time iTime

mat2 mm2(in float a){float c=cos(a),s=sin(a);return mat2(c,s,-s,c);}
mat2 m2=mat2(.95534,.29552,-.29552,.95534);
float tri(in float x){return clamp(abs(fract(x)-.5),.01,.49);}
vec2 tri2(in vec2 p){return vec2(tri(p.x)+tri(p.y),tri(p.y+tri(p.x)));}

float triNoise2d(in vec2 p,float spd)
{
  float z=1.8;
  float z2=2.5;
  float rz=0.;
  p*=mm2(p.x*.06);
  vec2 bp=p;
  for(float i=0.;i<5.;i++)
  {
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

float hash21(in vec2 n){return fract(sin(dot(n,vec2(12.9898,4.1414)))*43758.5453);}
vec4 aurora(vec3 ro,vec3 rd)
{
  vec4 col=vec4(0);
  vec4 avgCol=vec4(0);
  
  for(float i=0.;i<50.;i++)
  {
    float of=.006*hash21(gl_FragCoord.xy)*smoothstep(0.,15.,i);
    float pt=((.8+pow(i,1.4)*.002)-ro.y)/(rd.y*2.+.4);
    pt-=of;
    vec3 bpos=ro+pt*rd;
    vec2 p=bpos.zx;
    float rzt=triNoise2d(p,.06);
    vec4 col2=vec4(0,0,0,rzt);
    col2.rgb=(sin(1.-vec3(2.15,-.5,1.2)+i*.043)*.5+.5)*rzt;
    avgCol=mix(avgCol,col2,.5);
    col+=avgCol*exp2(-i*.065-2.5)*smoothstep(0.,5.,i);
    
  }
  
  col*=(clamp(rd.y*15.+.4,0.,1.));
  
  //return clamp(pow(col,vec4(1.3))*1.5,0.,1.);
  //return clamp(pow(col,vec4(1.7))*2.,0.,1.);
  //return clamp(pow(col,vec4(1.5))*2.5,0.,1.);
  //return clamp(pow(col,vec4(1.8))*1.5,0.,1.);
  
  //return smoothstep(0.,1.1,pow(col,vec4(1.))*1.5);
  return col*1.8;
  //return pow(col,vec4(1.))*2.
}

//-------------------Background and Stars--------------------

vec3 nmzHash33(vec3 q)
{
  uvec3 p=uvec3(ivec3(q));
  p=p*uvec3(374761393U,1103515245U,668265263U)+p.zxy+p.yzx;
  p=p.yzx*(p.zxy^(p>>3U));
  return vec3(p^(p>>16U))*(1./vec3(0xffffffffU));
}

vec3 stars(in vec3 p)
{
  vec3 c=vec3(0.);
  float res=iResolution.x*1.;
  
  for(float i=0.;i<4.;i++)
  {
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

vec3 bg(in vec3 rd)
{
  float sd=dot(normalize(vec3(-.5,-.6,.9)),rd)*.5+.5;
  sd=pow(sd,5.);
  vec3 col=mix(vec3(.05,.1,.2),vec3(.1,.05,.2),sd);
  return col*.63;
}
//-----------------------------------------------------------

void mainImage(out vec4 fragColor,in vec2 fragCoord)
{
  vec2 q=fragCoord.xy/iResolution.xy;
  vec2 p=q-.5;
  p.x*=iResolution.x/iResolution.y;
  
  vec3 ro=vec3(0,0,-6.7);
  vec3 rd=normalize(vec3(p,1.3));
  vec2 mo=iMouse.xy/iResolution.xy-.5;
  mo=(mo==vec2(-.5))?mo=vec2(-.1,.1):mo;
  mo.x*=iResolution.x/iResolution.y;
  rd.yz*=mm2(mo.y);
  rd.xz*=mm2(mo.x+sin(time*.05)*.2);
  
  vec3 col=vec3(0.);
  vec3 brd=rd;
  float fade=smoothstep(0.,.01,abs(brd.y))*.1+.9;
  
  col=bg(rd)*fade;
  
  if(rd.y>0.){
    vec4 aur=smoothstep(0.,1.5,aurora(ro,rd))*fade;
    col+=stars(rd);
    col=col*(1.-aur.a)+aur.rgb;
  }
  else//Reflections
  {
    rd.y=abs(rd.y);
    col=bg(rd)*fade*.6;
    vec4 aur=smoothstep(0.,2.5,aurora(ro,rd));
    col+=stars(rd)*.1;
    col=col*(1.-aur.a)+aur.rgb;
    vec3 pos=ro+((.5-ro.y)/rd.y)*rd;
    float nz2=triNoise2d(pos.xz*vec2(.5,.7),0.);
    col+=mix(vec3(.2,.25,.5)*.08,vec3(.3,.3,.5)*.7,nz2*.4);
  }
  
  fragColor=vec4(col,1.);
}