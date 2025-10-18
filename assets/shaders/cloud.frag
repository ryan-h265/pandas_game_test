#version 330

// Cloud fragment shader - realistic volumetric clouds with soft lighting
uniform vec3 lightDirection;// Sun direction
uniform vec3 sunColor;// Sun color
uniform float time;// Animation time for cloud movement
uniform float cloudDensity;// Cloud density multiplier (0.5 - 2.0)

// Fog uniforms
uniform int fogEnabled;// 1 = fog enabled
uniform vec3 fogColor;// Fog tint
uniform float fogStart;// Distance to start fog fade
uniform float fogEnd;// Distance where fog is fully opaque
uniform float fogStrength;// Fog multiplier

in vec3 vWorldPos;
in vec4 vColor;
in float vDistanceToCamera;
in vec2 vCloudCoord;

out vec4 fragColor;

// Simple procedural noise for cloud variation
float hash(vec2 p){
    p=fract(p*vec2(123.34,456.21));
    p+=dot(p,p+45.32);
    return fract(p.x*p.y);
}

float noise(vec2 p){
    vec2 i=floor(p);
    vec2 f=fract(p);
    f=f*f*(3.-2.*f);
    
    float a=hash(i);
    float b=hash(i+vec2(1.,0.));
    float c=hash(i+vec2(0.,1.));
    float d=hash(i+vec2(1.,1.));
    
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}

// Fractal Brownian Motion for realistic cloud texture
float fbm(vec2 p){
    float value=0.;
    float amplitude=.5;
    float frequency=1.;
    
    for(int i=0;i<4;i++){
        value+=amplitude*noise(p*frequency);
        frequency*=2.;
        amplitude*=.5;
    }
    
    return value;
}

// Soft cloud density calculation
float getCloudDensity(vec2 coord){
    // Animate clouds slowly
    vec2 animatedCoord=coord+vec2(time*.02,time*.01);
    
    // Multiple octaves of noise for realistic cloud texture
    float density=fbm(animatedCoord*2.);
    density+=fbm(animatedCoord*4.)*.5;
    density+=fbm(animatedCoord*8.)*.25;
    
    // Normalize and add contrast
    density=(density-.3)*1.5;
    density=clamp(density,0.,1.);
    
    return density;
}

// Soft lighting calculation for clouds
vec3 calculateCloudLighting(vec3 baseColor,vec2 coord){
    // Get cloud density for self-shadowing
    float cloudMask=getCloudDensity(coord);
    
    // Calculate light direction contribution (simplified)
    vec3 lightDir=normalize(lightDirection);
    
    // Simulate volumetric scattering
    // Clouds are brightest where lit by sun, darker in shadow
    float lightInfluence=max(0.,-lightDir.z)*.7+.3;
    
    // Add subtle edge lighting (sun shining through cloud edges)
    float edgeLighting=pow(1.-vColor.a,2.)*lightInfluence;
    
    // Combine base cloud color with lighting
    vec3 litColor=baseColor*lightInfluence;
    
    // Add sun color influence for warm highlights
    litColor+=sunColor*edgeLighting*.3;
    
    // Add slight blue ambient for realism
    vec3 ambientSky=vec3(.6,.7,.9)*.2;
    litColor+=ambientSky*(1.-cloudMask*.5);
    
    return litColor;
}

void main(){
    // Base cloud color from vertex color (white with opacity gradient)
    vec3 baseColor=vColor.rgb;
    
    // Get procedural cloud density for variation
    float proceduralDensity=getCloudDensity(vCloudCoord);
    
    // Modulate opacity with procedural noise for soft, natural edges
    float finalOpacity=vColor.a*proceduralDensity*cloudDensity;
    
    // Atmospheric fade based on distance (distant clouds are lighter/hazier)
    float atmosphericFade=clamp(vDistanceToCamera/3000.,0.,1.);
    vec3 atmosphericColor=vec3(.7,.8,.95);// Light blue sky color
    
    // Calculate realistic cloud lighting
    vec3 litCloudColor=calculateCloudLighting(baseColor,vCloudCoord);
    
    // Blend with atmospheric color for distant clouds
    vec3 finalColor=mix(litCloudColor,atmosphericColor,atmosphericFade*.3);
    
    // Fade opacity with distance for atmospheric perspective
    finalOpacity*=(1.-atmosphericFade*.5);
    
    if(fogEnabled==1){
        float range=max(fogEnd-fogStart,.001);
        float fogFactor=clamp((vDistanceToCamera-fogStart)/range,0.,1.);
        fogFactor=clamp(fogFactor*fogStrength,0.,1.);
        finalColor=mix(finalColor,fogColor,fogFactor);
        finalOpacity*=(1.-fogFactor*.4);
    }
    
    // Soft cloud edges - discard very transparent pixels for performance
    if(finalOpacity<.01){
        discard;
    }
    
    // Output with soft edges and realistic transparency
    fragColor=vec4(finalColor,finalOpacity);
}
