#version 330

// glTF model rendering with textures, shadows, and point lights
uniform sampler2D shadowMap0;
uniform sampler2D p3d_Texture0;// Base color texture from glTF
uniform vec3 lightDirection;
uniform vec3 lightColor;
uniform vec3 ambientColor;
uniform vec2 shadowMapSize;
uniform float shadowSoftness;

// Fog uniforms
uniform int fogEnabled;// 1 = fog enabled
uniform vec3 fogColor;// Fog tint
uniform float fogStart;// Start distance for fog
uniform float fogEnd;// Full fog distance
uniform float fogStrength;// Fog multiplier

// Point light uniforms (for lanterns, torches, etc.)
#define MAX_POINT_LIGHTS 32
uniform int numPointLights;// Number of active point lights
uniform vec4 pointLightPositions[MAX_POINT_LIGHTS];// World space positions
uniform vec4 pointLightColors[MAX_POINT_LIGHTS];// RGB colors
uniform float pointLightRadii[MAX_POINT_LIGHTS];// Maximum radius of effect
uniform float pointLightIntensities[MAX_POINT_LIGHTS];// Brightness multiplier

in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vTexCoord;
in vec4 vShadowCoord0;
in float vViewDepth;
in vec4 vColor;

out vec4 fragColor;

// Fast shadow lookup with minimal PCF
float calculateShadowPCF(sampler2D shadowMap,vec4 shadowCoord,float bias){
    // Perspective divide
    vec3 projCoords=shadowCoord.xyz/shadowCoord.w;
    
    // Transform to [0,1] range
    projCoords=projCoords*.5+.5;
    
    // Outside shadow map bounds = no shadow
    if(projCoords.x<0.||projCoords.x>1.||
        projCoords.y<0.||projCoords.y>1.||
    projCoords.z>1.){
        return 1.;
    }
    
    float currentDepth=projCoords.z;
    
    // Minimal PCF with 2 samples for performance
    vec2 texelSize=vec2(1.)/shadowMapSize;
    float shadow=0.;
    
    float pcfDepth1=texture(shadowMap,projCoords.xy).r;
    shadow+=currentDepth-bias>pcfDepth1?0.:1.;
    
    vec2 offset=texelSize*shadowSoftness;
    float pcfDepth2=texture(shadowMap,projCoords.xy+offset).r;
    shadow+=currentDepth-bias>pcfDepth2?0.:1.;
    
    return shadow/2.;
}

// Calculate point light contribution
vec3 calculatePointLights(vec3 worldPos,vec3 normal,vec3 baseColor){
    vec3 totalLight=vec3(0.);
    
    for(int i=0;i<numPointLights&&i<MAX_POINT_LIGHTS;i++){
        vec3 lightPos=pointLightPositions[i].xyz;
        vec3 lightColor=pointLightColors[i].rgb;
        float lightRadius=pointLightRadii[i];
        float lightIntensity=pointLightIntensities[i];
        
        // Vector from surface to light
        vec3 lightDir=lightPos-worldPos;
        float distance=length(lightDir);
        
        // Skip if beyond radius
        if(distance>lightRadius){
            continue;
        }
        
        lightDir=normalize(lightDir);
        
        // Diffuse lighting (Lambertian)
        float diff=max(dot(normal,lightDir),0.);
        
        // Attenuation (inverse square with radius falloff)
        float attenuation=lightIntensity/(1.+distance*distance/(lightRadius*lightRadius));
        attenuation*=1.-smoothstep(lightRadius*.8,lightRadius,distance);
        
        // Add contribution
        totalLight+=lightColor*baseColor*diff*attenuation;
    }
    
    return totalLight;
}

void main(){
    // Sample base color texture
    vec4 texColor=texture(p3d_Texture0,vTexCoord);
    
    // Use texture color as base (with vertex color tint if present)
    vec3 baseColor=texColor.rgb*vColor.rgb;
    
    // Normal
    vec3 normal=normalize(vNormal);
    
    // Directional light (sun)
    float NdotL=max(dot(normal,-lightDirection),0.);
    
    // Shadow
    float shadow=calculateShadowPCF(shadowMap0,vShadowCoord0,.005);
    
    // Directional lighting
    vec3 directionalLight=lightColor*NdotL*shadow;
    
    // Point lights (lanterns, torches, etc.)
    vec3 pointLight=calculatePointLights(vWorldPos,normal,baseColor);
    
    // Combine lighting
    vec3 ambient=ambientColor*baseColor;
    vec3 finalColor=ambient+(directionalLight*baseColor)+pointLight;
    
    if(fogEnabled==1){
        float range=max(fogEnd-fogStart,.001);
        float fogFactor=clamp((vViewDepth-fogStart)/range,0.,1.);
        fogFactor=clamp(fogFactor*fogStrength,0.,1.);
        finalColor=mix(finalColor,fogColor,fogFactor);
    }
    
    // Output with texture alpha
    fragColor=vec4(finalColor,texColor.a);
}
