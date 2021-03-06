#version 450 core

in vec3 aPos;
in vec2 aTexCoord;

out VS_OUT {
  vec4 color;
  vec3 texCoord;
  vec2 quad;
} vs_out;

uniform mat4 m_mvp;
uniform float u_unwrap;
uniform float u_z_offset;
uniform float u_separation;
uniform vec4 u_color;
uniform int u_layers;

const float rad_min = 0.8;
const float layer_spacing = 0.02;
const int num_pieces = 15;

void main() {
  vec4 vPos = vec4(aPos, 1.0);
  float depth = aPos.z / 6000;
  // for drawing a flat sphere (water)
  if (u_z_offset == 0) {
    vPos.z = -depth / 4;
  } else {
    // calculate z or sigma coordinate
    vPos.z = -u_z_offset - layer_spacing * (u_layers - gl_InstanceID);
    // don't penetrate topography
    vPos.z = max(vPos.z, -depth / 4);
    depth = 0; // for coloring
  }

  vec2 aQuad = num_pieces * aTexCoord;
  vPos.xy += (ivec2(aQuad) / (num_pieces - 1.0) - vec2(0.5)) * u_separation;

  // elevation and azimuth in spherical coords
  float phi = radians(aPos.x * 180 - 100);
  float theta = radians(aPos.y * 80);
  float rad = 1.0 - u_z_offset - (1.0 - rad_min) * depth;
  vec4 sPos = vec4(rad * cos(theta) * cos(phi),
		   rad * sin(theta),
		   -rad * cos(theta) * sin(phi),
		   1);
  
  gl_Position = m_mvp * mix(sPos, vPos, u_unwrap);
  vs_out.texCoord = vec3(aTexCoord, u_layers - gl_InstanceID);
  vs_out.quad = aQuad;

  if (depth < 0.05) {
    vs_out.color = u_color;
  } else {
    vs_out.color = vec4(vec3(1.0 - depth), 1.0);
  }
}
